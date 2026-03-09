"""
Skills Market Data Scraper
抓取 SkillHub、SkillsMP、GitHub 的公开数据，生成 data.json
"""

import json
import re
import time
import urllib.request
import urllib.error
import urllib.parse
from datetime import datetime, timezone

# ── 工具函数 ────────────────────────────────────────────────

def fetch(url, timeout=15):
    """简单 HTTP GET，返回文本；失败返回 None"""
    try:
        req = urllib.request.Request(url, headers={
            "User-Agent": "Mozilla/5.0 (compatible; SkillsDashboard/1.0)"
        })
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.read().decode("utf-8", errors="replace")
    except Exception as e:
        print(f"  [WARN] fetch {url} failed: {e}")
        return None

def safe_int(s, default=0):
    """从字符串提取第一个整数"""
    m = re.search(r"[\d,]+", str(s))
    if m:
        return int(m.group().replace(",", ""))
    return default

# ── 数据源抓取 ───────────────────────────────────────────────

def scrape_skillhub():
    """
    抓取 skillhub.club 首页，解析公开统计数字
    页面上有: "22.7K Skills · 4.6M Stars"
    """
    print("  Scraping skillhub.club …")
    html = fetch("https://www.skillhub.club")
    result = {"total_skills": None, "total_stars": None}

    if not html:
        return result

    # 匹配 "22.7K Skills" 或 "22,700+ Skills"
    m = re.search(r"([\d,\.]+[KkMm]?)\s*Skills", html)
    if m:
        raw = m.group(1).upper().replace(",", "")
        if "K" in raw:
            result["total_skills"] = int(float(raw.replace("K", "")) * 1000)
        elif "M" in raw:
            result["total_skills"] = int(float(raw.replace("M", "")) * 1_000_000)
        else:
            result["total_skills"] = int(raw)

    # 匹配 "4.6M Stars"
    m2 = re.search(r"([\d,\.]+[KkMm]?)\s*Stars", html)
    if m2:
        raw = m2.group(1).upper().replace(",", "")
        if "M" in raw:
            result["total_stars"] = int(float(raw.replace("M", "")) * 1_000_000)
        elif "K" in raw:
            result["total_stars"] = int(float(raw.replace("K", "")) * 1000)
        else:
            result["total_stars"] = int(raw)

    print(f"    → skills={result['total_skills']}, stars={result['total_stars']}")
    return result


def scrape_skillhub_rankings():
    """
    抓取 skillhub.club/rankings 页面，获取分类和 stars 数据
    """
    print("  Scraping skillhub.club/rankings …")
    html = fetch("https://www.skillhub.club/rankings")
    categories = {}

    if not html:
        return categories

    # 找所有类别标签，格式通常是 <a href="/skills?category=finance">金融服务</a>
    for m in re.finditer(r'category=([\w-]+)[^>]*>([^<]+)<', html):
        slug, label = m.group(1), m.group(2).strip()
        categories[slug] = label

    print(f"    → found {len(categories)} category hints")
    return categories


def scrape_github_anthropics():
    """
    抓取 GitHub anthropics/financial-services-plugins 仓库信息
    使用 GitHub API (无需认证，有速率限制 60次/小时)
    """
    print("  Scraping GitHub anthropics/financial-services-plugins …")
    result = {}

    repos = [
        "anthropics/financial-services-plugins",
        "anthropics/claude-code",
    ]

    for repo in repos:
        url = f"https://api.github.com/repos/{repo}"
        html = fetch(url)
        if not html:
            continue
        try:
            data = json.loads(html)
            result[repo] = {
                "stars":    data.get("stargazers_count", 0),
                "forks":    data.get("forks_count", 0),
                "updated":  data.get("updated_at", ""),
                "watchers": data.get("watchers_count", 0),
            }
            print(f"    → {repo}: ⭐{result[repo]['stars']}")
        except Exception as e:
            print(f"    [WARN] parse {repo} failed: {e}")
        time.sleep(0.5)   # 避免触发速率限制

    return result


def scrape_github_community_skills():
    """
    搜索 GitHub 上标记了 claude-skills / claude-code-skill 主题的仓库数量
    GitHub Search API 返回 total_count
    """
    print("  Scraping GitHub skill repos count …")
    result = {}

    queries = {
        "claude_skills":   "topic:claude-skills",
        "claude_code_skill": "topic:claude-code-skill",
        "skill_md":        "filename:SKILL.md",
    }

    for key, q in queries.items():
        try:
            url = f"https://api.github.com/search/repositories?q={urllib.parse.quote(q)}&per_page=1"
            html = fetch(url)
            if html:
                data = json.loads(html)
                result[key] = data.get("total_count", 0)
                print(f"    → {key}: {result[key]}")
        except Exception as e:
            print(f"    [WARN] {key}: {e}")
        time.sleep(1.0)

    return result


