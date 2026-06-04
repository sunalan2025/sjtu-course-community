import json
from flask import Flask, request, render_template_string, jsonify
import database as db

app = Flask(__name__)

# ============================================================
# Design system — pixel-perfect match of course.sjtu.plus
# ============================================================
TAILWIND_CDN = '<script src="https://cdn.tailwindcss.com"></script>'

TAILWIND_CONFIG = """
<script>
tailwind.config = {
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        background: 'var(--background)',
        foreground: 'var(--foreground)',
        card: { DEFAULT: 'var(--card)', foreground: 'var(--card-foreground)' },
        popover: { DEFAULT: 'var(--popover)', foreground: 'var(--popover-foreground)' },
        primary: { DEFAULT: 'var(--primary)', foreground: 'var(--primary-foreground)' },
        secondary: { DEFAULT: 'var(--secondary)', foreground: 'var(--secondary-foreground)' },
        muted: { DEFAULT: 'var(--muted)', foreground: 'var(--muted-foreground)' },
        accent: { DEFAULT: 'var(--accent)', foreground: 'var(--accent-foreground)' },
        destructive: { DEFAULT: 'var(--destructive)', foreground: 'var(--destructive-foreground)' },
        border: 'var(--border)',
        ring: 'var(--ring)',
        input: 'var(--input)',
      },
      borderRadius: {
        lg: 'var(--radius)',
        md: 'calc(var(--radius) * 0.6)',
        sm: 'calc(var(--radius) * 0.4)',
      },
      fontFamily: {
        sans: ['"Noto Sans SC"', 'system-ui', '-apple-system', 'BlinkMacSystemFont', '"Segoe UI"', 'Roboto', '"Helvetica Neue"', 'Arial', 'sans-serif'],
        mono: ['ui-monospace', 'SFMono-Regular', 'Menlo', 'Monaco', 'Consolas', '"Liberation Mono"', '"Courier New"', 'monospace'],
      },
    }
  }
}
</script>
"""

# Load Noto Sans SC from Google Fonts (400/500/600/700 weights)
GOOGLE_FONTS = '<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin><link href="https://fonts.googleapis.com/css2?family=Noto+Sans+SC:wght@400;500;600;700&display=swap" rel="stylesheet">'

BASE_CSS = """
<style>
  :root {
    --background: #ffffff;
    --foreground: #1a1a1a;
    --card: #ffffff;
    --card-foreground: #1a1a1a;
    --popover: #ffffff;
    --popover-foreground: #1a1a1a;
    --primary: #0f766e;
    --primary-foreground: #f0fdfa;
    --secondary: #f4f4f5;
    --secondary-foreground: #27272a;
    --muted: #f5f5f5;
    --muted-foreground: #737373;
    --accent: #f5f5f5;
    --accent-foreground: #1c1c1c;
    --destructive: #ef4444;
    --destructive-foreground: #fafafa;
    --border: #e5e5e5;
    --ring: #a3a3a3;
    --input: #e5e5e5;
    --radius: 0.875rem;
  }
  .dark {
    --background: #1c1c1c;
    --foreground: #fafafa;
    --card: #1c1c1c;
    --card-foreground: #fafafa;
    --popover: #1c1c1c;
    --popover-foreground: #fafafa;
    --primary: #0d6b64;
    --primary-foreground: #f0fdfa;
    --secondary: #27272a;
    --secondary-foreground: #fafafa;
    --muted: #262626;
    --muted-foreground: #a3a3a3;
    --accent: #262626;
    --accent-foreground: #fafafa;
    --destructive: #dc2626;
    --destructive-foreground: #fafafa;
    --border: rgba(255,255,255,0.1);
    --ring: #737373;
    --input: rgba(255,255,255,0.1);
  }
  *, ::before, ::after { border-color: var(--border); }
  html { scroll-behavior: smooth; }
  body {
    -webkit-font-smoothing: antialiased;
    -moz-osx-font-smoothing: grayscale;
    font-feature-settings: "cv02", "cv03", "cv04", "cv11";
  }
</style>
"""

LAYOUT = """<!DOCTYPE html>
<html lang="zh-CN" class="">
<head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="theme-color" content="#0f766e">
<title>{{ title }} - SJTU选课社区</title>
{{ fonts|safe }}
{{ tailwind|safe }}
{{ config|safe }}
{{ css|safe }}
</head>
<body class="min-h-screen bg-background text-foreground font-sans">
  <header class="sticky top-0 z-50 w-full border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
    <div class="mx-auto flex h-14 max-w-[1440px] items-center px-4">
      <a href="/" class="flex items-center gap-2 font-semibold text-lg">SJTU选课社区</a>
      <nav class="relative ml-8 hidden h-full gap-4 text-sm md:flex">
        <a href="/" class="flex items-center {{ 'font-medium text-primary' if page=='home' else 'text-foreground transition-colors hover:text-primary' }}">首页</a>
        <a href="/courses" class="flex items-center {{ 'font-medium text-primary' if page=='courses' else 'text-foreground transition-colors hover:text-primary' }}">课程</a>
        <a href="/teachers" class="flex items-center {{ 'font-medium text-primary' if page=='teachers' else 'text-foreground transition-colors hover:text-primary' }}">教师</a>
        <a href="/reviews" class="flex items-center {{ 'font-medium text-primary' if page=='reviews' else 'text-foreground transition-colors hover:text-primary' }}">点评</a>
      </nav>
      <div class="ml-auto flex items-center gap-2">
        <button onclick="toggleDark()" class="inline-flex items-center justify-center rounded-md text-sm font-medium transition-colors hover:bg-accent hover:text-accent-foreground h-9 w-9" aria-label="切换主题">
          <svg id="sun-icon" class="h-4 w-4 hidden dark:block" fill="none" stroke="currentColor" viewBox="0 0 24 24"><circle cx="12" cy="12" r="5"/><path d="M12 1v2M12 21v2M4.22 4.22l1.42 1.42M18.36 18.36l1.42 1.42M1 12h2M21 12h2M4.22 19.78l1.42-1.42M18.36 5.64l1.42-1.42"/></svg>
          <svg id="moon-icon" class="h-4 w-4 block dark:hidden" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/></svg>
        </button>
      </div>
    </div>
  </header>

  <div class="flex-1">
    <div class="mx-auto max-w-[1440px] px-4 py-6">
      {{ content|safe }}
    </div>
  </div>

  <footer class="border-t bg-background">
    <div class="mx-auto flex max-w-[1440px] flex-col gap-3 px-4 py-6 text-sm text-muted-foreground sm:flex-row sm:items-center sm:justify-between">
      <p>&copy; 2025 SJTU选课社区. 保留所有权利。</p>
      <nav class="flex gap-4">
        <a href="https://course.sjtu.plus" class="transition-colors hover:text-foreground" target="_blank">原始站点</a>
      </nav>
    </div>
  </footer>

  <script>
  function toggleDark() {
    document.documentElement.classList.toggle('dark');
    localStorage.setItem('theme', document.documentElement.classList.contains('dark') ? 'dark' : 'light');
  }
  (function() {
    const saved = localStorage.getItem('theme');
    if (saved === 'dark' || (!saved && window.matchMedia('(prefers-color-scheme: dark)').matches)) {
      document.documentElement.classList.add('dark');
    }
  })();
  </script>
</body></html>"""


def render(title, page, content, **kw):
    return render_template_string(
        LAYOUT, title=title, page=page, content=content,
        tailwind=TAILWIND_CDN, config=TAILWIND_CONFIG, css=BASE_CSS,
        fonts=GOOGLE_FONTS, **kw
    )


