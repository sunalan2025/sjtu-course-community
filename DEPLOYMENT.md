# 云端部署详细指南

> 本文档详细说明如何部署和维护 SJTU 选课社区评分助手的云端服务。

## 架构总览

```
油猴脚本 ──→ Render (免费 API 服务器) ──→ Turso (免费云端数据库)
                  ↑
本地电脑 ──→ sjtu_course.db ──→ sync_to_turso.py ──→ Turso
   (爬虫)                        (手动同步)
```

| 组件 | 作用 | 费用 | 限制 |
|---|---|---|---|
| **Turso** | 存储所有数据（教师、课程、点评） | 免费 | 9GB 存储，10 亿次读/月 |
| **Render** | 运行 Flask API，处理查询请求 | 免费 | 15 分钟无访问休眠，绑卡验证 $1 |
| **GitHub** | 存放代码，自动触发部署 | 免费 | 公开仓库 |

---

## 一、Turso 数据库

> **所有操作都可以在网页端完成，不需要安装任何 CLI 工具。**

### 1.1 创建数据库

1. 访问 https://turso.tech → 点 **Sign Up** → 用 **GitHub** 登录
2. 进入 Dashboard → 点 **Create Database**
3. 填写：
   - **Database Name**: `sjtu-course`
   - **Group**: `default`
   - **Location**: 选 **香港 (HKG)**（离国内最近）
4. 点 **Create** → 创建完成自动进入数据库详情页

### 1.2 获取连接信息

在数据库详情页：

1. 复制页面上的 **Database URL**
   - 格式类似：`libsql://sjtu-course-你的用户名.turso.io`
   - 后面同步数据和部署 Render 都要用
2. 点页面上的 **Create Token** 按钮
   - 复制生成的 Token（类似 `eyJhbGciOi...`）
   - 这是数据库的认证密钥，**不要泄露给别人**

**把 URL 和 Token 保存好**，后面要用好几次。

### 1.3 查看数据

在数据库详情页，点 **Console** 标签，可以直接执行 SQL：

```sql
-- 查看数据量
SELECT COUNT(*) FROM teachers;    -- 教师数
SELECT COUNT(*) FROM courses;     -- 课程数
SELECT COUNT(*) FROM reviews;     -- 点评数
SELECT COUNT(*) FROM review_tags; -- 标签数

-- 查看最新点评
SELECT course_name, semester, rating, content
FROM reviews ORDER BY created_at DESC LIMIT 5;

-- 按教师搜索
SELECT name, department FROM teachers WHERE name LIKE '%张%';
```

### 1.4 数据同步

本地爬取新数据后，同步到 Turso：

```bash
# 方式一：设置环境变量后运行（推荐）

# Windows PowerShell:
$env:TURSO_URL="libsql://sjtu-course-xxx.turso.io"
$env:TURSO_TOKEN="eyJ..."
python sync_to_turso.py

# macOS/Linux:
export TURSO_URL="libsql://sjtu-course-xxx.turso.io"
export TURSO_TOKEN="eyJ..."
python sync_to_turso.py

# 方式二：直接编辑 sync_to_turso.py 填入 URL 和 Token（不要提交到 Git）
```

同步脚本使用 `INSERT OR REPLACE`，已存在的记录会更新，新记录会插入。可以反复运行，不会产生重复数据。

### 1.5 Token 管理（网页端）

| 操作 | 步骤 |
|---|---|
| **创建新 Token** | 数据库详情页 → 点 **Create Token** |
| **查看所有 Token** | 数据库详情页 → **Tokens** 标签 |
| **吊销 Token** | 数据库详情页 → **Tokens** → 找到要吊销的 → 点删除 |

> 如果 Token 泄露了，立即吊销旧的并创建新的，然后去 Render 更新环境变量。

### 1.6 删除数据库（慎用）

数据库详情页 → **Settings** → **Dangerous Zone** → **Destroy Database**

> ⚠️ 数据不可恢复！操作前请确认。

---

## 二、Render API 服务器

### 2.1 注册并绑定

1. 访问 https://render.com → **Get Started** → **GitHub** 登录
2. 首次使用需要绑定信用卡验证（$1 一次性费用，不会重复扣费）
3. 选择 **Free** 计划

### 2.2 创建 Web Service

1. Dashboard → **New** → **Web Service**
2. 连接 GitHub → 选择 `sunalan2025/sjtu-course-community` 仓库
3. 配置以下信息：

| 字段 | 值 |
|---|---|
| **Name** | `sjtu-course`（或自定义） |
| **Region** | Singapore（或离你近的） |
| **Runtime** | Python 3 |
| **Build Command** | `pip install -r requirements.txt` |
| **Start Command** | `gunicorn -b 0.0.0.0:$PORT web_app:app` |
| **Instance Type** | Free |

### 2.3 添加环境变量

在页面下方 **Environment Variables** 部分，添加：

| Key | Value |
|---|---|
| `TURSO_URL` | `https://sjtu-course-xxx.turso.io`（你的 Turso URL，注意是 https 不是 libsql） |
| `TURSO_TOKEN` | `eyJ...`（你的 Turso Token） |

