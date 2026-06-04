import re
import database as db
from api_client import APIClient

TAG_PATTERNS = [
    "给分", "签到", "考试", "期末", "期中", "作业", "实验", "论文",
    "开卷", "闭卷", "点名", "提问", "pre", "presentation", "小组",
    "退课", "推荐", "水课", "硬课", "捞人", "调分", "平时分",
    "课堂", "PPT", "教材", "老师", "助教", "答疑", "收获",
    "考核", "上课", "课程内容", "授课质量", "自由度",
]

TAG_RE = re.compile("|".join(re.escape(t) for t in TAG_PATTERNS), re.IGNORECASE)


def extract_tags(content: str) -> list:
    if not content:
        return []
    return list(set(m.group().lower() for m in TAG_RE.finditer(content)))


class Scraper:
    def __init__(self, client: APIClient, full: bool = False):
        self.client = client
        self.full = full

    def run(self):
        db.init_db()
        user = self.client.get_me()
        if not user:
            raise RuntimeError("未登录，请先登录")

        print("\n=== 开始爬取 ===\n")

        print("[1/3] 爬取教师列表...")
        self.scrape_teachers()

        print("\n[2/3] 爬取课程列表...")
        self.scrape_courses()

        print("\n[3/3] 爬取全部点评...")
        self.scrape_reviews()

        print("\n=== 爬取完成 ===")
        stats = db.get_stats()
        print(f"  教师: {stats['teachers']}")
        print(f"  课程: {stats['courses']}")
        print(f"  点评: {stats['reviews']}")
        print(f"  标签: {stats['tags']}")

    def scrape_teachers(self):
        existing = set() if self.full else db.get_existing_teacher_ids()
        items = self.client.get_all_pages("/teacher/", existing_ids=existing if not self.full else None)
        new_items = [t for t in items if t.get("id") not in existing]
        batch_size = 500
        for i in range(0, len(new_items), batch_size):
            db.upsert_teachers_batch(new_items[i:i+batch_size])
        print(f"  新增 {len(new_items)} 位教师 (共 {len(items)} 位)")

    def scrape_courses(self):
        existing = set() if self.full else db.get_existing_course_ids()
        items = self.client.get_all_pages("/course/", existing_ids=existing if not self.full else None)
        new_items = [c for c in items if c.get("id") not in existing]
        batch_size = 500
        for i in range(0, len(new_items), batch_size):
            db.upsert_courses_batch(new_items[i:i+batch_size])
        print(f"  新增 {len(new_items)} 门课程 (共 {len(items)} 门)")

    def scrape_reviews(self):
        existing = set() if self.full else db.get_existing_review_ids()
        items = self.client.get_all_pages("/review/", existing_ids=existing if not self.full else None)
        new_items = [r for r in items if r.get("id") not in existing]

        # 批量写入点评
        batch_size = 500
        for i in range(0, len(new_items), batch_size):
            batch = new_items[i:i+batch_size]
            self._flush_review_batch(batch)
            written = min(i + batch_size, len(new_items))
            if written % 5000 < batch_size or written == len(new_items):
                print(f"  已写入 {written}/{len(new_items)} 条")

        # 批量提取并写入标签
        print("  提取标签中...")
        tag_pairs = []
        for r in new_items:
            tags = extract_tags(r.get("content"))
            for t in tags:
                tag_pairs.append((r["id"], t))

        conn = db.get_conn()
        conn.executemany(
            "INSERT OR IGNORE INTO review_tags (review_id, tag) VALUES (?, ?)",
            tag_pairs
        )
        conn.commit()
        conn.close()

        print(f"  新增 {len(new_items)} 条点评 (共 {len(items)} 条)")

    def _flush_review_batch(self, batch):
        conn = db.get_conn()
        for data in batch:
            course = data.get("course") or {}
            vote = data.get("vote") or {}
            conn.execute(
                """INSERT OR REPLACE INTO reviews
                   (id, course_id, course_name, semester, score, rating, content,
                    moderator_remark, vote_like, vote_dislike, created_at, updated_at, raw_json)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (data.get("id"),
                 data.get("course_id") or course.get("id"),
                 course.get("name"),
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
