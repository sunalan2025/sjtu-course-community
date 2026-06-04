# SJTU 选课社区数据爬虫与搜索工具

> 从 [course.sjtu.plus](https://course.sjtu.plus) 抓取上海交通大学选课社区的教师、课程、点评数据，存储到本地 SQLite 数据库，并提供命令行搜索、Web 仪表盘浏览，以及**在选课网站直接显示评分徽章**的油猴脚本。

## ✨ 功能特性

### ⭐ 核心功能：选课网站评分助手（油猴脚本）

**本项目最重要的功能** — 安装油猴脚本后，在交大选课网站 (`i.sjtu.edu.cn/xsxk/`) 的教师名后面直接显示社区评分，选课时一眼看出哪些老师教得好。

```
┌─────────────────────────────────────────────────────┐
│  课程名称    教师      学分    学期                  │
├─────────────────────────────────────────────────────┤
│  数据结构    张三 ★4.8  4     2025-2026-1           │
│  操作系统    李四 ★4.2  4     2025-2026-1           │
│  高等数学    王五 ★3.9  5     2025-2026-1           │
└─────────────────────────────────────────────────────┘
```

**功能亮点：**
- 🎨 **彩色评分徽章** — 颜色随评分变化（绿色 ≥4.5, 青色 ≥4.0, 黄色 ≥3.5, 橙色 ≥3.0, 红色 <3.0）
- 📊 **悬停弹窗** — 鼠标悬停显示评分分布图、学期趋势图、教授课程列表、最新点评
- 📈 **加权评分** — 新学期权重更高，更准确反映教师近期教学水平
- 🔗 **一键跳转** — 点击徽章查看完整详情

**快速使用：**
1. 先爬取数据：`python main.py scrape`
2. 启动本地服务：`python web_app.py`（保持运行）
3. 安装油猴脚本：将 `sjtu-course-rating.user.js` 粘贴到 Tampermonkey
4. 打开选课网站：https://i.sjtu.edu.cn/xsxk/

> ⚠️ 使用油猴脚本前**必须先运行 `python web_app.py`**，脚本通过本地 API 查询评分数据。
> 详细安装说明见 [INSTALL_RATING_PLUGIN.md](INSTALL_RATING_PLUGIN.md)

### 数据爬取

- 自动抓取全部教师、课程、点评数据
- 默认增量更新，支持全量覆盖
- 从点评内容中自动识别"签到""给分""考试""水课"等 30+ 个话题标签

### 命令行搜索

- 按教师、课程、评分、时间、话题、学期等多维度检索
- 支持汇总统计（教师课程数、平均评分等）

### Web 仪表盘

| 页面 | 功能 |
|---|---|
| **首页** | 数据概览卡片、评分分布柱状图、院系教师数量 TOP 10、热门高分课程 TOP 10 |
| **教师详情** | 评分趋势折线图（按学期 + 点评数双轴）、各课程评分排行 |
| **课程详情** | 评分分布饼图、学期趋势折线图、同课程不同教师对比（当前教师高亮） |
| **点评列表** | 按内容/课程名搜索，支持评分、学期、话题筛选，可按最新/评分/点赞排序 |

## 📦 安装

### 环境要求

- Python 3.10+
- pip (Python 包管理器)

### 安装步骤

```bash
# 1. 克隆项目
git clone <repo-url>
cd sjtu-course-community-fetch

# 2. 安装依赖
pip install -r requirements.txt
```

### 依赖说明

| 包名 | 版本 | 用途 |
|---|---|---|
| `requests` | ≥2.28.0 | HTTP 请求库，用于调用 API |
| `flask` | ≥3.0.0 | Web 框架，用于仪表盘和本地 API |

## 🚀 使用指南

### 1. 爬取数据

```bash
# 增量爬取（默认，只抓取新数据，跳过已有记录）
python main.py scrape

# 全量爬取（覆盖更新所有数据，用于更新已有记录的变化）
python main.py scrape --full
```

**注意事项：**
- 运行后会提示输入 SJTU 邮箱和密码进行登录认证
- 邮箱可只输入用户名部分（如 `yourname`），会自动补全 `@sjtu.edu.cn`
- 密码输入时不会显示在屏幕上
- 默认请求间隔 0.3 秒，避免被封禁

### 2. 命令行搜索

```bash
# 按教师搜索
python main.py search -t "教师姓名"

# 按课程搜索
python main.py search -c "课程名称"

# 全文搜索点评内容
python main.py search -q "给分好"

# 按评分筛选（5 星点评）
python main.py search -r 5

# 按话题搜索
python main.py search --topic "签到"

# 按学期搜索
python main.py search --semester "2025-2026-1"

# 教师汇总统计
python main.py search -t "教师姓名" -s

# 热门高分课程
python main.py search --top
```

### 3. 查看数据库统计

```bash
python main.py stats
```

### 4. ⭐ 使用油猴脚本（选课评分助手）

这是本项目的核心功能，让评分直接显示在选课网站上。

#### 第一步：启动本地服务

```bash
python web_app.py
```

启动后保持终端窗口运行（最小化即可），这是油猴脚本的数据来源。

#### 第二步：安装油猴脚本

1. 浏览器安装 [Tampermonkey](https://www.tampermonkey.net/) 扩展
2. 点击 Tampermonkey 图标 → 添加新脚本
3. 删除默认内容，粘贴 `sjtu-course-rating.user.js` 的全部内容
4. `Ctrl+S` 保存

#### 第三步：访问选课网站

打开 https://i.sjtu.edu.cn/xsxk/ 登录，评分徽章自动显示。

**日常使用流程：** 每次选课前运行 `python web_app.py` → 打开选课网站 → 看评分选课。

> 详细说明见 [INSTALL_RATING_PLUGIN.md](INSTALL_RATING_PLUGIN.md)

### 5. Web 仪表盘

```bash
python web_app.py
```

浏览器访问 http://localhost:8080，界面风格与 course.sjtu.plus 一致（Tailwind CSS），支持暗色模式切换（右上角图标）。

## 📁 项目结构

```
sjtu-course-community-fetch/
├── config.py                   # 配置常量（API 地址、DB 路径、请求间隔等）
├── api_client.py               # HTTP 客户端（CSRF 认证、分页、限流、重试）
├── scraper.py                  # 爬虫逻辑（教师→课程→点评，标签提取）
├── database.py                 # SQLite 数据库操作（建表、批量 upsert、统计）
├── search.py                   # 搜索函数集（按教师/课程/评分/时间/话题/全文等）
├── main.py                     # CLI 入口（scrape / search / stats 子命令）
├── web_app.py                  # Flask Web 应用（仪表盘 + 油猴脚本 API）
├── sjtu-course-rating.user.js  # ⭐ 油猴脚本（在选课网站显示社区评分）
├── requirements.txt            # Python 依赖
├── .gitignore                  # Git 忽略规则
├── CLAUDE.md                   # Claude AI 辅助开发说明
├── INSTALL_RATING_PLUGIN.md    # 油猴脚本详细安装说明
├── test_rating_plugin.html     # 油猴脚本本地测试页面
└── sjtu_course.db              # SQLite 数据库文件（运行后生成）
```

## 🔌 油猴脚本 API 端点

`web_app.py` 提供以下 API 端点供油猴脚本调用：

| 端点 | 方法 | 参数 | 说明 |
|---|---|---|---|
| `/api/teacher_rating` | GET | `names=教师1,教师2` | 批量查询教师评分（加权计算） |
| `/api/course_rating` | GET | `names=课程1,课程2` | 批量查询课程评分 |
| `/api/teacher_detail` | GET | `name=教师名&course=课程代码` | 教师详情（弹出窗口用） |
| `/api/course_detail` | GET | `code=课程代码&teacher=教师名` | 课程详情（弹出窗口用） |

## 🗄️ 数据库表结构

| 表名 | 说明 | 主要字段 |
|---|---|---|
| `teachers` | 教师信息 | id, code, name, department, title |
| `courses` | 课程信息 | id, code, name, credit, department, rating_count, rating_avg |
| `reviews` | 点评内容 | id, course_id, semester, rating, content, vote_like, vote_dislike |
| `review_tags` | 话题标签 | review_id, tag（从点评内容正则提取） |
| `scrape_meta` | 爬取元数据 | key, value |

## ⚙️ 配置说明

在 `config.py` 中可调整：

| 参数 | 默认值 | 说明 |
|---|---|---|
| `BASE_URL` | `https://course.sjtu.plus/api` | API 地址 |
| `DB_PATH` | `sjtu_course.db` | 数据库文件路径 |
| `REQUEST_DELAY` | `0.3` | 请求间隔（秒），避免被封 |
| `MAX_RETRIES` | `3` | 网络请求最大重试次数 |
| `PAGE_SIZE` | `50` | API 分页每页条数 |

## 📝 常见问题

### Q: 油猴脚本不显示评分？

A: **最常见的原因是没有运行 `python web_app.py`。** 请确认：
1. 终端中 `python web_app.py` 正在运行且没有关闭
2. 浏览器控制台（F12 → Console）没有报错
3. 已经爬取过数据（`python main.py stats` 确认有数据）

### Q: 爬取时提示"登录失败"怎么办？

A: 请确认使用 SJTU 官方邮箱，密码正确，网络可以访问 course.sjtu.plus。

### Q: 如何更新数据？

A: 增量更新 `python main.py scrape`（只抓取新数据），全量更新 `python main.py scrape --full`（覆盖所有数据）。更新后重启 `web_app.py`。

### Q: Web 仪表盘打不开？

A: 确认已安装 Flask（`pip install flask`），端口 8080 未被占用，数据库文件存在。

## 🛠️ 技术栈

- **后端**：Python 3.10+, requests, Flask
- **数据库**：SQLite (WAL 模式)
- **前端**：Tailwind CSS (CDN), Chart.js (CDN)
- **浏览器扩展**：Tampermonkey 油猴脚本

## 📄 许可证

本项目仅供学习交流使用，请勿用于商业用途。数据来源于 [course.sjtu.plus](https://course.sjtu.plus)，版权归原作者所有。

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

## 📧 联系方式

如有问题或建议，请通过 GitHub Issues 反馈。