def stars_html(n):
    if not n:
        return '<span class="text-muted-foreground">-</span>'
    full = int(n)
    return (
        f'<span class="text-yellow-500 tracking-tight">'
        f'{"&#9733;" * full}{"&#9734;" * (5 - full)}'
        f'</span>'
        f' <span class="text-muted-foreground text-xs font-mono">{n}</span>'
    )


def paginate(total, page, per_page, base_url, **params):
    pages = (total + per_page - 1) // per_page
    if pages <= 1:
        return ""
    parts = ['<div class="flex items-center justify-center gap-1 mt-6">']
    clean = {k: v for k, v in params.items() if v}

    def page_link(p, label=None):
        qs = "&".join(f"{k}={v}" for k, v in clean.items())
        href = f"{base_url}?page={p}&{qs}" if qs else f"{base_url}?page={p}"
        return f'<a href="{href}" class="inline-flex items-center justify-center rounded-md border border-border bg-background px-3 py-1.5 text-sm font-medium transition-colors hover:bg-accent hover:text-accent-foreground">{label or p}</a>'

    def page_current(p):
        return f'<span class="inline-flex items-center justify-center rounded-md bg-primary px-3 py-1.5 text-sm font-medium text-primary-foreground">{p}</span>'

    if page > 1:
        parts.append(page_link(page - 1, "上一页"))
    for p in range(max(1, page - 3), min(pages + 1, page + 4)):
        parts.append(page_current(p) if p == page else page_link(p))
    if page < pages:
        parts.append(page_link(page + 1, "下一页"))
    parts.append('</div>')
    return "".join(parts)


# ============================================================
# 首页
# ============================================================
@app.route("/")
def home():
    stats = db.get_stats()
    conn = db.get_conn()
    dist = conn.execute(
        "SELECT rating, COUNT(*) as c FROM reviews WHERE rating IS NOT NULL GROUP BY rating ORDER BY rating"
    ).fetchall()
    dist_labels = json.dumps([str(r["rating"]) for r in dist])
    dist_data = json.dumps([r["c"] for r in dist])

    top = conn.execute(
        """SELECT c.id, c.name, c.code, c.main_teacher_name, c.rating_avg, c.rating_count
           FROM courses c WHERE c.rating_count > 0
           ORDER BY c.rating_avg DESC, c.rating_count DESC LIMIT 10"""
    ).fetchall()
    depts = conn.execute(
        """SELECT department, COUNT(*) as c FROM teachers
           WHERE department IS NOT NULL AND department != '无'
           GROUP BY department ORDER BY c DESC LIMIT 10"""
    ).fetchall()
    conn.close()

    stat_cards = "".join(
        f'<div class="rounded-xl border bg-card p-6 shadow-sm">'
        f'<div class="text-2xl font-bold text-primary">{v:,}</div>'
        f'<div class="text-sm text-muted-foreground mt-1">{l}</div></div>'
        for v, l in [
            (stats['teachers'], '教师'),
            (stats['courses'], '课程'),
            (stats['reviews'], '点评'),
            (stats['tags'], '话题标签'),
        ]
    )

    top_rows = "".join(
        f'<a href="/course/{r["id"]}" class="block border-b px-4 py-3 transition-colors hover:bg-muted/40">'
        f'<div class="flex min-w-0 items-center justify-between gap-3">'
        f'<div class="min-w-0 flex-1 space-y-1">'
        f'<div class="flex items-center gap-2 text-sm text-muted-foreground">'
        f'<span class="shrink-0 font-mono">{r["code"]}</span>'
        f'<span>{r["main_teacher_name"] or "-"}</span></div>'
        f'<div class="leading-tight font-semibold break-words">{r["name"]}</div></div>'
        f'<div class="shrink-0">{stars_html(round(r["rating_avg"],1) if r["rating_avg"] else None)}</div>'
        f'</div></a>'
        for r in top
    )

    content = f"""
    <div class="space-y-6">
      <h1 class="text-2xl font-bold tracking-tight">数据概览</h1>

      <div class="grid grid-cols-2 gap-4 md:grid-cols-4">
        {stat_cards}
      </div>

      <div class="grid gap-6 lg:grid-cols-2">
        <div class="rounded-xl border bg-card p-6 shadow-sm">
          <h3 class="mb-4 text-sm font-medium text-muted-foreground">评分分布</h3>
          <canvas id="ratingChart" height="200"></canvas>
        </div>
        <div class="rounded-xl border bg-card p-6 shadow-sm">
          <h3 class="mb-4 text-sm font-medium text-muted-foreground">院系教师数量 TOP 10</h3>
          <canvas id="deptChart" height="200"></canvas>
        </div>
      </div>

      <div class="rounded-xl border bg-card shadow-sm overflow-hidden">
        <div class="px-4 py-3 border-b">
          <h2 class="font-semibold">热门高分课程 TOP 10</h2>
        </div>
        <div>{top_rows if top_rows else '<div class="p-8 text-center text-muted-foreground">暂无数据</div>'}</div>
      </div>
    </div>

    <script src="https://cdn.jsdelivr.net/npm/chart.js@4"></script>
    <script>
    const isDark = document.documentElement.classList.contains('dark');
    const textColor = isDark ? '#a3a3a3' : '#737373';
    const gridColor = isDark ? 'rgba(255,255,255,0.1)' : '#e5e5e5';
    Chart.defaults.color = textColor;
    Chart.defaults.borderColor = gridColor;

    new Chart(document.getElementById('ratingChart'),{{
      type:'bar',
      data:{{labels:{dist_labels},datasets:[{{label:'点评数',data:{dist_data},backgroundColor:'#0f766e',borderRadius:4}}]}},
      options:{{responsive:true,plugins:{{legend:{{display:false}}}},scales:{{y:{{beginAtZero:true,grid:{{color:gridColor}}}},x:{{grid:{{display:false}}}}}}}}
    }});
    new Chart(document.getElementById('deptChart'),{{
      type:'bar',
      data:{{labels:{json.dumps([r['department'][:6] for r in depts])},datasets:[{{label:'教师数',data:{json.dumps([r['c'] for r in depts])},backgroundColor:'#0d6b64',borderRadius:4}}]}},
      options:{{indexAxis:'y',responsive:true,plugins:{{legend:{{display:false}}}},scales:{{x:{{beginAtZero:true,grid:{{color:gridColor}}}},y:{{grid:{{display:false}}}}}}}}
    }});
    </script>
    """
    return render("首页", "home", content)


