"""Gera assets/stats.svg com dados públicos do GitHub (roda no GitHub Actions)."""
import json
import os
import urllib.request

USER = os.environ.get("GH_USER", "YagoXavier10")
TOKEN = os.environ.get("GITHUB_TOKEN", "")
COLORS = {
    "JavaScript": "#f1e05a", "HTML": "#e34c26", "CSS": "#663399", "Python": "#3572A5",
    "TypeScript": "#3178c6", "Java": "#b07219", "C": "#555555", "C++": "#f34b7d",
    "C#": "#178600", "Shell": "#89e051", "PHP": "#4F5D95", "Go": "#00ADD8",
}


def api(path):
    req = urllib.request.Request(f"https://api.github.com{path}")
    req.add_header("Accept", "application/vnd.github+json")
    if TOKEN:
        req.add_header("Authorization", f"Bearer {TOKEN}")
    with urllib.request.urlopen(req) as r:
        return json.load(r)


repos = [r for r in api(f"/users/{USER}/repos?per_page=100&type=owner") if not r["fork"]]
stars = sum(r["stargazers_count"] for r in repos)
langs = {}
for r in repos:
    for name, size in api(f"/repos/{USER}/{r['name']}/languages").items():
        langs[name] = langs.get(name, 0) + size
commits = api(f"/search/commits?q=author:{USER}&per_page=1")["total_count"]
followers = api(f"/users/{USER}")["followers"]

total = sum(langs.values()) or 1
top = sorted(langs.items(), key=lambda kv: -kv[1])[:5]

W, H = 1000, 240
items = [("🛰️", "Repositórios", len(repos)), ("⭐", "Estrelas", stars),
         ("☄️", "Commits", commits), ("👽", "Seguidores", followers)]
cards = ""
for i, (icon, label, value) in enumerate(items):
    y = 70 if i < 2 else 150
    x = 30 + (i % 2) * 220
    cards += f'''
  <g class="pop" style="animation-delay:{i*0.15:.2f}s">
    <rect x="{x}" y="{y}" width="200" height="66" rx="12" fill="#ffffff" fill-opacity=".05" stroke="#a78bfa" stroke-opacity=".35"/>
    <text x="{x+18}" y="{y+42}" font-size="24">{icon}</text>
    <text x="{x+58}" y="{y+28}" class="lbl">{label}</text>
    <text x="{x+58}" y="{y+52}" class="num">{value}</text>
  </g>'''

bars = ""
y = 78
bx, bw = 520, 300
for i, (name, size) in enumerate(top):
    pct = size / total * 100
    w = max(bw * pct / 100, 4)
    c = COLORS.get(name, "#a78bfa")
    bars += f'''
  <text x="{bx}" y="{y+i*30+12}" class="lang">{name}</text>
  <rect x="{bx+110}" y="{y+i*30}" width="{bw}" height="14" rx="7" fill="#ffffff" fill-opacity=".07"/>
  <rect x="{bx+110}" y="{y+i*30}" width="{w:.1f}" height="14" rx="7" fill="{c}" class="grow" style="animation-delay:{0.3+i*0.12:.2f}s"/>
  <text x="{bx+bw+122}" y="{y+i*30+12}" class="pct">{pct:.1f}%</text>'''

svg = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}">
<defs>
  <linearGradient id="bg" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#05061a"/><stop offset=".6" stop-color="#0d0b2e"/><stop offset="1" stop-color="#1a0f3d"/></linearGradient>
</defs>
<style>
  text {{ font-family: 'Segoe UI', Ubuntu, 'Helvetica Neue', Arial, sans-serif; }}
  .h {{ font-size: 18px; font-weight: 700; fill: #fff; letter-spacing: 2px; }}
  .lbl {{ font-size: 12px; fill: #b9c4ff; letter-spacing: 1px; }}
  .num {{ font-size: 22px; font-weight: 700; fill: #fff; }}
  .lang {{ font-size: 13px; fill: #d9ccff; }}
  .pct {{ font-size: 12px; fill: #b9c4ff; }}
  .pop {{ opacity: 0; animation: pop .6s ease-out forwards; }}
  @keyframes pop {{ from {{ opacity: 0; transform: translateY(8px) }} to {{ opacity: 1; transform: none }} }}
  .grow {{ transform-box: fill-box; transform-origin: left; transform: scaleX(0); animation: grow 1.2s cubic-bezier(.2,.8,.2,1) forwards; }}
  @keyframes grow {{ to {{ transform: scaleX(1) }} }}
  .tw {{ animation: tw 3s ease-in-out infinite; }}
  @keyframes tw {{ 0%,100% {{ opacity: .2 }} 50% {{ opacity: .9 }} }}
</style>
<rect width="{W}" height="{H}" rx="16" fill="url(#bg)"/>
<rect x=".5" y=".5" width="{W-1}" height="{H-1}" rx="16" fill="none" stroke="#a78bfa" stroke-opacity=".25"/>
<g fill="#fff">
  <circle cx="470" cy="40" r="1" class="tw"/><circle cx="960" cy="200" r="1.2" class="tw" style="animation-delay:-1s"/>
  <circle cx="490" cy="210" r=".8" class="tw" style="animation-delay:-2s"/><circle cx="940" cy="30" r="1" class="tw" style="animation-delay:-.5s"/>
</g>
<text x="30" y="44" class="h">📡 PAINEL DA NAVE</text>
<text x="{bx}" y="44" class="h">🪐 LINGUAGENS</text>{cards}{bars}
</svg>'''
os.makedirs("assets", exist_ok=True)
open("assets/stats.svg", "w", encoding="utf-8").write(svg)
print(f"repos={len(repos)} stars={stars} commits={commits} langs={top}")
