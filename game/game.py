"""Caça aos Aliens: jogo do README. Cada jogada chega como uma issue "alien|C4"."""
import base64
import json
import os
import random
import re
import sys
import urllib.parse
from datetime import datetime, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STATE = os.path.join(ROOT, "game", "state.json")
README = os.path.join(ROOT, "README.md")
REPO = "YagoXavier10/YagoXavier10"
COLS = "ABCDEF"
ROWS = 6
ALIENS = 6
START, END = "<!-- JOGO:INICIO -->", "<!-- JOGO:FIM -->"


def new_round(number):
    cells = [f"{c}{r}" for c in COLS for r in range(1, ROWS + 1)]
    hidden = base64.b64encode(json.dumps(random.sample(cells, ALIENS)).encode()).decode()
    return {"round": number, "hidden": hidden, "shots": {}}


def aliens(state):
    return set(json.loads(base64.b64decode(state["hidden"])))


def load():
    if os.path.exists(STATE):
        with open(STATE, encoding="utf-8") as f:
            return json.load(f)
    return {"game": new_round(1), "log": [], "players": {}, "winners": []}


def save(data):
    with open(STATE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def link(cell):
    title = urllib.parse.quote(f"alien|{cell}")
    body = urllib.parse.quote(
        "Só clicar em **Create** (ou **Submit new issue**)! "
        "Em uns 30 segundos o tabuleiro do perfil é atualizado. 🚀"
    )
    return f"https://github.com/{REPO}/issues/new?title={title}&body={body}"


def render(data):
    game = data["game"]
    found = aliens(game) & set(game["shots"])
    lines = [
        START,
        "## 🎮 Caça aos Aliens",
        "",
        f"Tem **{ALIENS} aliens** escondidos nessa galáxia. Clique em um 🌑 para disparar: "
        "o GitHub abre uma issue, é só confirmar e esperar uns 30 segundos. "
        "Quem achar o último alien vence a rodada!",
        "",
        f"<p align=\"center\"><b>Rodada {game['round']}</b> · 👾 {len(found)}/{ALIENS} encontrados · "
        f"🔫 {len(game['shots'])} disparos</p>",
        "",
        "<div align=\"center\">",
        "",
        "| | " + " | ".join(f"**{c}**" for c in COLS) + " |",
        "|:-:|" + ":-:|" * len(COLS),
    ]
    hidden = aliens(game)
    for r in range(1, ROWS + 1):
        row = []
        for c in COLS:
            cell = f"{c}{r}"
            if cell in game["shots"]:
                row.append("👾" if cell in hidden else "💨")
            else:
                row.append(f"[🌑]({link(cell)})")
        lines.append(f"| **{r}** | " + " | ".join(row) + " |")
    lines += ["", "</div>", ""]

    if data["log"]:
        lines.append("**📡 Últimos disparos**")
        lines.append("")
        for e in data["log"][:5]:
            lines.append(f"- [@{e['user']}](https://github.com/{e['user']}) atirou em **{e['cell']}** → {e['result']}")
        lines.append("")
    top = sorted(data["players"].items(), key=lambda kv: (-kv[1]["hits"], -kv[1]["shots"]))[:5]
    if top:
        lines.append("**🏆 Melhores caçadores**")
        lines.append("")
        lines.append("| Piloto | 👾 Aliens | 🔫 Disparos | 🥇 Rodadas vencidas |")
        lines.append("|:--|:-:|:-:|:-:|")
        for user, p in top:
            lines.append(f"| [@{user}](https://github.com/{user}) | {p['hits']} | {p['shots']} | {p.get('wins', 0)} |")
        lines.append("")
    lines.append(END)

    with open(README, encoding="utf-8") as f:
        readme = f.read()
    block = "\n".join(lines)
    if START in readme:
        readme = re.sub(re.escape(START) + r".*?" + re.escape(END), lambda _: block, readme, flags=re.S)
    else:
        readme = readme.rstrip() + "\n\n" + block + "\n"
    with open(README, "w", encoding="utf-8") as f:
        f.write(readme)


def play(title, user):
    """Aplica a jogada e devolve a mensagem para comentar na issue."""
    data = load()
    game = data["game"]
    m = re.fullmatch(r"\s*alien\|\s*([A-Fa-f])\s*([1-6])\s*", title)
    if not m:
        return data, "🤔 Não entendi essa jogada. Use os 🌑 do tabuleiro no meu perfil!"
    cell = f"{m[1].upper()}{m[2]}"
    if cell in game["shots"]:
        return data, f"😅 A casa **{cell}** já foi atingida. Escolha outro 🌑 no perfil!"

    hit = cell in aliens(game)
    game["shots"][cell] = user
    p = data["players"].setdefault(user, {"hits": 0, "shots": 0, "wins": 0})
    p["shots"] += 1
    p["hits"] += hit
    result = "👾 Alien abatido!" if hit else "💨 Errou, só poeira espacial."
    data["log"].insert(0, {"user": user, "cell": cell, "result": result,
                           "at": datetime.now(timezone.utc).isoformat(timespec="seconds")})
    data["log"] = data["log"][:20]

    msg = f"{result} Você atirou em **{cell}**."
    if aliens(game) <= set(game["shots"]):
        p["wins"] += 1
        data["winners"].insert(0, {"round": game["round"], "user": user})
        data["game"] = new_round(game["round"] + 1)
        msg += f"\n\n🏆 **Você achou o último alien e venceu a rodada {game['round']}!** Uma nova rodada começou."
    return data, msg + f"\n\n[Voltar ao perfil](https://github.com/{REPO.split('/')[0]})"


if __name__ == "__main__":
    if sys.argv[1:2] == ["render"]:
        data = load()
        save(data)
        render(data)
    else:
        data, msg = play(os.environ["ISSUE_TITLE"], os.environ["ISSUE_USER"])
        save(data)
        render(data)
        with open(os.environ.get("REPLY_FILE", "reply.md"), "w", encoding="utf-8") as f:
            f.write(msg)