# ============================================================
# 教师列表
# ============================================================
@app.route("/teachers")
def teachers():
    q = request.args.get("q", "").strip()
    page = max(1, int(request.args.get("page", 1)))
    per_page = 30
    conn = db.get_conn()

    where = "WHERE 1=1"
    params = []
    if q:
        where += " AND (t.name LIKE ? OR t.department LIKE ?)"
        params = [f"%{q}%", f"%{q}%"]

    total = conn.execute(f"SELECT COUNT(*) as c FROM teachers t {where}", params).fetchone()["c"]
    rows = conn.execute(
        f"""SELECT t.id, t.name, t.department, t.title,
                   COUNT(DISTINCT c.id) as course_count,
                   SUM(c.rating_count) as total_reviews,
                   ROUND(AVG(c.rating_avg), 2) as avg_rating
            FROM teachers t
            LEFT JOIN courses c ON c.main_teacher_id = t.id
            {where}
            GROUP BY t.id
            ORDER BY total_reviews DESC NULLS LAST
            LIMIT ? OFFSET ?""",
        params + [per_page, (page - 1) * per_page]
    ).fetchall()
    conn.close()

    teacher_rows = "".join(
        f'<a href="/teacher/{r["id"]}" class="block border-b px-4 py-3 transition-colors hover:bg-muted/40">'
        f'<div class="flex min-w-0 items-center gap-4">'
        f'<div class="min-w-0 flex-1 space-y-1">'
        f'<div class="font-semibold leading-tight">{r["name"]}</div>'
        f'<div class="flex items-center gap-3 text-sm text-muted-foreground">'
        f'<span>{r["department"] or "-"}</span>'
        f'<span>{r["title"] or "-"}</span>'
        f'<span>{r["course_count"] or 0} 门课程</span>'
        f'<span>{r["total_reviews"] or 0} 条点评</span>'
        f'</div></div>'
        f'<div class="shrink-0">{stars_html(round(r["avg_rating"],1) if r["avg_rating"] else None)}</div>'
        f'</div></a>'
        for r in rows
    )

    content = f"""
    <div class="space-y-4">
      <div class="flex items-baseline justify-between">
        <h1 class="text-2xl font-bold tracking-tight">教师列表</h1>
        <span class="text-sm text-muted-foreground">{total:,} 位</span>
      </div>
      <form method="get" class="flex gap-2">
        <input type="text" name="q" value="{q}" placeholder="搜索教师姓名或院系..."
               class="flex h-9 w-full rounded-md border border-input bg-background px-3 py-1 text-sm shadow-sm transition-colors placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring md:max-w-sm">
        <button type="submit" class="inline-flex items-center justify-center rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground shadow hover:bg-primary/90 transition-colors">搜索</button>
      </form>
      <div class="rounded-xl border bg-card shadow-sm overflow-hidden">
        {teacher_rows if teacher_rows else '<div class="p-8 text-center text-muted-foreground">暂无数据</div>'}
      </div>
      {paginate(total, page, per_page, '/teachers', q=q)}
    </div>
    """
    return render("教师", "teachers", content)


# ============================================================
# 教师详情
# ============================================================
@app.route("/teacher/<int:tid>")
def teacher_detail(tid):
    conn = db.get_conn()
    t = conn.execute("SELECT * FROM teachers WHERE id=?", (tid,)).fetchone()
    if not t:
        conn.close()
        return render("教师详情", "teachers", '<div class="p-8 text-center text-muted-foreground">教师不存在</div>')

    courses = conn.execute(
        """SELECT id, name, code, credit, rating_avg, rating_count
           FROM courses WHERE main_teacher_id=? ORDER BY rating_count DESC""",
        (tid,)
    ).fetchall()

    course_ids = [c["id"] for c in courses]
    reviews = []
    if course_ids:
        placeholders = ",".join("?" * len(course_ids))
        reviews = conn.execute(
            f"""SELECT r.*, c.name as cname FROM reviews r
                LEFT JOIN courses c ON c.id=r.course_id
                WHERE r.course_id IN ({placeholders})
                ORDER BY r.created_at DESC LIMIT 50""",
            course_ids
        ).fetchall()
    # 评分趋势：每个学期的平均分
    trend = []
    if course_ids:
        placeholders = ",".join("?" * len(course_ids))
        trend = conn.execute(
            f"""SELECT r.semester, ROUND(AVG(r.rating), 2) as avg_rating, COUNT(*) as cnt
                FROM reviews r
                WHERE r.course_id IN ({placeholders}) AND r.rating IS NOT NULL AND r.semester IS NOT NULL
                GROUP BY r.semester ORDER BY r.semester""",
            course_ids
        ).fetchall()

    # 每门课的评分对比
    course_compare = conn.execute(
        """SELECT c.name, c.code, c.rating_avg, c.rating_count
           FROM courses c WHERE c.main_teacher_id=? AND c.rating_count > 0
           ORDER BY c.rating_avg DESC""",
        (tid,)
    ).fetchall()

    conn.close()

    info_items = "".join(
        f'<div><div class="text-xs text-muted-foreground">{label}</div>'
        f'<div class="text-sm font-medium mt-0.5">{value}</div></div>'
        for label, value in [
            ("院系", t["department"] or "-"),
            ("职称", t["title"] or "-"),
            ("教师代码", t["code"] or "-"),
            ("课程数", str(len(courses))),
        ]
    )

    # 图表数据
    trend_labels = json.dumps([r["semester"] for r in trend])
    trend_data = json.dumps([r["avg_rating"] for r in trend])
    trend_counts = json.dumps([r["cnt"] for r in trend])

    # 课程排行榜
    course_rank_html = ""
    if course_compare:
        items = []
        for i, r in enumerate(course_compare):
            name = r["name"] or "?"
            avg = round(r["rating_avg"], 2) if r["rating_avg"] else 0
            cnt = r["rating_count"] or 0
            bar_w = max(8, avg / 5 * 100)
            items.append(
                f'<div class="flex items-center gap-3 py-2.5">'
                f'<span class="w-5 text-right text-xs text-muted-foreground">{i+1}</span>'
                f'<div class="flex-1 min-w-0">'
                f'<div class="flex items-center justify-between mb-1">'
                f'<span class="text-sm font-medium truncate">{name}</span>'
                f'<span class="text-sm font-mono text-muted-foreground ml-2 shrink-0">{avg}</span>'
                f'</div>'
                f'<div class="h-1.5 rounded-full bg-muted overflow-hidden">'
                f'<div class="h-full rounded-full bg-primary/60 transition-all duration-700" style="width:{bar_w}%"></div>'
                f'</div>'
                f'<div class="text-[11px] text-muted-foreground mt-0.5">{cnt} 条点评</div>'
                f'</div></div>'
            )
        course_rank_html = "".join(items)

    course_rows = "".join(
        f'<a href="/course/{c["id"]}" class="block border-b px-4 py-3 transition-colors hover:bg-muted/40">'
        f'<div class="flex min-w-0 items-center justify-between gap-3">'
        f'<div class="min-w-0 flex-1">'
        f'<div class="font-semibold leading-tight">{c["name"]}</div>'
        f'<div class="text-sm text-muted-foreground mt-0.5">{c["code"]} &middot; {c["credit"]} 学分</div></div>'
        f'<div class="shrink-0">{stars_html(round(c["rating_avg"],1) if c["rating_avg"] else None)}'
        f'<span class="text-xs text-muted-foreground ml-1">{c["rating_count"] or 0} 条</span></div>'
        f'</div></a>'
        for c in courses
    )

    review_cards = "".join(
        f'<article class="border-b px-4 py-3 transition-colors hover:bg-muted/30">'
        f'<div class="space-y-2">'
        f'<div class="flex items-center justify-between">'
        f'<a href="/course/{r["course_id"]}" class="text-sm font-medium text-primary hover:underline">{r["cname"] or "?"}</a>'
        f'{stars_html(r["rating"])}</div>'
        f'<div class="text-xs text-muted-foreground font-mono">{r["semester"] or ""} &middot; {r["created_at"] or ""}</div>'
        f'<div class="text-sm leading-relaxed whitespace-pre-wrap">{(r["content"] or "")[:300]}</div>'
        f'</div></article>'
        for r in reviews
    )

    content = f"""
    <div class="space-y-6">
      <a href="/teachers" class="inline-flex items-center text-sm text-muted-foreground hover:text-foreground transition-colors">
        <svg class="mr-1 h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7"/></svg>
        返回教师列表
      </a>

      <div class="rounded-xl border bg-card p-6 shadow-sm">
        <h1 class="text-xl font-bold">{t["name"]}</h1>
        <div class="mt-3 grid grid-cols-2 gap-4 sm:grid-cols-4">{info_items}</div>
      </div>

      <div class="grid gap-6 lg:grid-cols-3">
        <!-- 左侧面板 -->
        <div class="space-y-4 lg:col-span-1">
          <div class="rounded-xl border bg-card shadow-sm overflow-hidden">
            <div class="px-4 py-3 border-b"><h2 class="text-sm font-semibold">评分趋势（按学期）</h2></div>
            <div class="p-4" style="height:300px">
              <canvas id="trendChart"></canvas>
            </div>
          </div>
          {"" if not course_rank_html else f'''
          <div class="rounded-xl border bg-card shadow-sm overflow-hidden">
            <div class="px-4 py-3 border-b"><h2 class="font-semibold text-sm">各课程评分排行</h2></div>
            <div class="p-4 space-y-0.5">{course_rank_html}</div>
          </div>
          '''}
        </div>

        <!-- 右侧内容 -->
        <div class="space-y-6 lg:col-span-2">
          <div class="rounded-xl border bg-card shadow-sm overflow-hidden">
            <div class="px-4 py-3 border-b"><h2 class="font-semibold">教授课程 ({len(courses)} 门)</h2></div>
            {course_rows if course_rows else '<div class="p-8 text-center text-muted-foreground">暂无</div>'}
          </div>

          <div class="rounded-xl border bg-card shadow-sm overflow-hidden">
            <div class="px-4 py-3 border-b"><h2 class="font-semibold">相关点评 (最近50条)</h2></div>
            {review_cards if review_cards else '<div class="p-8 text-center text-muted-foreground">暂无点评</div>'}
          </div>
        </div>
      </div>
    </div>

    <script src="https://cdn.jsdelivr.net/npm/chart.js@4"></script>
    <script>
    const isDark = document.documentElement.classList.contains('dark');
    const txtColor = isDark ? '#a3a3a3' : '#737373';
    const gridColor = isDark ? 'rgba(255,255,255,0.1)' : '#e5e5e5';
    Chart.defaults.color = txtColor;
    Chart.defaults.borderColor = gridColor;

    const trendCtx = document.getElementById('trendChart');
    if (trendCtx) {{
      new Chart(trendCtx, {{
        type: 'line',
        data: {{
          labels: {trend_labels},
          datasets: [{{
            label: '平均评分',
            data: {trend_data},
            borderColor: '#0f766e',
            backgroundColor: 'rgba(15,118,110,0.1)',
            fill: true,
            tension: 0.3,
            pointRadius: 4,
            pointHoverRadius: 6
          }}, {{
            label: '点评数',
            data: {trend_counts},
            borderColor: '#737373',
            backgroundColor: 'transparent',
            borderDash: [5, 5],
            tension: 0.3,
            pointRadius: 3,
            yAxisID: 'y1'
          }}]
        }},
        options: {{
          responsive: true,
          maintainAspectRatio: false,
          interaction: {{ mode: 'index', intersect: false }},
          plugins: {{ legend: {{ position: 'bottom', labels: {{ usePointStyle: true, padding: 12, font: {{ size: 11 }} }} }} }},
          scales: {{
            y: {{ beginAtZero: false, min: 1, max: 5, title: {{ display: true, text: '评分' }}, grid: {{ color: gridColor }} }},
            y1: {{ position: 'right', beginAtZero: true, title: {{ display: true, text: '点评数' }}, grid: {{ drawOnChartArea: false }} }},
            x: {{ grid: {{ display: false }} }}
          }}
        }}
      }});
    }}
    </script>
    """
    return render(f"{t['name']} - 教师详情", "teachers", content)


