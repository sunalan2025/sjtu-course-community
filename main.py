import argparse
import getpass
import sys

import database as db
import search
from api_client import APIClient
from scraper import Scraper


def cmd_scrape(args):
    db.init_db()
    email = input("邮箱: ").strip()
    if "@" not in email:
        email = f"{email}@sjtu.edu.cn"
    password = getpass.getpass("密码: ")

    client = APIClient()
    try:
        client.login(email, password)
    except RuntimeError as e:
        print(f"错误: {e}", file=sys.stderr)
        sys.exit(1)

    scraper = Scraper(client, full=args.full)
    scraper.run()


def _print_results(results, limit=50):
    if not results:
        print("未找到结果")
        return
    for i, row in enumerate(results[:limit]):
        print(f"\n--- [{i+1}] ---")
        for k, v in row.items():
            if v is not None:
                val = str(v)
                if len(val) > 200:
                    val = val[:200] + "..."
                print(f"  {k}: {val}")
    total = len(results)
    if total > limit:
        print(f"\n... 仅显示前 {limit} 条，共 {total} 条结果")
    else:
        print(f"\n共 {total} 条结果")


def cmd_search(args):
    db.init_db()
    limit = args.limit or 50

    if args.teacher:
        if args.summary:
            results = search.get_teacher_summary(args.teacher)
            print(f"\n=== 教师汇总: {args.teacher} ===")
        else:
            results = search.search_by_teacher(args.teacher)
            print(f"\n=== 教师搜索: {args.teacher} ===")
    elif args.rating is not None:
        min_r = args.rating
        max_r = args.rating_max if args.rating_max else args.rating
        results = search.search_by_rating(min_r, max_r, args.course)
        label = f"{min_r}星" if min_r == max_r else f"{min_r}-{max_r}星"
        print(f"\n=== 评分: {label} ===")
    elif args.time:
        parts = args.time.split(":")
        if len(parts) != 2:
            print("时间格式: YYYY-MM-DD:YYYY-MM-DD", file=sys.stderr)
            sys.exit(1)
        results = search.search_by_time(parts[0], parts[1])
        print(f"\n=== 时间: {parts[0]} ~ {parts[1]} ===")
    elif args.topic:
        results = search.search_by_topic(args.topic)
        print(f"\n=== 话题: {args.topic} ===")
    elif args.semester:
        results = search.search_by_semester(args.semester)
        print(f"\n=== 学期: {args.semester} ===")
    elif args.course:
        if args.summary:
            results = search.get_course_summary(args.course)
            print(f"\n=== 课程汇总: {args.course} ===")
        else:
            results = search.search_by_course(args.course)
            print(f"\n=== 课程搜索: {args.course} ===")
    elif args.top:
        results = search.get_top_courses(limit)
        print(f"\n=== 热门课程 TOP {limit} ===")
    elif args.query:
        results = search.full_text_search(args.query)
        print(f"\n=== 全文搜索: {args.query} ===")
    else:
        print("请指定搜索条件，使用 --help 查看帮助")
        sys.exit(1)

    _print_results(results, limit)


def cmd_stats(args):
    db.init_db()
    stats = db.get_stats()
    print("\n=== 数据库统计 ===")
    print(f"  教师: {stats['teachers']}")
    print(f"  课程: {stats['courses']}")
    print(f"  点评: {stats['reviews']}")
    print(f"  标签: {stats['tags']}")


def main():
    parser = argparse.ArgumentParser(
        description="SJTU 选课社区数据爬虫 & 搜索工具"
    )
    subparsers = parser.add_subparsers(dest="command", help="可用命令")

    # scrape
    p_scrape = subparsers.add_parser("scrape", help="爬取网站数据")
    p_scrape.add_argument("--full", "-f", action="store_true",
                          help="全量模式：覆盖更新所有数据（默认只爬取新数据）")

    # search
    p_search = subparsers.add_parser("search", help="搜索数据")
    p_search.add_argument("--teacher", "-t", help="按教师名搜索")
    p_search.add_argument("--rating", "-r", type=int, help="按评分搜索（最低星数）")
    p_search.add_argument("--rating-max", type=int, help="最高星数（配合 --rating）")
    p_search.add_argument("--time", help="按时间搜索，格式: YYYY-MM-DD:YYYY-MM-DD")
    p_search.add_argument("--topic", help="按话题/标签搜索")
    p_search.add_argument("--semester", help="按学期搜索 (如 2025-2026-1)")
    p_search.add_argument("--course", "-c", help="按课程名/代码搜索")
    p_search.add_argument("--query", "-q", help="全文搜索点评内容")
    p_search.add_argument("--top", action="store_true", help="查看热门高分课程")
    p_search.add_argument("--limit", "-l", type=int, default=50, help="显示条数限制")
    p_search.add_argument("--summary", "-s", action="store_true", help="显示汇总统计")

    # stats
    subparsers.add_parser("stats", help="查看数据库统计")

    args = parser.parse_args()

    if args.command == "scrape":
        cmd_scrape(args)
    elif args.command == "search":
        cmd_search(args)
    elif args.command == "stats":
        cmd_stats(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
