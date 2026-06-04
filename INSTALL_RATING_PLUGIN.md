# SJTU 选课社区评分助手 — 安装说明

> 在交大选课网站直接显示教师社区评分。**只需安装油猴脚本，无需 Python、无需本地服务。**

## 快速安装（3 分钟）

### 1. 安装 Tampermonkey 浏览器扩展

| 浏览器 | 安装链接 |
|---|---|
| Chrome / Edge | [Chrome Web Store](https://chromewebstore.google.com/detail/tampermonkey/dhdgffkkebhmkfjojejmpbldmpobfkfo) |
| Firefox | [Firefox Add-ons](https://addons.mozilla.org/firefox/addon/tampermonkey/) |
| Safari | [Mac App Store](https://apps.apple.com/app/tampermonkey/id1482490089) |

安装后浏览器右上角会出现 Tampermonkey 图标。

### 2. 安装油猴脚本

**方法一：从 GitHub 安装（推荐）**

1. 打开 [`sjtu-course-rating.user.js`](sjtu-course-rating.user.js)
2. 点击 Raw 按钮，Tampermonkey 会自动弹出安装确认
3. 点确认安装即可

**方法二：手动粘贴**

1. 点击 Tampermonkey 图标 → **添加新脚本**
2. **删除编辑器中的所有默认内容**
3. 复制 [`sjtu-course-rating.user.js`](sjtu-course-rating.user.js) 的全部内容粘贴进去
4. 按 `Ctrl+S` 保存

### 3. 打开选课网站

访问 https://i.sjtu.edu.cn/xsxk/ 登录，教师名后面自动出现评分徽章。

> 💡 首次加载可能需要等 30-60 秒（云端服务器休眠唤醒），之后会很快。

## 使用方式

### 评分徽章

每个教师名后面会出现一个彩色评分徽章：

| 颜色 | 评分 | 含义 |
|---|---|---|
| 🟢 绿色 | ≥ 4.5 | 非常推荐 |
| 🔵 青色 | ≥ 4.0 | 推荐 |
| 🟡 黄色 | ≥ 3.5 | 一般 |
| 🟠 橙色 | ≥ 3.0 | 谨慎选择 |
| 🔴 红色 | < 3.0 | 不推荐 |

### 悬停查看详情

鼠标悬停在评分徽章上，弹出详情窗口：

- 📊 评分分布柱状图（1-5 星各多少条）
- 📈 学期评分趋势图（哪个学期教得好）
- 📚 教授课程列表（带评分进度条）
- 💬 最新点评摘要（最多 3 条）

### 快捷操作

| 操作 | 说明 |
|---|---|
| 鼠标悬停徽章 | 弹出教师详情窗口 |
| 点击徽章 | 跳转到完整详情页 |
| `Ctrl+Shift+R` | 强制刷新所有评分（清除缓存） |

### 菜单设置

点击 Tampermonkey 图标 → **SJTU 选课社区评分助手**：

- ⚙️ **设置 API 地址** — 默认连接云端，可改为本地地址
- 🔄 **刷新评分** — 清除缓存并重新扫描页面

## 故障排除

### 评分徽章不显示

1. **确认 Tampermonkey 已安装** — 浏览器右上角应有图标
2. **确认脚本已启用** — 点击图标，脚本名旁边应有绿色开关
3. **等待服务器唤醒** — 首次加载需要 30-60 秒（Render 免费层休眠机制）
4. **检查控制台** — 按 `F12` → Console，看是否有红色报错

### 弹窗加载失败

- 可能是服务器正在唤醒，等几秒后鼠标移开再悬停重试
- 按 `Ctrl+Shift+R` 强制刷新

### 页面变卡

- 首次加载需要查询 API，会有短暂延迟
- 后续访问使用 10 分钟缓存，不会重复请求
- 如果仍然很慢，减少页面上显示的课程数量

### 如何卸载

1. 点击 Tampermonkey 图标
2. 找到 "SJTU 选课社区评分助手"
3. 点击垃圾桶图标删除

## 切换数据源

### 云端模式（默认）

脚本默认连接云端 API `https://sjtu-course-community.onrender.com`，无需任何额外操作。

### 本地模式

如果你想用本地数据（比如自己爬取了最新数据）：

1. 本地运行 `python web_app.py`
2. 点击 Tampermonkey 图标 → ⚙️ 设置 API 地址
3. 改为 `http://localhost:8080`
4. 刷新选课页面

## 技术细节

- 油猴脚本通过 `GM_xmlhttpRequest` 调用云端 API
- 使用 `MutationObserver` 监听选课页面的动态加载
- 图表通过 iframe 隔离渲染，避免选课页面污染 `Array.prototype.filter`
- 数据存储在 Turso（云端 SQLite），API 由 Render 托管
- 10 分钟客户端缓存，`Ctrl+Shift+R` 可强制刷新