# ============================================================
# 课程列表
# ============================================================
@app.route("/courses")
def courses():
    q = request.args.get("q", "").strip()
    dept = request.args.get("dept", "").strip()
    credit = request.args.get("credit", "").strip()
    rating = request.args.get("rating", "").strip()
    page = max(1, int(request.args.get("page", 1)))
    per_page = 30
    conn = db.get_conn()

    where = "WHERE 1=1"
    params = []
    if q:
        where += " AND (c.name LIKE ? OR c.code LIKE ? OR c.main_teacher_name LIKE ?)"
        params += [f"%{q}%", f"%{q}%", f"%{q}%"]
    if dept:
        where += " AND c.department = ?"
        params.append(dept)
    if credit:
        where += " AND c.credit = ?"
        params.append(float(credit))
    if rating:
        where += " AND c.rating_avg >= ?"
        params.append(float(rating))

    total = conn.execute(f"SELECT COUNT(*) as c FROM courses c {where}", params).fetchone()["c"]
    rows = conn.execute(
        f"""SELECT c.id, c.name, c.code, c.department, c.credit, c.language,
                   c.main_teacher_name, c.rating_avg, c.rating_count, c.categories
            FROM courses c {where}
            ORDER BY c.last_semester DESC, c.rating_count DESC NULLS LAST
            LIMIT ? OFFSET ?""",
        params + [per_page, (page - 1) * per_page]
    ).fetchall()

    depts = conn.execute(
        "SELECT DISTINCT department FROM courses WHERE department IS NOT NULL ORDER BY department"
    ).fetchall()
    credits = conn.execute(
        "SELECT DISTINCT credit FROM courses WHERE credit IS NOT NULL ORDER BY credit"
    ).fetchall()
    conn.close()

    dept_opts = "".join(
        f'<option value="{d["department"]}" {"selected" if d["department"]==dept else ""}>{d["department"]}</option>'
        for d in depts
    )
    credit_opts = "".join(
        f'<option value="{c["credit"]}" {"selected" if str(c["credit"])==credit else ""}>{c["credit"]}</option>'
        for c in credits
    )

    select_cls = ("flex h-9 rounded-md border border-input bg-background px-3 py-1 text-sm shadow-sm "
                  "transition-colors focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring")

    course_rows = "".join(
        f'<a href="/course/{r["id"]}" class="block border-b px-4 py-3 transition-colors hover:bg-muted/40">'
        f'<div class="flex min-w-0 items-center gap-4">'
        f'<div class="min-w-0 flex-1 space-y-1">'
        f'<div class="flex min-w-0 items-center gap-2 text-sm text-muted-foreground">'
        f'<span class="shrink-0 font-mono">{r["code"]}</span>'
        f'<span class="truncate">{r["main_teacher_name"] or "-"}</span></div>'
        f'<div class="leading-tight font-semibold break-words">{r["name"]}</div>'
        f'<div class="text-sm text-muted-foreground">{r["department"] or "-"} &middot; {r["credit"]} 学分</div>'
        f'</div>'
        f'<div class="shrink-0">{stars_html(round(r["rating_avg"],1) if r["rating_avg"] else None)}'
        f'<div class="text-xs text-muted-foreground text-right">{r["rating_count"] or 0} 条</div></div>'
        f'</div></a>'
        for r in rows
    )

    content = f"""
    <div class="space-y-4">
      <div class="flex items-baseline justify-between">
        <h1 class="text-2xl font-bold tracking-tight">课程列表</h1>
        <span class="text-sm text-muted-foreground">{total:,} 门</span>
      </div>
      <form method="get" class="flex flex-wrap gap-2">
        <input type="text" name="q" value="{q}" placeholder="搜索课程名、代码或教师..."
               class="flex h-9 flex-1 min-w-[200px] rounded-md border border-input bg-background px-3 py-1 text-sm shadow-sm placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring">
        <select name="dept" class="{select_cls}"><option value="">全部院系</option>{dept_opts}</select>
        <select name="credit" class="{select_cls}"><option value="">全部学分</option>{credit_opts}</select>
        <select name="rating" class="{select_cls}"><option value="">最低评分</option>
          <option value="4.5" {"selected" if rating=='4.5' else ""}>4.5+</option>
          <option value="4" {"selected" if rating=='4' else ""}>4.0+</option>
          <option value="3" {"selected" if rating=='3' else ""}>3.0+</option>
        </select>
        <button type="submit" class="inline-flex items-center justify-center rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground shadow hover:bg-primary/90 transition-colors">筛选</button>
      </form>
      <div class="rounded-xl border bg-card shadow-sm overflow-hidden">
        {course_rows if course_rows else '<div class="p-8 text-center text-muted-foreground">暂无数据</div>'}
      </div>
      {paginate(total, page, per_page, '/courses', q=q, dept=dept, credit=credit, rating=rating)}
    </div>
    """
    return render("课程", "courses", content)


