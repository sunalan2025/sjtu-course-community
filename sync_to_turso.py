"""把本地 sjtu_course.db 数据同步到 Turso 云端。

用法：
    1. 先安装依赖: pip install libsql-client
    2. 填入下方 TURSO_URL 和 TURSO_TOKEN
    3. 运行: python sync_to_turso.py
"""
import sqlite3
from libsql_client.dbapi2 import connect

# ====== 改成你的 Turso 连接信息 ======
TURSO_URL = "libsql://sjtu-course-xxx.turso.io"  # 替换为你的 URL
TURSO_TOKEN = "eyJ..."                             # 替换为你的 Token
# =====================================

SCHEMA = """
CREATE TABLE IF NOT EXISTS teachers (
    id INTEGER PRIMARY KEY, code TEXT, name TEXT NOT NULL,
    department TEXT, title TEXT, raw_json TEXT
);
CREATE TABLE IF NOT EXISTS courses (
    id INTEGER PRIMARY KEY, code TEXT, name TEXT NOT NULL,
    credit REAL, department TEXT, language TEXT, categories TEXT,
    target_years TEXT, last_semester TEXT, main_teacher_id INTEGER,
    main_teacher_name TEXT, rating_count INTEGER, rating_avg REAL,
    rating_score REAL, rating_distribution TEXT, raw_json TEXT
);
CREATE TABLE IF NOT EXISTS reviews (
    id INTEGER PRIMARY KEY, course_id INTEGER, course_name TEXT,
    semester TEXT, score REAL, rating INTEGER, content TEXT,
    moderator_remark TEXT, vote_like INTEGER DEFAULT 0,
    vote_dislike INTEGER DEFAULT 0, created_at TEXT, updated_at TEXT,
    raw_json TEXT
);
CREATE TABLE IF NOT EXISTS review_tags (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    review_id INTEGER NOT NULL, tag TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS scrape_meta (
    key TEXT PRIMARY KEY, value TEXT
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
"""

TABLES = ["teachers", "courses", "reviews", "review_tags", "scrape_meta"]


def main():
    print("连接本地数据库...")
    local = sqlite3.connect("sjtu_course.db")
    local.row_factory = sqlite3.Row

    print("连接 Turso 云端...")
    remote = connect(TURSO_URL, auth_token=TURSO_TOKEN)

    print("在 Turso 建表（如已存在则跳过）...")
    for stmt in SCHEMA.strip().split(";"):
        stmt = stmt.strip()
        if stmt:
            remote.execute(stmt)
    remote.commit()

    for table in TABLES:
        rows = local.execute(f"SELECT * FROM {table}").fetchall()
        if not rows:
            print(f"  {table}: 空表，跳过")
            continue

        cols = [d[0] for d in local.execute(f"SELECT * FROM {table}").description]
        placeholders = ",".join(["?"] * len(cols))
        col_names = ",".join(cols)

        total = len(rows)
        print(f"  {table}: {total} 行", end="", flush=True)

        for i in range(0, total, 500):
            batch = [tuple(r) for r in rows[i:i + 500]]
            remote.executemany(
                f"INSERT OR REPLACE INTO {table} ({col_names}) VALUES ({placeholders})",
                batch,
            )
            print(".", end="", flush=True)

        remote.commit()
        print(" 完成")

    local.close()
    print("\n✅ 同步完成！")


if __name__ == "__main__":
    main()
