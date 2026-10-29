"""Atualiza a seção "Últimas atividades" do README com eventos públicos recentes do GitHub."""
import json
import os
import re
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path

USER = os.environ.get("GH_USER", "YagoXavier10")
TOKEN = os.environ.get("GITHUB_TOKEN", "")
BRT = timezone(timedelta(hours=-3))
README = Path(__file__).resolve().parent.parent / "README.md"
START, END = "<!-- ATIVIDADE:INICIO -->", "<!-- ATIVIDADE:FIM -->"
MAX_LINES = 6
SKIP_REPOS = {f"{USER}/{USER}"}
# commits feitos pelas automações (GitHub Actions) não contam como atividade
AUTO_PREFIXES = ("📰", "🥋 Conquistas", "🤖 Modelo retreinado", "Atualiza estatísticas")


def api(path):
    req = urllib.request.Request(f"https://api.github.com{path}")
    req.add_header("Accept", "application/vnd.github+json")
    if TOKEN:
        req.add_header("Authorization", f"Bearer {TOKEN}")
    with urllib.request.urlopen(req) as r:
        return json.load(r)


def recent_commits():
    """Último commit feito à mão em cada projeto atualizado recentemente (ignora automações e o repo do perfil)."""
    items = []
    for repo in api(f"/users/{USER}/repos?sort=pushed&per_page=10&type=owner"):
        if repo["full_name"] in SKIP_REPOS or repo["fork"]:
            continue
        commits = [
            c for c in api(f"/repos/{repo['full_name']}/commits?per_page=30")
            if not (c.get("author") or {}).get("login", "").endswith("[bot]")
            and not c["commit"]["message"].startswith(AUTO_PREFIXES)
        ]
        if not commits:
            continue
        c = commits[0]["commit"]
        when = datetime.fromisoformat(c["author"]["date"].replace("Z", "+00:00")).astimezone(BRT)
        msg = c["message"].splitlines()[0].replace("|", "/")
        if len(msg) > 70:
            msg = msg[:67].rstrip() + "…"
        items.append((when, repo["name"], repo["html_url"], msg, repo.get("homepage") or ""))
    return sorted(items, reverse=True)[:MAX_LINES]


def main():
    lines = []
    for when, name, url, msg, home in recent_commits():
        site = f" · [site]({home})" if home else ""
        lines.append(f"| `{when:%d/%m}` | [**{name}**]({url}){site} | {msg} |")
    if not lines:
        lines = ["| | | Sem atividade pública recente |"]
    block = "\n".join([START, "| Quando | Projeto | Último commit |", "| :-: | :-- | :-- |", *lines, END])
    s = README.read_text(encoding="utf-8")
    s = re.sub(re.escape(START) + r".*?" + re.escape(END), lambda _: block, s, flags=re.S)
    README.write_text(s, encoding="utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