def _review_card_course(r):
    sem = r["semester"] or ""
    sem_badge = f'<span class="inline-flex items-center rounded-md bg-secondary px-2 py-0.5 text-xs font-medium text-secondary-foreground">{sem}</span>' if sem else ""
    return (
        f'<article class="border-b px-4 py-3 transition-colors hover:bg-muted/30">'
        f'<div class="space-y-2">'
        f'<div class="flex flex-wrap items-center gap-2">'
        f'{stars_html(r["rating"])}{sem_badge}'
        f'</div>'
        f'<div class="text-xs text-muted-foreground font-mono">{r["created_at"] or ""} &middot; 👍{r["vote_like"] or 0} 👎{r["vote_dislike"] or 0}</div>'
        f'<div class="text-sm leading-relaxed whitespace-pre-wrap">{(r["content"] or "")[:500]}</div>'
        f'</div></article>'
    )


# ============================================================
# 课程详情
# ============================================================
@app.route("/course/<int:cid>")
def course_detail(cid):
    conn = db.get_conn()
    c = conn.execute("SELECT * FROM courses WHERE id=?", (cid,)).fetchone()
    if not c:
        conn.close()
        return render("课程详情", "courses", '<div class="p-8 text-center text-muted-foreground">课程不存在</div>')

    reviews = conn.execute(
        "SELECT * FROM reviews WHERE course_id=? ORDER BY created_at DESC LIMIT 50", (cid,)
    ).fetchall()

    dist = conn.execute(
        "SELECT rating, COUNT(*) as cnt FROM reviews WHERE course_id=? AND rating IS NOT NULL GROUP BY rating ORDER BY rating",
        (cid,)
    ).fetchall()
    dist_labels = json.dumps([str(r["rating"]) for r in dist])
    dist_data = json.dumps([r["cnt"] for r in dist])

    # 相同课程不同老师的对比（按课程代码匹配）
    peer_courses = []
    if c["code"]:
        peer_courses = conn.execute(
            """SELECT id, main_teacher_name, rating_avg, rating_count
               FROM courses WHERE code=? AND rating_count > 0
               ORDER BY rating_avg DESC""",
            (c["code"],)
        ).fetchall()

    # 该课程的学期评分趋势
    sem_trend = conn.execute(
        """SELECT semester, ROUND(AVG(rating), 2) as avg_rating, COUNT(*) as cnt
           FROM reviews WHERE course_id=? AND rating IS NOT NULL AND semester IS NOT NULL
           GROUP BY semester ORDER BY semester""",
        (cid,)
    ).fetchall()

    conn.close()

    info_items = "".join(
        f'<div><div class="text-xs text-muted-foreground">{label}</div>'
        f'<div class="text-sm font-medium mt-0.5">{value}</div></div>'
        for label, value in [
            ("院系", c["department"] or "-"),
            ("教师", c["main_teacher_name"] or "-"),
            ("学分", str(c["credit"])),
            ("语言", c["language"] or "-"),
            ("类别", c["categories"] or "-"),
            ("平均评分", stars_html(round(c["rating_avg"], 2) if c["rating_avg"] else None)),
            ("点评数", str(c["rating_count"] or 0)),
            ("学期", c["last_semester"] or "-"),
        ]
    )

    review_cards = "".join(_review_card_course(r) for r in reviews)

    # 图表数据
    has_peer = len(peer_courses) > 1
    sem_labels = json.dumps([r["semester"] for r in sem_trend])
    sem_data = json.dumps([r["avg_rating"] for r in sem_trend])
    sem_counts = json.dumps([r["cnt"] for r in sem_trend])

    # 教师排行榜
    current_teacher = c["main_teacher_name"] or ""
    peer_rank_html = ""
    if has_peer:
        items = []
        for i, r in enumerate(peer_courses):
            name = r["main_teacher_name"] or "?"
            avg = round(r["rating_avg"], 2) if r["rating_avg"] else 0
            cnt = r["rating_count"] or 0
            is_current = name == current_teacher
            badge = '<span class="ml-1.5 inline-flex items-center rounded bg-primary/10 px-1.5 py-0.5 text-[10px] font-medium text-primary">当前</span>' if is_current else ""
            bar_w = max(8, avg / 5 * 100)
            bar_color = "bg-primary" if is_current else "bg-muted-foreground/30"
            rank_color = "text-primary font-bold" if is_current else "text-muted-foreground"
            items.append(
                f'<div class="flex items-center gap-3 py-2.5 {"bg-primary/5 -mx-4 px-4 rounded-lg" if is_current else ""}">'
                f'<span class="w-5 text-right text-xs {rank_color}">{i+1}</span>'
                f'<div class="flex-1 min-w-0">'
                f'<div class="flex items-center justify-between mb-1">'
                f'<span class="text-sm font-medium truncate">{name}{badge}</span>'
                f'<span class="text-sm font-mono text-muted-foreground ml-2 shrink-0">{avg}</span>'
                f'</div>'
                f'<div class="h-1.5 rounded-full bg-muted overflow-hidden">'
                f'<div class="h-full rounded-full {bar_color} transition-all duration-700" style="width:{bar_w}%"></div>'
                f'</div>'
                f'<div class="text-[11px] text-muted-foreground mt-0.5">{cnt} 条点评</div>'
                f'</div></div>'
            )
        peer_rank_html = "".join(items)

    content = f"""
    <div class="space-y-6">
      <a href="/courses" class="inline-flex items-center text-sm text-muted-foreground hover:text-foreground transition-colors">
        <svg class="mr-1 h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7"/></svg>
        返回课程列表
      </a>

      <div class="rounded-xl border bg-card p-6 shadow-sm">
        <h1 class="text-xl font-bold">{c["name"]} <span class="text-sm font-mono text-muted-foreground">{c["code"]}</span></h1>
        <div class="mt-3 grid grid-cols-2 gap-4 sm:grid-cols-4">{info_items}</div>
      </div>

      <div class="grid gap-6 lg:grid-cols-3">
        <!-- 左侧面板 -->
        <div class="space-y-4 lg:col-span-1">
          <div class="rounded-xl border bg-card shadow-sm overflow-hidden">
            <div class="flex border-b">
              <button onclick="switchCourseTab(0)" class="course-tab flex-1 px-2 py-2.5 text-xs font-medium text-center transition-all duration-300 border-b-2 border-primary text-primary bg-primary/5" data-tab="0">评分分布</button>
              <button onclick="switchCourseTab(1)" class="course-tab flex-1 px-2 py-2.5 text-xs font-medium text-center transition-all duration-300 border-b-2 border-transparent text-muted-foreground hover:text-foreground" data-tab="1">学期趋势</button>
            </div>
            <div class="relative overflow-hidden" style="height:300px">
              <div id="courseChart0" class="course-chart absolute inset-0 p-4 transition-all duration-500 ease-out opacity-100 translate-x-0 flex items-center justify-center">
                <canvas id="distChart"></canvas>
              </div>
              <div id="courseChart1" class="course-chart absolute inset-0 p-4 transition-all duration-500 ease-out opacity-0 translate-x-full">
                <canvas id="semTrendChart"></canvas>
              </div>
            </div>
          </div>
          {"" if not has_peer else f'''
          <div class="rounded-xl border bg-card shadow-sm overflow-hidden">
            <div class="px-4 py-3 border-b"><h2 class="font-semibold text-sm">教师评分排行</h2></div>
            <div class="p-4 space-y-0.5">{peer_rank_html}</div>
          </div>
          '''}
        </div>

        <!-- 右侧内容 -->
        <div class="lg:col-span-2">
          <div class="rounded-xl border bg-card shadow-sm overflow-hidden">
            <div class="px-4 py-3 border-b"><h2 class="font-semibold">点评 (最近50条)</h2></div>
            {review_cards if review_cards else '<div class="p-8 text-center text-muted-foreground">暂无点评</div>'}
          </div>
        </div>
      </div>
    </div>

    <script src="https://cdn.jsdelivr.net/npm/chart.js@4"></script>
    <script>
    const isDark = document.documentElement.classList.contains('dark');
    const txtColor = isDark ? '#a3a3a3' : '#737373';
    const gridColor = isDark ? 'rgba(255,255,255,0.1)' : '#e5e5e5';
    Chart.defaults.color = txtColor;
    Chart.defaults.borderColor = gridColor;

    function switchCourseTab(idx) {{
      document.querySelectorAll('.course-tab').forEach((t, i) => {{
        t.classList.toggle('border-primary', i === idx);
        t.classList.toggle('text-primary', i === idx);
        t.classList.toggle('bg-primary/5', i === idx);
        t.classList.toggle('border-transparent', i !== idx);
        t.classList.toggle('text-muted-foreground', i !== idx);
      }});
      document.querySelectorAll('.course-chart').forEach((c, i) => {{
        if (i === idx) {{
          c.classList.remove('opacity-0', 'translate-x-full', '-translate-x-full');
          c.classList.add('opacity-100', 'translate-x-0');
        }} else {{
          c.classList.remove('opacity-100', 'translate-x-0');
          c.classList.add('opacity-0', i < idx ? '-translate-x-full' : 'translate-x-full');
        }}
      }});
    }}

    new Chart(document.getElementById('distChart'), {{
      type: 'doughnut',
      data: {{ labels: {dist_labels}, datasets: [{{ data: {dist_data}, backgroundColor: ['#ef4444','#f97316','#eab308','#22c55e','#14b8a6'] }}] }},
      options: {{ responsive: true, maintainAspectRatio: false, plugins: {{ legend: {{ position: 'bottom', labels: {{ usePointStyle: true, padding: 10, font: {{ size: 11 }} }} }} }} }}
    }});

    const semCtx = document.getElementById('semTrendChart');
    if (semCtx && {sem_labels}.length > 0) {{
      new Chart(semCtx, {{
        type: 'line',
        data: {{
          labels: {sem_labels},
          datasets: [{{
            label: '平均评分',
            data: {sem_data},
            borderColor: '#0f766e',
            backgroundColor: 'rgba(15,118,110,0.1)',
            fill: true,
            tension: 0.3,
            pointRadius: 4,
            pointHoverRadius: 6
          }}, {{
            label: '点评数',
            data: {sem_counts},
            borderColor: '#737373',
            backgroundColor: 'transparent',
            borderDash: [5, 5],
            tension: 0.3,
            pointRadius: 3,
            yAxisID: 'y1'
          }}]
        }},
        options: {{
          responsive: true,
          maintainAspectRatio: false,
          interaction: {{ mode: 'index', intersect: false }},
          plugins: {{ legend: {{ position: 'bottom', labels: {{ usePointStyle: true, padding: 10, font: {{ size: 11 }} }} }} }},
          scales: {{
            y: {{ beginAtZero: false, min: 1, max: 5, title: {{ display: true, text: '评分' }}, grid: {{ color: gridColor }} }},
            y1: {{ position: 'right', beginAtZero: true, title: {{ display: true, text: '点评数' }}, grid: {{ drawOnChartArea: false }} }},
            x: {{ grid: {{ display: false }} }}
          }}
        }}
      }});
    }}
    </script>
    """
    return render(f"{c['name']} - 课程详情", "courses", content)