def scrape_skillsmp():
    """
    抓取 skillsmp.com，解析页面上的统计数字
    """
    print("  Scraping skillsmp.com …")
    html = fetch("https://skillsmp.com")
    result = {"total": None}

    if not html:
        return result

    m = re.search(r"([\d,\.]+[KkMm]?)\+?\s*[Ss]kills?", html)
    if m:
        raw = m.group(1).upper().replace(",", "")
        if "K" in raw:
            result["total"] = int(float(raw.replace("K", "")) * 1000)
        else:
            result["total"] = int(raw)

    print(f"    → total={result['total']}")
    return result


# ── 历史数据追加 ─────────────────────────────────────────────

def load_existing(path="data.json"):
    try:
        with open(path) as f:
            return json.load(f)
    except Exception:
        return {}


def append_history(existing, today_str, total_skills):
    """把今天的总量追加进历史序列，最多保留 180 天"""
    history = existing.get("history", [])

    # 去掉今天已有的记录（避免重复）
    history = [h for h in history if h["date"] != today_str]

    if total_skills:
        history.append({"date": today_str, "total": total_skills})

    # 只保留最近 180 条
    history = sorted(history, key=lambda x: x["date"])[-180:]
    return history


# ── 主流程 ───────────────────────────────────────────────────

def main():

    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    print(f"\n=== Skills Scraper — {today} ===\n")

    existing = load_existing("data.json")

    # 1. 抓取各数据源
    skillhub    = scrape_skillhub()
    github_repos = scrape_github_anthropics()
    github_skill_count = scrape_github_community_skills()
    skillsmp    = scrape_skillsmp()

    # 2. 计算综合总量（SkillHub 为主，其余补充）
    total_skills = skillhub.get("total_skills") or existing.get("summary", {}).get("total_skills", 22700)

    # 3. 追加历史
    history = append_history(existing, today, total_skills)

    # 4. 计算月增量（对比上月同期）
    monthly_delta = None
    if len(history) >= 30:
        prev = history[-30]["total"]
        monthly_delta = total_skills - prev

    # 5. 构建输出
    output = {
        "meta": {
            "updated_at":  datetime.now(timezone.utc).isoformat(),
            "updated_date": today,
            "sources": ["skillhub.club", "skillsmp.com", "api.github.com"],
        },
        "summary": {
            "total_skills":   total_skills,
            "total_stars":    skillhub.get("total_stars"),
            "monthly_delta":  monthly_delta,
        },
        "github": {
            "repos":         github_repos,
            "skill_md_count": github_skill_count.get("skill_md"),
            "topic_claude_skills": github_skill_count.get("claude_skills"),
        },
        "skillsmp": skillsmp,

        # 历史时序（供折线图使用）
        "history": history,

        # 以下为静态参考数据，每季度人工核对一次
        # （爬虫无法自动获取行业细分，这些基于公开报道估算）
        "categories": existing.get("categories", [
            {"name":"💻 开发工具","count":8400,"growth6m":38,"color":"#58a6ff"},
            {"name":"🤖 AI/ML",   "count":2100,"growth6m":95,"color":"#3fb950"},
            {"name":"📊 金融服务","count":1850,"growth6m":420,"color":"#e3b341"},
            {"name":"📝 内容创作","count":1600,"growth6m":52,"color":"#4ecdc4"},
            {"name":"📈 数据分析","count":1400,"growth6m":88,"color":"#a371f7"},
            {"name":"⚙️ DevOps",  "count":1200,"growth6m":41,"color":"#f0883e"},
            {"name":"⚖️ 法律服务","count":680, "growth6m":310,"color":"#f778ba"},
            {"name":"🏥 医疗健康","count":520, "growth6m":180,"color":"#22d3ee"},
            {"name":"📦 产品管理","count":480, "growth6m":260,"color":"#84cc16"},
            {"name":"🎨 设计创意","count":420, "growth6m":75,"color":"#f59e0b"},
            {"name":"🔒 网络安全","count":380, "growth6m":110,"color":"#fb7185"},
            {"name":"🎓 教育学习","count":370, "growth6m":60,"color":"#c084fc"},
        ]),
        "agents": existing.get("agents", [
            {"name":"Claude",   "count":18500,"growth6m":95, "color":"#f0883e"},
            {"name":"Cursor",   "count":14200,"growth6m":82, "color":"#58a6ff"},
            {"name":"OpenClaw", "count":8600, "growth6m":680,"color":"#3fb950"},
            {"name":"OpenCode", "count":7800, "growth6m":120,"color":"#8b949e"},
            {"name":"Windsurf", "count":7200, "growth6m":95, "color":"#39d3c3"},
            {"name":"Cline",    "count":6400, "growth6m":65, "color":"#a371f7"},
            {"name":"Roo Code", "count":5800, "growth6m":75, "color":"#f778ba"},
            {"name":"Augment",  "count":4200, "growth6m":140,"color":"#e3b341"},
            {"name":"Aide",     "count":3100, "growth6m":90, "color":"#22d3ee"},
        ]),
    }

    with open("data.json", "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"\n✅ data.json written — total_skills={total_skills}, history={len(history)} days")


if __name__ == "__main__":
    main()
