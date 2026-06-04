# SJTU 选课社区评分助手

> 在交大选课网站直接显示教师社区评分，悬停查看详情 — **无需安装任何软件，装个油猴脚本就能用**

## ⭐ 快速使用（3 分钟）

**你只需要做一件事：安装油猴脚本。** 数据已经部署在云端，不需要跑 Python、不需要开本地服务。

### 第一步：安装 Tampermonkey 浏览器扩展

- [Chrome / Edge](https://chromewebstore.google.com/detail/tampermonkey/dhdgffkkebhmkfjojejmpbldmpobfkfo)
- [Firefox](https://addons.mozilla.org/firefox/addon/tampermonkey/)
- [Safari](https://apps.apple.com/app/tampermonkey/id1482490089)

### 第二步：安装油猴脚本

1. 点击浏览器右上角 Tampermonkey 图标 → **添加新脚本**
2. **删除编辑器中的所有默认内容**
3. 打开项目仓库中的 [`sjtu-course-rating.user.js`](sjtu-course-rating.user.js)，复制全部内容粘贴进去
4. 按 `Ctrl+S` 保存

### 第三步：打开选课网站

访问 https://i.sjtu.edu.cn/xsxk/ 登录，教师名后面自动出现评分徽章 ✨

```
┌─────────────────────────────────────────────────────┐
│  课程名称    教师      学分    学期                  │
├─────────────────────────────────────────────────────┤
│  数据结构    张三 ★4.8  4     2025-2026-1           │
│  操作系统    李四 ★4.2  4     2025-2026-1           │
│  高等数学    王五 ★3.9  5     2025-2026-1           │
└─────────────────────────────────────────────────────┘
```

## ✨ 功能特性

### 油猴脚本（核心功能）

- 🎨 **彩色评分徽章** — 颜色随评分变化（绿色 ≥4.5, 青色 ≥4.0, 黄色 ≥3.5, 橙色 ≥3.0, 红色 <3.0）
- 📊 **悬停弹窗** — 鼠标悬停显示评分分布图、学期趋势图、教授课程列表、最新点评
- 📈 **加权评分** — 新学期权重更高，更准确反映教师近期教学水平
- 🔗 **一键跳转** — 点击徽章查看完整详情页
- ⚡ **无需本地服务** — 数据存储在云端，装脚本即用
- 💾 **智能缓存** — 10 分钟缓存，不重复请求

### Web 仪表盘

| 页面 | 功能 |
|---|---|
| **首页** | 数据概览卡片、评分分布柱状图、院系教师数量 TOP 10、热门高分课程 TOP 10 |
| **教师详情** | 评分趋势折线图（按学期 + 点评数双轴）、各课程评分排行 |
| **课程详情** | 评分分布饼图、学期趋势折线图、同课程不同教师对比（当前教师高亮） |
| **点评列表** | 按内容/课程名搜索，支持评分、学期、话题筛选，可按最新/评分/点赞排序 |

### 数据爬取与搜索

- 自动抓取全部教师、课程、点评数据，支持增量/全量更新
- 从点评内容中自动识别"签到""给分""考试""水课"等 30+ 个话题标签
- 命令行按教师、课程、评分、时间、话题、学期等多维度检索

## 🖱️ 快捷操作

| 操作 | 说明 |
|---|---|
| 鼠标悬停徽章 | 弹出教师详情窗口（评分分布、趋势、点评） |
| 点击徽章 | 跳转到 Web 仪表盘的教师详情页 |
| `Ctrl+Shift+R` | 强制刷新所有评分（清除缓存） |
| Tampermonkey 菜单 → ⚙️ 设置 API 地址 | 切换数据源（默认云端，可改回本地） |
| Tampermonkey 菜单 → 🔄 刷新评分 | 清除缓存并重新扫描 |

## 📊 评分计算方式

- **加权平均**：新学期的评分权重更高
- **衰减公式**：每往前一个学期，权重衰减 30%
- **权重公式**：`weight = 0.7 ^ (当前学期序号 - 该学期序号)`

| 学期 | 相对权重 |
|---|---|
| 2025-2026-1 | 100% |
| 2024-2025-2 | 70% |
| 2024-2025-1 | 49% |
| 2023-2024-2 | 34% |
| 2023-2024-1 | 24% |

---

## 🏗️ 架构说明

```
油猴脚本 ──→ Render (API 服务器) ──→ Turso (云端 SQLite)
                  ↑
本地爬虫 ──→ sjtu_course.db ──→ sync_to_turso.py 同步
```

| 组件 | 作用 | 费用 |
|---|---|---|
| **Turso** | 云端 SQLite 数据库存储 | 免费（9GB 存储，10 亿次读/月） |
| **Render** | API 服务器，处理查询请求 | 免费（15 分钟无访问休眠） |
| **Tampermonkey** | 浏览器扩展，注入评分脚本 | 免费 |

## 🔧 维护者指南

> 以下内容仅项目维护者需要关注。普通用户只需安装油猴脚本即可。

### 环境要求

- Python 3.10+
- Git
- [Turso CLI](https://turso.tech)（数据同步用）

### 本地开发

```bash
# 克隆项目
git clone https://github.com/sunalan2025/sjtu-course-community.git
cd sjtu-course-community

# 安装依赖
pip install -r requirements.txt

# 爬取数据（需要 SJTU 账号）
python main.py scrape

# 本地启动 Web 服务
python web_app.py
# 访问 http://localhost:8080

# 命令行搜索
python main.py search -t "教师名"
python main.py search -c "课程名"
python main.py stats
```

### 数据库表结构

| 表名 | 说明 | 主要字段 |
|---|---|---|
| `teachers` | 教师信息 | id, code, name, department, title |
| `courses` | 课程信息 | id, code, name, credit, department, rating_count, rating_avg |
| `reviews` | 点评内容 | id, course_id, semester, rating, content, vote_like, vote_dislike |
| `review_tags` | 话题标签 | review_id, tag（从点评内容正则提取） |
| `scrape_meta` | 爬取元数据 | key, value |

### API 端点

| 端点 | 方法 | 参数 | 说明 |
|---|---|---|---|
| `/api/teacher_rating` | GET | `names=教师1,教师2` | 批量查询教师评分（加权计算） |
| `/api/course_rating` | GET | `names=课程1,课程2` | 批量查询课程评分 |
| `/api/teacher_detail` | GET | `name=教师名&course=课程代码` | 教师详情（弹出窗口用） |
| `/api/course_detail` | GET | `code=课程代码&teacher=教师名` | 课程详情（弹出窗口用） |

### 配置说明

在 `config.py` 中可调整：

| 参数 | 默认值 | 说明 |
|---|---|---|
| `BASE_URL` | `https://course.sjtu.plus/api` | API 地址 |
| `DB_PATH` | `sjtu_course.db` | 本地数据库文件路径 |
| `REQUEST_DELAY` | `0.3` | 请求间隔（秒），避免被封 |
| `MAX_RETRIES` | `3` | 网络请求最大重试次数 |
| `PAGE_SIZE` | `50` | API 分页每页条数 |

---

## 📦 云端部署指南

详细步骤见 [DEPLOYMENT.md](DEPLOYMENT.md)，以下为概要：

### 1. 创建 Turso 数据库（免费）

```bash
# 安装 Turso CLI
winget install tursodatabase.turso  # Windows
# 或 brew install tursodatabase/tap/turso  # macOS

# 登录、建库
turso auth login
turso db create sjtu-course

# 获取连接信息
turso db show sjtu-course --url      # → TURSO_URL
turso db tokens create sjtu-course    # → TURSO_TOKEN
```

### 2. 同步数据到 Turso

```bash
# 设置环境变量
export TURSO_URL="libsql://sjtu-course-xxx.turso.io"
export TURSO_TOKEN="eyJ..."

# 运行同步
python sync_to_turso.py
```

### 3. 部署 API 服务器到 Render（免费）

1. 注册 [render.com](https://render.com)（需绑卡验证 $1，不会重复扣费）
2. New → Web Service → 连接 GitHub 仓库
3. 配置：
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `gunicorn -b 0.0.0.0:$PORT web_app:app`
4. Environment Variables 添加 `TURSO_URL` 和 `TURSO_TOKEN`
5. Deploy

### 4. 更新数据

```bash
# 本地爬取新数据
python main.py scrape

# 同步到 Turso
python sync_to_turso.py

# Render 会自动读取 Turso 新数据，无需重新部署
```

### 5. 更新油猴脚本地址

如果 Render 域名变化，修改 `sjtu-course-rating.user.js` 中的默认 API 地址：

```javascript
const API_BASE = GM_getValue('apiBase', 'https://你的新域名.onrender.com');
```

---

## 📁 项目结构

```
sjtu-course-community/
├── config.py                   # 配置常量（API 地址、DB 路径、请求间隔等）
├── api_client.py               # HTTP 客户端（CSRF 认证、分页、限流、重试）
├── scraper.py                  # 爬虫逻辑（教师→课程→点评，标签提取）
├── database.py                 # 数据库操作（支持本地 SQLite 和云端 Turso）
├── search.py                   # 搜索函数集（按教师/课程/评分/时间/话题/全文等）
├── main.py                     # CLI 入口（scrape / search / stats 子命令）
├── web_app.py                  # Flask Web 应用（仪表盘 + 油猴脚本 API）
├── sjtu-course-rating.user.js  # ⭐ 油猴脚本（在选课网站显示社区评分）
├── sync_to_turso.py            # 数据同步脚本（本地 SQLite → Turso 云端）
├── requirements.txt            # Python 依赖
├── runtime.txt                 # Python 版本（Render 部署用）
├── Procfile                    # Render 启动配置
├── DEPLOYMENT.md               # 云端部署详细指南
├── INSTALL_RATING_PLUGIN.md    # 油猴脚本安装说明
├── CLAUDE.md                   # Claude AI 辅助开发说明
└── sjtu_course.db              # 本地 SQLite 数据库文件（.gitignore 排除）
```

## 📝 常见问题

### Q: 油猴脚本不显示评分？

A: 确认以下几点：
1. Tampermonkey 扩展已安装且脚本已启用（图标上会显示脚本数量）
2. 已经爬取过数据（云端已有数据，通常不需要担心）
3. 浏览器控制台（F12 → Console）没有报错
4. 如果 Render 休眠了，首次加载需要等 30-60 秒唤醒

### Q: Render 休眠了怎么办？

A: Render 免费层 15 分钟无人访问会自动休眠。首次请求会唤醒服务，等待 30-60 秒即可。正常使用时不会休眠。

### Q: 如何切换回本地模式？

A: 在油猴脚本菜单中点 ⚙️ **设置 API 地址**，改为 `http://localhost:8080`，同时本地运行 `python web_app.py`。

### Q: 爬取时提示"登录失败"怎么办？

A: 请确认使用 SJTU 官方邮箱，密码正确，网络可以访问 course.sjtu.plus。

### Q: 如何更新数据？

A:
```bash
python main.py scrape          # 增量爬取
python sync_to_turso.py        # 同步到云端
```
云端会自动读取新数据，用户无需任何操作。

## 🛠️ 技术栈

- **后端**：Python 3.12, requests, Flask, gunicorn
- **数据库**：Turso (云端 SQLite) / SQLite (本地)
- **前端**：Tailwind CSS (CDN), Chart.js (CDN)
- **部署**：Render (API 服务器), Turso (数据库)
- **浏览器扩展**：Tampermonkey 油猴脚本

## 📄 许可证

本项目仅供学习交流使用，请勿用于商业用途。数据来源于 [course.sjtu.plus](https://course.sjtu.plus)，版权归原作者所有。

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

## 📧 联系方式

如有问题或建议，请通过 [GitHub Issues](https://github.com/sunalan2025/sjtu-course-community/issues) 反馈。
