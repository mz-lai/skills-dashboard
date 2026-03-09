# Skills Market Dashboard

每日自动抓取 SkillHub、SkillsMP、GitHub 数据，部署到 GitHub Pages。

## 快速上手（5步）

### 第1步：Fork 或创建仓库

把这个项目推到你的 GitHub 仓库，比如命名为 `skills-dashboard`。

```bash
git init
git add .
git commit -m "init"
git remote add origin https://github.com/你的用户名/skills-dashboard.git
git push -u origin main
```

### 第2步：开启 GitHub Pages

1. 进入仓库 → **Settings** → **Pages**
2. Source 选 **GitHub Actions**
3. 保存

### 第3步：给 Actions 授权写入

1. 进入仓库 → **Settings** → **Actions** → **General**
2. 滚到 "Workflow permissions"
3. 选 **Read and write permissions**
4. 勾选 "Allow GitHub Actions to create and approve pull requests"
5. 保存

### 第4步：手动触发第一次运行

1. 进入仓库 → **Actions** → **Daily Skills Data Update**
2. 点击 **Run workflow** → **Run workflow**
3. 等待约 1 分钟

运行完成后，仓库根目录会出现 `data.json`，Pages 会自动部署。

### 第5步：访问页面

```
https://你的用户名.github.io/skills-dashboard/
```

---

## 文件结构

```
skills-dashboard/
├── index.html                    # 看板页面（读取 data.json）
├── data.json                     # 自动生成，每天更新
├── scripts/
│   └── scraper.py                # 数据抓取脚本（纯标准库，无需安装依赖）
└── .github/
    └── workflows/
        └── daily-update.yml     # 定时任务（每天 08:00 CST）
```

---

## 数据说明

| 字段 | 来源 | 更新频率 |
|------|------|----------|
| `total_skills` | skillhub.club 首页 | 每日 |
| `total_stars` | skillhub.club 首页 | 每日 |
| `history[]` | 每日抓取累积 | 每日追加 |
| `github.repos` | GitHub API | 每日 |
| `categories[]` | 内置估算值 | 每季度手动核对 |
| `agents[]` | 内置估算值 | 每季度手动核对 |

> **注意**：行业细分（categories）和智能体分布（agents）数据目前没有公开 API，
> 为基于公开报道的估算值。`total_skills` 和历史趋势是真实抓取的。

---

## 手动更新行业/智能体数据

打开 `data.json`，修改 `categories` 或 `agents` 数组，提交 push 即可：

```json
{
  "categories": [
    {"name": "📊 金融服务", "count": 2100, "growth6m": 450, "color": "#e3b341"},
    ...
  ]
}
```

---

## 修改抓取时间

编辑 `.github/workflows/daily-update.yml`：

```yaml
schedule:
  - cron: "0 0 * * *"   # UTC 00:00 = 北京时间 08:00
  # 改成 UTC 01:00（北京 09:00）:
  # - cron: "0 1 * * *"
```

---

## 本地调试

```bash
# 在项目根目录运行爬虫（会生成根目录的 data.json）
python3 scripts/scraper.py

# 本地预览（需要从服务器访问才能读到 data.json）
python3 -m http.server 8080
# 打开 http://localhost:8080
```
