import sqlite3
import os
from config import DB_PATH

# Turso 云端连接（通过环境变量启用）
TURSO_URL = os.environ.get("TURSO_URL")
TURSO_TOKEN = os.environ.get("TURSO_TOKEN")


class _TursoConn:
    """包装 Turso sync client，使其兼容 sqlite3.Connection 接口。"""

    def __init__(self, client):
        self._client = client
        self.row_factory = None  # 兼容赋值，但不实际使用

    def execute(self, sql, params=None):
        result = self._client.execute(sql, params or [])
        return _TursoCursor(result)

    def executemany(self, sql, params_list):
        stmts = [(sql, list(p)) for p in params_list]
        if stmts:
            self._client.batch(stmts)

    def commit(self):
        pass  # Turso HTTP 模式自动提交

    def close(self):
        self._client.close()


class _TursoCursor:
    """包装 Turso ResultSet，使其兼容 sqlite3 cursor 接口。"""

    def __init__(self, result):
        self._result = result
        self._iter = iter(result)

    def fetchone(self):
        try:
            return next(self._iter)
        except StopIteration:
            return None

    def fetchall(self):
        return list(self._result)

    @property
    def description(self):
        return [(c,) for c in self._result.columns]

    def __iter__(self):
        return self._iter


def get_conn():
    if TURSO_URL and TURSO_TOKEN:
        from libsql_client.sync import create_client_sync
        client = create_client_sync(TURSO_URL, auth_token=TURSO_TOKEN)
        return _TursoConn(client)

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_db():
    conn = get_conn()
    cur = conn.cursor()

    cur.executescript("""
    CREATE TABLE IF NOT EXISTS teachers (
        id INTEGER PRIMARY KEY,
        code TEXT,
        name TEXT NOT NULL,
        department TEXT,
        title TEXT,
        raw_json TEXT
    );

    CREATE TABLE IF NOT EXISTS courses (
        id INTEGER PRIMARY KEY,
        code TEXT,
        name TEXT NOT NULL,
        credit REAL,
        department TEXT,
        language TEXT,
        categories TEXT,
        target_years TEXT,
        last_semester TEXT,
        main_teacher_id INTEGER,
        main_teacher_name TEXT,
        rating_count INTEGER,
        rating_avg REAL,
        rating_score REAL,
        rating_distribution TEXT,
        raw_json TEXT
    );

    CREATE TABLE IF NOT EXISTS reviews (
        id INTEGER PRIMARY KEY,
        course_id INTEGER,
        course_name TEXT,
        semester TEXT,
        score REAL,
        rating INTEGER,
        content TEXT,
        moderator_remark TEXT,
        vote_like INTEGER DEFAULT 0,
        vote_dislike INTEGER DEFAULT 0,
        created_at TEXT,
        updated_at TEXT,
        raw_json TEXT
    );

    CREATE TABLE IF NOT EXISTS review_tags (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        review_id INTEGER NOT NULL,
        tag TEXT NOT NULL,
        FOREIGN KEY (review_id) REFERENCES reviews(id)
    );

    CREATE TABLE IF NOT EXISTS scrape_meta (
        key TEXT PRIMARY KEY,
        value TEXT
    );

    CREATE INDEX IF NOT EXISTS idx_reviews_course ON reviews(course_id);
    CREATE INDEX IF NOT EXISTS idx_reviews_rating ON reviews(rating);
    CREATE INDEX IF NOT EXISTS idx_reviews_created ON reviews(created_at);
    CREATE INDEX IF NOT EXISTS idx_reviews_semester ON reviews(semester);
    CREATE INDEX IF NOT EXISTS idx_review_tags_tag ON review_tags(tag);
    CREATE INDEX IF NOT EXISTS idx_teachers_name ON teachers(name);
    CREATE INDEX IF NOT EXISTS idx_courses_name ON courses(name);
    CREATE INDEX IF NOT EXISTS idx_courses_code ON courses(code);
    CREATE INDEX IF NOT EXISTS idx_courses_teacher ON courses(main_teacher_id);
    """)

    conn.commit()
    conn.close()


# ---- Teachers ----

def upsert_teachers_batch(items: list):
    conn = get_conn()
    conn.executemany(
        "INSERT OR REPLACE INTO teachers (id, code, name, department, title, raw_json) VALUES (?, ?, ?, ?, ?, ?)",
        [(d.get("id"), d.get("code"), d.get("name"), d.get("department"),
          d.get("title"), str(d)) for d in items]
    )
    conn.commit()
    conn.close()


