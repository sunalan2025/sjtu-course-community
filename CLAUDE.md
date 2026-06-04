# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

SJTU 选课社区数据爬虫与搜索工具 — 从 [course.sjtu.plus](https://course.sjtu.plus) 抓取上海交通大学选课社区的教师、课程、点评数据，存储到本地 SQLite 数据库，并提供命令行搜索和 Web 仪表盘浏览功能。

### 核心特性

- **数据爬取**：支持增量/全量两种模式，自动处理分页、限流、重试
- **标签提取**：从点评内容中自动识别 30+ 个话题标签（签到、给分、水课等）
- **命令行搜索**：按教师、课程、评分、时间、话题、学期等多维度检索
- **Web 仪表盘**：Tailwind CSS + Chart.js，支持暗色模式，可视化图表
- **浏览器扩展**：油猴脚本，在选课网站直接显示社区评分

## Commands

```bash
# Install dependencies
pip install -r requirements.txt

# Scrape data (interactive — prompts for SJTU email/password)
python main.py scrape              # incremental (skip existing records)
python main.py scrape --full       # full scrape (overwrite all data)

# CLI search
python main.py search -t "教师名"          # by teacher
python main.py search -c "课程名"          # by course
python main.py search -q "关键词"          # full-text search
python main.py search -r 5                 # by rating (1-5 stars)
python main.py search --topic "签到"       # by tag/topic
python main.py search --semester "2025-2026-1"  # by semester
python main.py search --top                # top-rated courses
python main.py search -t "教师名" -s       # teacher summary stats
python main.py search -c "课程名" -s       # course summary stats

# Database stats
python main.py stats

# Web dashboard (http://localhost:8080, Tailwind CSS, dark mode)
python web_app.py
```

## Architecture

```
├── config.py                   # 配置常量：API 地址、DB 路径、请求间隔、重试设置
├── api_client.py               # HTTP 客户端：CSRF 认证、会话管理、分页、限流 (0.3s)、重试退避
├── scraper.py                  # 爬虫逻辑：教师→课程→点评，增量/全量模式，标签提取
├── database.py                 # SQLite 操作：WAL 模式、外键、批量 upsert (500)、元数据存储
├── search.py                   # 搜索函数集：返回 list[dict]，支持多维度查询
├── main.py                     # CLI 入口：argparse 子命令 (scrape/search/stats)
├── web_app.py                  # Flask Web 应用：Tailwind CSS + Chart.js，暗色模式
├── sjtu-course-rating.user.js  # 油猴脚本：在选课网站显示社区评分
├── requirements.txt            # Python 依赖：requests>=2.28.0, flask>=3.0.0
└── .gitignore                  # 忽略：*.db, __pycache__/, *.pyc, .env, IDE 目录
```

## Key Patterns

- **数据存储**：API 响应存储为 `raw_json`（字符串化的 dict）alongside 解析后的列
- **标签提取**：爬取后通过正则匹配完成，存储在 `review_tags` 关联表
- **Web 模板**：使用 `render_template_string` + Tailwind CSS CDN，CSS 自定义属性定义颜色令牌
- **数据库连接**：短生命周期（每次查询打开、查询、关闭）
- **排序策略**：课程和点评默认按学期降序（最新在前）
- **批量操作**：INSERT OR REPLACE，批次大小 500

## Web Dashboard Layout

Detail pages use a 1/3 + 2/3 grid: left column has charts (sticky) and ranked lists, right column has review content.

- **Home** (`/`): stat cards, rating distribution bar chart, department teacher count top 10 bar chart, hot courses top 10
- **Teacher detail** (`/teacher/<id>`): rating trend line chart (avg per semester + review count dual-axis) + course rating ranked list (progress bars, sorted high to low)
- **Course detail** (`/course/<id>`): tabbed chart panel (rating distribution doughnut / semester trend line, animated slide transition) + teacher rating ranked list (current teacher highlighted, progress bars, shown only when multiple teachers share the same course code)
- All charts use Chart.js, auto-adapt to dark/light theme, `maintainAspectRatio: false` for fixed container sizing

## Browser Extension (Tampermonkey Script) — 核心功能

`sjtu-course-rating.user.js` — 油猴脚本，在交大选课网站 (`i.sjtu.edu.cn/xsxk/`) 直接显示教师和课程的社区评分。

### 使用前提

**必须先运行 `python web_app.py`**，油猴脚本通过本地 API（`localhost:8080`）查询评分数据。详细安装和使用说明见 `INSTALL_RATING_PLUGIN.md`。

### API Endpoints

- `GET /api/teacher_rating?names=教师1,教师2` — 批量查询教师评分（支持加权计算）
- `GET /api/course_rating?names=课程1,课程2` — 批量查询课程评分
- `GET /api/teacher_detail?name=教师名&course=课程代码` — 教师详情（用于弹出窗口）
- `GET /api/course_detail?code=课程代码&teacher=教师名` — 课程详情（用于弹出窗口）

### Features

- 自动检测页面中的教师和课程列（通过表头识别）
- 评分徽章颜色根据分值变化（绿色 ≥4.5, 青色 ≥4.0, 黄色 ≥3.5, 橙色 ≥3.0, 红色 <3.0）
- 鼠标悬停弹出详情窗口（评分分布图、学期趋势图、课程列表、最新点评）
- 点击徽章跳转到本地详情页
- 10分钟缓存，支持 `Ctrl+Shift+R` 强制刷新
- 菜单设置 API 地址（默认 `http://localhost:8080`）

### Testing

- `test_rating_plugin.html` — 本地测试页面，用于调试脚本
- 详细安装说明见 `INSTALL_RATING_PLUGIN.md`

## Development Guidelines

### 代码风格

- Python 3.10+ 语法，使用类型提示
- 函数和变量使用 snake_case
- 类名使用 PascalCase
- 常量使用 UPPER_SNAKE_CASE

### 数据库操作

- 所有数据库连接使用 `with` 语句或手动 close
- 批量操作使用 `executemany`，批次大小 500
- 使用 `INSERT OR REPLACE` 进行 upsert
- 启用 WAL 模式和外键约束

### API 调用

- 遵守请求间隔（默认 0.3 秒）
- 处理 HTTP 429（Too Many Requests）自动重试
- 使用 CSRF token 进行认证
- 分页处理，每页 50 条

### Web 开发

- 使用 `render_template_string` 而非模板文件
- Tailwind CSS 和 Chart.js 使用 CDN
- 支持暗色模式（CSS 自定义属性）
- 响应式设计，移动端适配

### 测试

- 油猴脚本测试页面：`test_rating_plugin.html`
- 手动测试 Web 仪表盘：`python web_app.py` 后访问 http://localhost:8080

## Common Tasks

### 添加新的搜索维度

1. 在 `search.py` 中添加新的查询函数
2. 在 `main.py` 的 `cmd_search` 中添加参数处理
3. 在 argparse 中添加命令行参数

### 添加新的图表

1. 在 `web_app.py` 中找到对应的路由函数
2. 在 HTML 模板中添加 canvas 元素
3. 添加 Chart.js 配置和数据

### 修改标签关键词

1. 在 `scraper.py` 中找到 `TAG_KEYWORDS` 列表
2. 添加或删除关键词
3. 重新爬取数据以更新标签

## Environment Variables

项目不使用环境变量，所有配置在 `config.py` 中硬编码。如需修改配置，直接编辑 `config.py`。

## Database Schema

```sql
-- 教师表
CREATE TABLE teachers (
    id INTEGER PRIMARY KEY,
    code TEXT UNIQUE,
    name TEXT,
    department TEXT,
    title TEXT,
    raw_json TEXT
);

-- 课程表
CREATE TABLE courses (
    id INTEGER PRIMARY KEY,
    code TEXT UNIQUE,
    name TEXT,
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

-- 点评表
CREATE TABLE reviews (
    id INTEGER PRIMARY KEY,
    course_id INTEGER,
    course_name TEXT,
    semester TEXT,
    score REAL,
    rating INTEGER,
    content TEXT,
    moderator_remark TEXT,
    vote_like INTEGER,
    vote_dislike INTEGER,
    created_at TEXT,
    updated_at TEXT,
    raw_json TEXT,
    FOREIGN KEY (course_id) REFERENCES courses(id)
);

-- 标签关联表
CREATE TABLE review_tags (
    review_id INTEGER,
    tag TEXT,
    PRIMARY KEY (review_id, tag),
    FOREIGN KEY (review_id) REFERENCES reviews(id)
);

-- 元数据表
CREATE TABLE scrape_meta (
    key TEXT PRIMARY KEY,
    value TEXT
);
```
