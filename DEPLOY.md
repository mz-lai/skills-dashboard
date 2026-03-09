# 部署到 GitHub 步骤

本地已做好：`git init`、首次提交已完成。按下面步骤即可推到 GitHub 并开启 Pages。

---

## 1. 在 GitHub 上新建仓库

1. 打开：**https://github.com/new**
2. **Repository name** 填：`skills-dashboard`（或你喜欢的名字）
3. 选 **Public**，**不要**勾选 “Add a README”
4. 点 **Create repository**

---

## 2. 添加远程并推送

在终端执行（把 `你的用户名` 换成你的 GitHub 用户名）：

```bash
cd /Users/laimingzhe/Downloads/files

git remote add origin https://github.com/你的用户名/skills-dashboard.git
git branch -M main
git push -u origin main
```

若使用 SSH：

```bash
git remote add origin git@github.com:你的用户名/skills-dashboard.git
git push -u origin main
```

推送时按提示登录 GitHub（或使用已配置的 token/SSH）。

---

## 3. 开启 GitHub Pages

1. 仓库页 → **Settings** → 左侧 **Pages**
2. **Source** 选 **GitHub Actions**
3. 保存

---

## 4. 给 Actions 写权限

1. 仓库 → **Settings** → **Actions** → **General**
2. 找到 **Workflow permissions**
3. 选 **Read and write permissions**
4. 可选：勾选 “Allow GitHub Actions to create and approve pull requests”
5. 点 **Save**

---

## 5. 手动跑一次工作流

1. 仓库 → **Actions** → **Daily Skills Data Update**
2. 点 **Run workflow** → **Run workflow**
3. 等约 1 分钟，跑完后会生成/更新 `data.json` 并部署

---

## 6. 访问看板

打开：

```
https://你的用户名.github.io/skills-dashboard/
```

（若仓库名不是 `skills-dashboard`，把 URL 里的仓库名改成你的即可。）

之后每天北京时间 08:00 会自动更新数据并部署。