> ⚠️ Turso URL 需要用 `https://` 格式，不是 `libsql://`。把 `libsql://` 改成 `https://` 即可。

### 2.4 部署

点击 **Create Web Service**，等待 2-3 分钟构建完成。

部署成功后页面顶部会显示域名：`https://xxx.onrender.com`

### 2.5 查看日志

如果部署失败或运行报错：

1. 进入服务页面
2. 点击 **Logs** 标签
3. 查看错误信息

常见问题：
- **Python 版本不兼容**：确保 `runtime.txt` 存在且内容为 `python-3.12.3`
- **环境变量未设置**：检查 `TURSO_URL` 和 `TURSO_TOKEN` 是否正确
- **依赖安装失败**：检查 `requirements.txt` 是否完整

### 2.6 重新部署

代码更新后，Render 会自动从 GitHub 拉取最新代码并重新部署。

也可以手动触发：
1. 进入服务页面
2. 点击 **Manual Deploy** → **Deploy latest commit**

### 2.7 更新环境变量

如果 Turso Token 更换了：
1. 进入服务页面 → **Environment**
2. 修改 `TURSO_TOKEN` 的值
3. 点击 **Save Changes**
4. Render 会自动重新部署

### 2.8 休眠机制

Render 免费层的休眠规则：

| 状态 | 说明 |
|---|---|
| **活跃** | 有人访问时运行，响应速度正常 |
| **休眠** | 15 分钟无人访问后自动休眠 |
| **唤醒** | 首次请求触发唤醒，需要 30-60 秒 |

**影响：** 如果很长时间没人用过脚本，第一次打开选课网站会等半分钟左右。之后正常使用没有延迟。

---

## 三、日常维护流程

### 3.1 更新数据（推荐每月一次）

```bash
# 1. 本地爬取最新数据
python main.py scrape

# 2. 同步到 Turso 云端
python sync_to_turso.py

# 3. 用户端自动生效，无需任何操作
```

### 3.2 全量重新爬取

如果需要更新已有记录的变化（比如新的评分）：

```bash
python main.py scrape --full    # 覆盖所有数据
python sync_to_turso.py         # 同步到云端
```

### 3.3 更新代码后部署

```bash
# 1. 修改代码
# 2. 提交并推送到 GitHub
git add -A
git commit -m "描述你的改动"
git push origin master

# 3. Render 自动检测到 GitHub 更新，自动重新部署（2-3 分钟）
```

### 3.4 更新油猴脚本

如果修改了 `sjtu-course-rating.user.js`：

1. 用户需要在 Tampermonkey 中更新脚本（重新粘贴或从 GitHub 安装）
2. 或者发布到 [Greasy Fork](https://greasyfork.org) 方便用户自动更新

---

## 四、故障排查

### Turso 连接失败

1. 打开 https://turso.tech → 进入数据库详情页
2. 点 **Console** 标签，执行 `SELECT 1;` 测试连接
3. 如果 Token 过期，去 **Tokens** 标签创建新的，然后更新 Render 环境变量

### Render 部署失败

1. 检查 **Logs** 页面的错误信息
2. 确认 `runtime.txt` 内容为 `python-3.12.3`
3. 确认环境变量 `TURSO_URL` 和 `TURSO_TOKEN` 已设置
4. 尝试 **Manual Deploy** → **Deploy latest commit**

### API 返回 500 错误

1. 查看 Render **Logs** 页面
2. 最常见原因：Turso Token 过期或 URL 格式错误
3. 确认 URL 用的是 `https://` 不是 `libsql://`

### 油猴脚本不显示评分

1. 确认 Render 服务正在运行（Dashboard 显示绿色）
2. 如果 Render 休眠了，等 30-60 秒
3. 按 `Ctrl+Shift+R` 强制刷新
4. 在油猴脚本菜单中检查 API 地址是否正确

### 数据不同步

1. 打开 https://turso.tech → 进入数据库详情页 → **Console**
2. 执行 `SELECT COUNT(*) FROM reviews;` 查看云端数据量
3. 本地运行 `python main.py stats` 对比
4. 如果不一致，重新运行 `python sync_to_turso.py`

---

## 五、费用说明

| 项目 | 费用 | 说明 |
|---|---|---|
| Turso 免费层 | $0 | 9GB 存储，10 亿次读/月，500M 写入行/月 |
| Render 免费层 | $0 | 750 小时/月，15 分钟休眠 |
| Render 绑卡验证 | $1（一次性） | 只在首次绑定时扣一次 |
| GitHub 公开仓库 | $0 | 免费 |

**总计：一次性 $1，之后永久免费。**

只要不超过免费额度，不会产生任何额外费用。当前数据量（5000+ 教师、14000+ 课程、50000+ 点评）远远在免费额度内。

---

## 六、安全注意事项

- **Turso Token** 等同于数据库密码，不要泄露到公开仓库
- `sync_to_turso.py` 中的 Token 通过环境变量读取，不要硬编码
- 如果 Token 泄露，立即在 Turso 网页端吊销旧 Token 并创建新的
- Render 环境变量是加密存储的，不会暴露给前端
- 油猴脚本只调用只读 API，不会修改数据