# ============================================================
# 点评列表
# ============================================================
@app.route("/reviews")
def reviews():
    q = request.args.get("q", "").strip()
    rating = request.args.get("rating", "").strip()
    semester = request.args.get("semester", "").strip()
    topic = request.args.get("topic", "").strip()
    sort = request.args.get("sort", "newest")
    page = max(1, int(request.args.get("page", 1)))
    per_page = 20
    conn = db.get_conn()

    where = "WHERE 1=1"
    params = []
    if q:
        where += " AND (r.content LIKE ? OR r.course_name LIKE ?)"
        params += [f"%{q}%", f"%{q}%"]
    if rating:
        where += " AND r.rating = ?"
        params.append(int(rating))
    if semester:
        where += " AND r.semester LIKE ?"
        params.append(f"%{semester}%")
    if topic:
        where += " AND r.id IN (SELECT review_id FROM review_tags WHERE tag LIKE ?)"
        params.append(f"%{topic}%")

    order = "r.semester DESC, r.created_at DESC" if sort == "newest" else "r.rating DESC, r.semester DESC" if sort == "rating" else "r.vote_like DESC, r.semester DESC"

    total = conn.execute(f"SELECT COUNT(*) as c FROM reviews r {where}", params).fetchone()["c"]
    rows = conn.execute(
        f"""SELECT r.id, r.course_id, r.course_name, r.semester, r.rating, r.score,
                   r.content, r.vote_like, r.vote_dislike, r.created_at
            FROM reviews r {where}
            ORDER BY {order}
            LIMIT ? OFFSET ?""",
        params + [per_page, (page - 1) * per_page]
    ).fetchall()

    semesters = conn.execute(
        "SELECT DISTINCT semester FROM reviews WHERE semester IS NOT NULL ORDER BY semester DESC LIMIT 20"
    ).fetchall()
    topics = conn.execute(
        "SELECT tag, COUNT(*) as c FROM review_tags GROUP BY tag ORDER BY c DESC"
    ).fetchall()
    conn.close()

    sem_opts = "".join(
        f'<option value="{s["semester"]}" {"selected" if s["semester"]==semester else ""}>{s["semester"]}</option>'
        for s in semesters
    )
    topic_badges = " ".join(
        f'<a href="/reviews?topic={t["tag"]}" class="inline-flex items-center rounded-md border border-border px-2 py-0.5 text-xs font-medium transition-colors hover:bg-accent hover:text-accent-foreground">{t["tag"]} ({t["c"]})</a>'
        for t in topics
    )

    select_cls = ("flex h-9 rounded-md border border-input bg-background px-3 py-1 text-sm shadow-sm "
                  "transition-colors focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring")

    review_cards = "".join(
        f'<article class="border-b px-4 py-3 transition-colors hover:bg-muted/30">'
        f'<div class="space-y-2">'
        f'<div class="flex items-center justify-between">'
        f'<a href="/course/{r["course_id"]}" class="text-sm font-medium text-primary hover:underline">{r["course_name"] or "?"}</a>'
        f'{stars_html(r["rating"])}</div>'
        f'<div class="text-xs text-muted-foreground font-mono">{r["semester"] or ""} &middot; {r["created_at"] or ""} &middot; 👍{r["vote_like"] or 0} 👎{r["vote_dislike"] or 0}</div>'
        f'<div class="text-sm leading-relaxed whitespace-pre-wrap">{(r["content"] or "")[:400]}</div>'
        f'</div></article>'
        for r in rows
    )

    content = f"""
    <div class="space-y-4">
      <div class="flex items-baseline justify-between">
        <h1 class="text-2xl font-bold tracking-tight">点评列表</h1>
        <span class="text-sm text-muted-foreground">{total:,} 条</span>
      </div>
      <form method="get" class="flex flex-wrap gap-2">
        <input type="text" name="q" value="{q}" placeholder="搜索点评内容或课程名..."
               class="flex h-9 flex-1 min-w-[200px] rounded-md border border-input bg-background px-3 py-1 text-sm shadow-sm placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring">
        <select name="rating" class="{select_cls}"><option value="">全部评分</option>
          <option value="5" {"selected" if rating=='5' else ""}>5星</option>
          <option value="4" {"selected" if rating=='4' else ""}>4星</option>
          <option value="3" {"selected" if rating=='3' else ""}>3星</option>
          <option value="2" {"selected" if rating=='2' else ""}>2星</option>
          <option value="1" {"selected" if rating=='1' else ""}>1星</option>
        </select>
        <select name="semester" class="{select_cls}"><option value="">全部学期</option>{sem_opts}</select>
        <input type="text" name="topic" value="{topic}" placeholder="话题关键词"
               class="flex h-9 w-[120px] rounded-md border border-input bg-background px-3 py-1 text-sm shadow-sm placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring">
        <select name="sort" class="{select_cls}">
          <option value="newest" {"selected" if sort=='newest' else ""}>最新</option>
          <option value="rating" {"selected" if sort=='rating' else ""}>评分最高</option>
          <option value="popular" {"selected" if sort=='popular' else ""}>最多点赞</option>
        </select>
        <button type="submit" class="inline-flex items-center justify-center rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground shadow hover:bg-primary/90 transition-colors">筛选</button>
      </form>
      <div class="flex flex-wrap gap-1.5">{topic_badges}</div>
      <div class="rounded-xl border bg-card shadow-sm overflow-hidden">
        {review_cards if review_cards else '<div class="p-8 text-center text-muted-foreground">暂无点评</div>'}
      </div>
      {paginate(total, page, per_page, '/reviews', q=q, rating=rating, semester=semester, topic=topic, sort=sort)}
    </div>
    """
    return render("点评", "reviews", content)