def get_existing_teacher_ids() -> set:
    conn = get_conn()
    rows = conn.execute("SELECT id FROM teachers").fetchall()
    conn.close()
    return {r["id"] for r in rows}


# ---- Courses ----

def upsert_courses_batch(items: list):
    conn = get_conn()
    conn.executemany(
        """INSERT OR REPLACE INTO courses
           (id, code, name, credit, department, language, categories, target_years,
            last_semester, main_teacher_id, main_teacher_name,
            rating_count, rating_avg, rating_score, rating_distribution, raw_json)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        [(
            d.get("id"), d.get("code"), d.get("name"), d.get("credit"),
            d.get("department"), d.get("language"),
            ",".join(d.get("categories") or []),
            ",".join(d.get("target_years") or []),
            d.get("last_semester"),
            (d.get("main_teacher") or {}).get("id"),
            (d.get("main_teacher") or {}).get("name"),
            (d.get("rating") or {}).get("count"),
            (d.get("rating") or {}).get("avg"),
            (d.get("rating") or {}).get("score"),
            str((d.get("rating") or {}).get("distribution")),
            str(d)
        ) for d in items]
    )
    conn.commit()
    conn.close()


def get_existing_course_ids() -> set:
    conn = get_conn()
    rows = conn.execute("SELECT id FROM courses").fetchall()
    conn.close()
    return {r["id"] for r in rows}


# ---- Reviews ----

def upsert_review(data: dict, course_id: int = None, course_name: str = None):
    conn = get_conn()
    vote = data.get("vote") or {}
    conn.execute(
        """INSERT OR REPLACE INTO reviews
           (id, course_id, course_name, semester, score, rating, content,
            moderator_remark, vote_like, vote_dislike, created_at, updated_at, raw_json)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (data.get("id"),
         course_id or data.get("course_id"),
         course_name or (data.get("course") or {}).get("name"),
         data.get("semester"),
         data.get("score"),
         data.get("rating"),
         data.get("content"),
         data.get("moderator_remark"),
         vote.get("like_count", 0),
         vote.get("dislike_count", 0),
         data.get("created_at"),
         data.get("updated_at"),
         str(data))
    )
    conn.commit()
    conn.close()


def upsert_reviews_batch(items: list, course_id: int = None, course_name: str = None):
    conn = get_conn()
    for data in items:
        vote = data.get("vote") or {}
        conn.execute(
            """INSERT OR REPLACE INTO reviews
               (id, course_id, course_name, semester, score, rating, content,
                moderator_remark, vote_like, vote_dislike, created_at, updated_at, raw_json)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (data.get("id"),
             course_id or data.get("course_id"),
             course_name or (data.get("course") or {}).get("name"),
             data.get("semester"),
             data.get("score"),
             data.get("rating"),
             data.get("content"),
             data.get("moderator_remark"),
             vote.get("like_count", 0),
             vote.get("dislike_count", 0),
             data.get("created_at"),
             data.get("updated_at"),
             str(data))
        )
    conn.commit()
    conn.close()


def get_existing_review_ids() -> set:
    conn = get_conn()
    rows = conn.execute("SELECT id FROM reviews").fetchall()
    conn.close()
    return {r["id"] for r in rows}


# ---- Meta ----

def get_meta(key: str) -> str | None:
    conn = get_conn()
    row = conn.execute("SELECT value FROM scrape_meta WHERE key=?", (key,)).fetchone()
    conn.close()
    return row["value"] if row else None


def set_meta(key: str, value: str):
    conn = get_conn()
    conn.execute("INSERT OR REPLACE INTO scrape_meta (key, value) VALUES (?, ?)", (key, value))
    conn.commit()
    conn.close()


# ---- Stats ----

def get_stats() -> dict:
    conn = get_conn()
    stats = {
        "teachers": conn.execute("SELECT COUNT(*) as c FROM teachers").fetchone()["c"],
        "courses": conn.execute("SELECT COUNT(*) as c FROM courses").fetchone()["c"],
        "reviews": conn.execute("SELECT COUNT(*) as c FROM reviews").fetchone()["c"],
        "tags": conn.execute("SELECT COUNT(DISTINCT tag) as c FROM review_tags").fetchone()["c"],
    }
    conn.close()
    return stats
