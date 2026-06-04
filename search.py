import database as db


def search_by_teacher(name: str) -> list:
    if not name or not name.strip():
        return []
    conn = db.get_conn()
    rows = conn.execute(
        """SELECT t.name as teacher_name, t.department, t.title,
                  c.name as course_name, c.code, c.credit, c.rating_avg,
                  c.rating_count
           FROM teachers t
           JOIN courses c ON c.main_teacher_id = t.id
           WHERE t.name LIKE ?
           ORDER BY c.rating_count DESC""",
        (f"%{name}%",)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def search_by_rating(min_rating: int = 1, max_rating: int = 5,
                     course_name: str = None) -> list:
    conn = db.get_conn()
    if course_name:
        rows = conn.execute(
            """SELECT r.id, r.course_name, r.semester, r.content,
                      r.rating, r.score, r.created_at, r.vote_like, r.vote_dislike
               FROM reviews r
               WHERE r.rating BETWEEN ? AND ? AND r.course_name LIKE ?
               ORDER BY r.created_at DESC
               LIMIT 200""",
            (min_rating, max_rating, f"%{course_name}%")
        ).fetchall()
    else:
        rows = conn.execute(
            """SELECT r.id, r.course_name, r.semester, r.content,
                      r.rating, r.score, r.created_at, r.vote_like, r.vote_dislike
               FROM reviews r
               WHERE r.rating BETWEEN ? AND ?
               ORDER BY r.created_at DESC
               LIMIT 200""",
            (min_rating, max_rating)
        ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def search_by_time(start_date: str, end_date: str) -> list:
    if not start_date or not end_date:
        return []
    conn = db.get_conn()
    rows = conn.execute(
        """SELECT r.id, r.course_name, r.semester, r.content,
                  r.rating, r.score, r.created_at
           FROM reviews r
           WHERE r.created_at BETWEEN ? AND ?
           ORDER BY r.created_at DESC
           LIMIT 200""",
        (start_date, end_date)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def search_by_topic(keyword: str) -> list:
    if not keyword or not keyword.strip():
        return []
    conn = db.get_conn()
    rows = conn.execute(
        """SELECT DISTINCT r.id, r.course_name, r.semester, r.content,
                  r.rating, r.score, r.created_at, GROUP_CONCAT(rt.tag) as tags
           FROM reviews r
           JOIN review_tags rt ON rt.review_id = r.id
           WHERE rt.tag LIKE ?
           GROUP BY r.id
           ORDER BY r.created_at DESC
           LIMIT 200""",
        (f"%{keyword}%",)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def search_by_course(keyword: str) -> list:
    if not keyword or not keyword.strip():
        return []
    conn = db.get_conn()
    rows = conn.execute(
        """SELECT c.id, c.name, c.code, c.department, c.credit,
                  c.language, c.categories, c.main_teacher_name,
                  c.rating_count, c.rating_avg, c.rating_score
           FROM courses c
           WHERE c.name LIKE ? OR c.code LIKE ?
           ORDER BY c.rating_count DESC
           LIMIT 100""",
        (f"%{keyword}%", f"%{keyword}%")
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def full_text_search(query: str) -> list:
    if not query or not query.strip():
        return []
    conn = db.get_conn()
    rows = conn.execute(
        """SELECT r.id, r.course_name, r.semester, r.content,
                  r.rating, r.score, r.created_at
           FROM reviews r
           WHERE r.content LIKE ? OR r.course_name LIKE ?
           ORDER BY r.created_at DESC
           LIMIT 200""",
        (f"%{query}%", f"%{query}%")
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_teacher_summary(teacher_name: str) -> list:
    if not teacher_name or not teacher_name.strip():
        return []
    conn = db.get_conn()
    rows = conn.execute(
        """SELECT t.name, t.department, t.title,
                  COUNT(DISTINCT c.id) as course_count,
                  SUM(c.rating_count) as total_reviews,
                  ROUND(AVG(c.rating_avg), 2) as avg_rating
           FROM teachers t
           JOIN courses c ON c.main_teacher_id = t.id
           WHERE t.name LIKE ?
           GROUP BY t.id
           ORDER BY total_reviews DESC""",
        (f"%{teacher_name}%",)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_course_summary(course_name: str) -> list:
    if not course_name or not course_name.strip():
        return []
    conn = db.get_conn()
    rows = conn.execute(
        """SELECT c.name, c.code, c.department, c.credit, c.language,
                  c.main_teacher_name, c.categories,
                  c.rating_count, c.rating_avg, c.rating_score,
                  (SELECT COUNT(*) FROM reviews r WHERE r.course_id = c.id) as review_count_in_db
           FROM courses c
           WHERE c.name LIKE ?
           ORDER BY c.rating_count DESC
           LIMIT 50""",
        (f"%{course_name}%",)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def search_by_semester(semester: str) -> list:
    if not semester or not semester.strip():
        return []
    conn = db.get_conn()
    rows = conn.execute(
        """SELECT r.id, r.course_name, r.semester, r.content,
                  r.rating, r.score, r.created_at
           FROM reviews r
           WHERE r.semester LIKE ?
           ORDER BY r.created_at DESC
           LIMIT 200""",
        (f"%{semester}%",)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_top_courses(limit: int = 20) -> list:
    conn = db.get_conn()
    rows = conn.execute(
        """SELECT c.name, c.code, c.department, c.main_teacher_name,
                  c.rating_count, c.rating_avg
           FROM courses c
           WHERE c.rating_count > 0
           ORDER BY c.rating_avg DESC, c.rating_count DESC
           LIMIT ?""",
        (limit,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]