# ============================================================
# API 端点（供油猴脚本调用）
# ============================================================

def _parse_semester_weight(semester_str):
    """计算学期权重：越新的学期权重越高

    学期格式: "2025-2026-1" 或 "2024-2025-2"
    权重计算: 以当前学期为基准，每往前一个学期权重衰减 30%
    """
    import re
    from datetime import datetime

    if not semester_str:
        return 0.5  # 无学期信息，给一个中等权重

    # 解析学期
    match = re.match(r'(\d{4})-(\d{4})-(\d)', semester_str)
    if not match:
        return 0.5

    start_year = int(match.group(1))
    sem_num = int(match.group(3))

    # 计算学期序号（越大越新）
    # 2024-2025-1 = 2024*2 + 0 = 4048
    # 2024-2025-2 = 2024*2 + 1 = 4049
    # 2025-2026-1 = 2025*2 + 0 = 4050
    sem_index = start_year * 2 + (sem_num - 1)

    # 当前学期估算（假设当前是 2025-2026-1）
    now = datetime.now()
    current_sem_index = now.year * 2 + (0 if now.month < 8 else 1)

    # 计算差距
    diff = current_sem_index - sem_index

    # 权重衰减：每往前一个学期，权重 * 0.7
    weight = max(0.1, 0.7 ** diff)

    return round(weight, 3)


@app.route("/api/teacher_rating")
def api_teacher_rating():
    """根据教师名查询评分（加权计算，新学期权重更高）
    names 格式: "教师1,教师2" 或 "教师1|课程代码1,教师2|课程代码2"
    当提供课程代码时，只计算该课程的评分。
    """
    names = request.args.get("names", "")
    if not names:
        return jsonify({"error": "缺少 names 参数"}), 400

    name_list = [n.strip() for n in names.split(",") if n.strip()]
    if not name_list:
        return jsonify({"error": "无有效教师名"}), 400

    conn = db.get_conn()
    result = {}

    for entry in name_list:
        # 解析 "教师名|课程代码" 格式
        parts = entry.split("|")
        name = parts[0].strip()
        course_code = parts[1].strip() if len(parts) > 1 else None

        # 查找结果的 key（包含课程代码以区分）
        result_key = f"{name}|{course_code}" if course_code else name

        # 获取教师基本信息
        teacher = conn.execute(
            "SELECT id, name, department, title FROM teachers WHERE name = ?",
            (name,)
        ).fetchone()

        if not teacher:
            result[result_key] = None
            continue

        teacher_id = teacher["id"]

        # 如果指定了课程代码，找到对应课程 ID
        course_filter = ""
        review_params = [teacher_id]
        if course_code:
            course_row = conn.execute(
                "SELECT id FROM courses WHERE main_teacher_id = ? AND code LIKE ?",
                (teacher_id, f"%{course_code}%")
            ).fetchone()
            if course_row:
                course_filter = " AND c.id = ?"
                review_params.append(course_row["id"])

        # 获取评分（按学期）
        reviews = conn.execute(
            f"""SELECT r.semester, r.rating
               FROM reviews r
               JOIN courses c ON c.id = r.course_id
               WHERE c.main_teacher_id = ? AND r.rating IS NOT NULL
               {course_filter}""",
            review_params
        ).fetchall()

        # 获取课程统计
        course_stats = conn.execute(
            """SELECT COUNT(DISTINCT c.id) as course_count,
                      SUM(c.rating_count) as total_reviews
               FROM courses c WHERE c.main_teacher_id = ?""",
            (teacher_id,)
        ).fetchone()

        if not reviews:
            # 没有评论，尝试用课程表的平均分
            course_avg = conn.execute(
                "SELECT AVG(rating_avg) as avg FROM courses WHERE main_teacher_id = ? AND rating_avg IS NOT NULL",
                (teacher_id,)
            ).fetchone()
            result[result_key] = {
                "id": teacher_id,
                "name": teacher["name"],
                "department": teacher["department"],
                "title": teacher["title"],
                "course_count": course_stats["course_count"] or 0,
                "total_reviews": course_stats["total_reviews"] or 0,
                "avg_rating": round(course_avg["avg"], 1) if course_avg and course_avg["avg"] else None
            }
            continue

        # 加权计算评分
        weighted_sum = 0
        weight_total = 0

        for r in reviews:
            weight = _parse_semester_weight(r["semester"])
            weighted_sum += r["rating"] * weight
            weight_total += weight

        weighted_avg = weighted_sum / weight_total if weight_total > 0 else 0

        result[result_key] = {
            "id": teacher_id,
            "name": teacher["name"],
            "department": teacher["department"],
            "title": teacher["title"],
            "course_count": course_stats["course_count"] or 0,
            "total_reviews": course_stats["total_reviews"] or 0,
            "avg_rating": round(weighted_avg, 1) if weighted_avg else None
        }

    conn.close()
    return jsonify(result)


@app.route("/api/course_rating")
def api_course_rating():
    """根据课程名查询评分"""
    names = request.args.get("names", "")
    if not names:
        return jsonify({"error": "缺少 names 参数"}), 400

    name_list = [n.strip() for n in names.split(",") if n.strip()]
    if not name_list:
        return jsonify({"error": "无有效课程名"}), 400

    conn = db.get_conn()
    result = {}
    for name in name_list:
        rows = conn.execute(
            """SELECT name, code, main_teacher_name, rating_avg, rating_count
               FROM courses WHERE name = ? ORDER BY rating_count DESC""",
            (name,)
        ).fetchall()
        if rows:
            result[name] = [
                {
                    "name": r["name"],
                    "code": r["code"],
                    "teacher": r["main_teacher_name"],
                    "rating_avg": round(r["rating_avg"], 1) if r["rating_avg"] else None,
                    "rating_count": r["rating_count"] or 0
                }
                for r in rows
            ]
        else:
            result[name] = None
    conn.close()
    return jsonify(result)


@app.route("/api/teacher_detail")
def api_teacher_detail():
    """教师详情 — 用于弹出窗口。支持按课程过滤。"""
    name = request.args.get("name", "").strip()
    course_code = request.args.get("course", "").strip()  # 可选：课程代码如 "PHY1265"
    if not name:
        return jsonify({"error": "缺少 name 参数"}), 400

    conn = db.get_conn()
    teacher = conn.execute(
        "SELECT id, name, department, title FROM teachers WHERE name = ?", (name,)
    ).fetchone()

    if not teacher:
        conn.close()
        return jsonify({"error": "未找到教师"}), 404

    tid = teacher["id"]

    # 如果指定了课程代码，找到对应课程 ID
    course_filter = ""
    course_params = [tid]
    if course_code:
        course_row = conn.execute(
            "SELECT id FROM courses WHERE main_teacher_id = ? AND code LIKE ?",
            (tid, f"%{course_code}%")
        ).fetchone()
        if course_row:
            course_filter = " AND c.id = ?"
            course_params.append(course_row["id"])

    # 课程列表
    courses = conn.execute(
        """SELECT name, code, credit, rating_avg, rating_count
           FROM courses WHERE main_teacher_id = ? ORDER BY rating_count DESC""",
        (tid,)
    ).fetchall()

    # 学期评分趋势（如有课程过滤则只看该课程）
    trend = conn.execute(
        f"""SELECT r.semester, ROUND(AVG(r.rating), 2) as avg, COUNT(*) as cnt
           FROM reviews r JOIN courses c ON c.id = r.course_id
           WHERE c.main_teacher_id = ? AND r.rating IS NOT NULL AND r.semester IS NOT NULL
           {course_filter}
           GROUP BY r.semester ORDER BY r.semester""",
        course_params
    ).fetchall()

    # 评分分布
    dist = conn.execute(
        f"""SELECT r.rating, COUNT(*) as cnt
           FROM reviews r JOIN courses c ON c.id = r.course_id
           WHERE c.main_teacher_id = ? AND r.rating IS NOT NULL
           {course_filter}
           GROUP BY r.rating ORDER BY r.rating""",
        course_params
    ).fetchall()

    # 最新几条评论
    review_params = [tid]
    if course_code and course_row:
        review_params.append(course_row["id"])
    recent = conn.execute(
        f"""SELECT r.rating, r.semester, r.content, c.name as course_name
           FROM reviews r JOIN courses c ON c.id = r.course_id
           WHERE c.main_teacher_id = ?
           {course_filter}
           ORDER BY r.created_at DESC LIMIT 3""",
        review_params
    ).fetchall()

    conn.close()

    # 计算加权平均分（从趋势数据）
    weighted_sum = 0
    weight_total = 0
    total_reviews = 0
    for t in trend:
        w = _parse_semester_weight(t["semester"])
        weighted_sum += t["avg"] * t["cnt"] * w
        weight_total += t["cnt"] * w
        total_reviews += t["cnt"]
    weighted_avg = round(weighted_sum / weight_total, 1) if weight_total > 0 else None

    return jsonify({
        "id": tid,
        "name": teacher["name"],
        "department": teacher["department"],
        "title": teacher["title"],
        "weighted_avg": weighted_avg,
        "total_reviews": total_reviews,
        "course_filter": course_code or None,
        "courses": [dict(c) for c in courses],
        "trend": [dict(t) for t in trend],
        "distribution": [dict(d) for d in dist],
        "recent_reviews": [dict(r) for r in recent]
    })


@app.route("/api/course_detail")
def api_course_detail():
    """课程详情 — 用于弹出窗口"""
    code = request.args.get("code", "").strip()
    teacher = request.args.get("teacher", "").strip()

    if not code and not teacher:
        return jsonify({"error": "缺少参数"}), 400

    conn = db.get_conn()

    # 查找课程
    if code:
        course = conn.execute(
            "SELECT id, name, code, credit, department, rating_avg, rating_count FROM courses WHERE code = ?",
            (code,)
        ).fetchone()
    else:
        course = conn.execute(
            "SELECT id, name, code, credit, department, rating_avg, rating_count FROM courses WHERE name LIKE ? LIMIT 1",
            (f"%{teacher}%",)
        ).fetchone()

    if not course:
        conn.close()
        return jsonify({"error": "未找到课程"}), 404

    cid = course["id"]

    # 学期趋势
    trend = conn.execute(
        """SELECT semester, ROUND(AVG(rating), 2) as avg, COUNT(*) as cnt
           FROM reviews WHERE course_id = ? AND rating IS NOT NULL AND semester IS NOT NULL
           GROUP BY semester ORDER BY semester""",
        (cid,)
    ).fetchall()

    # 评分分布
    dist = conn.execute(
        """SELECT rating, COUNT(*) as cnt FROM reviews
           WHERE course_id = ? AND rating IS NOT NULL
           GROUP BY rating ORDER BY rating""",
        (cid,)
    ).fetchall()

    # 同课程不同教师对比
    peers = conn.execute(
        """SELECT main_teacher_name, rating_avg, rating_count
           FROM courses WHERE code = ? AND rating_count > 0
           ORDER BY rating_avg DESC""",
        (course["code"],)
    ).fetchall()

    # 最新评论
    recent = conn.execute(
        """SELECT rating, semester, content FROM reviews
           WHERE course_id = ? ORDER BY created_at DESC LIMIT 3""",
        (cid,)
    ).fetchall()

    conn.close()

    return jsonify({
        "name": course["name"],
        "code": course["code"],
        "credit": course["credit"],
        "department": course["department"],
        "rating_avg": course["rating_avg"],
        "rating_count": course["rating_count"],
        "trend": [dict(t) for t in trend],
        "distribution": [dict(d) for d in dist],
        "peers": [dict(p) for p in peers],
        "recent_reviews": [dict(r) for r in recent]
    })


# ============================================================
# 启动
# ============================================================
if __name__ == "__main__":
    db.init_db()
    print("启动 Web 服务器: http://localhost:8080")
    app.run(host="0.0.0.0", port=8080, debug=False)
