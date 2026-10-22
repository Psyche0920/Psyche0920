"""Render a self-contained GitHub portfolio from attributable project evidence."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
from collections import Counter
from dataclasses import dataclass, field
from datetime import date
from html import escape
from html.parser import HTMLParser
from pathlib import Path
from typing import cast
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
BG = "#090e1c"
PANEL = "#10192c"
INK = "#edf4ff"
MUTED = "#a0b2cc"
CYAN = "#63e8ed"
PURPLE = "#ad95ff"
LIME = "#c4f17b"
FONT = "Inter,Segoe UI,Arial,sans-serif"
MONO = "Consolas,Menlo,monospace"
ACHIEVEMENTS = ("Quickdraw", "Pair Extraordinaire", "Pull Shark", "YOLO")


class ProfileDataError(RuntimeError):
    """Public source data could not be retrieved or validated."""


@dataclass(frozen=True, slots=True)
class Repository:
    name: str
    language: str | None
    stars: int


@dataclass(frozen=True, slots=True)
class ContributionDay:
    day: date
    level: int


@dataclass(frozen=True, slots=True)
class Snapshot:
    captured: str
    repositories: tuple[Repository, ...]
    followers: int
    contributions: int
    days: tuple[ContributionDay, ...]


@dataclass(frozen=True, slots=True)
class Focus:
    label: str
    projects: tuple[str, ...]


FOCUSES = (
    Focus("Agentic AI", ("GoalCoach", "Neckarus", "PastPort")),
    Focus("Backend & state", ("GoalCoach", "Neckarus", "PastPort")),
    Focus("RAG & tool calling", ("RAG-against-the-machine", "Python_callmemaybe")),
    Focus("Algorithms & games", ("push_swap", "python_amazing", "Python-fly_in", "pacman")),
    Focus("Systems & C", ("libft", "ft_printf", "get_next_line", "c_codexion", "born2beroot", "Inception")),
    Focus("Product delivery", ("GoalCoach", "PastPort", "Neckarus")),
)


class CalendarParser(HTMLParser):
    """Read published contribution levels without authenticated browser data."""

    def __init__(self) -> None:
        super().__init__()
        self.days: list[ContributionDay] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = dict(attrs)
        if tag == "td" and values.get("data-date") and values.get("data-level"):
            self.days.append(ContributionDay(date.fromisoformat(str(values["data-date"])), int(str(values["data-level"]))))


class PublicGitHubSource:
    """Fetch only unauthenticated public profile endpoints, never private repos."""

    @staticmethod
    def text(url: str) -> str:
        request = Request(url, headers={"User-Agent": "Psyche0920-Portfolio", "Accept": "application/vnd.github+json"})
        try:
            with urlopen(request, timeout=30) as response:
                payload = cast(bytes, response.read())
                return payload.decode("utf-8")
        except (HTTPError, URLError, TimeoutError, UnicodeError) as exc:
            raise ProfileDataError(f"Cannot refresh public profile source: {url}") from exc

    def fetch(self) -> Snapshot:
        user = cast(dict[str, object], json.loads(self.text("https://api.github.com/users/Psyche0920")))
        records: list[Repository] = []
        for page in range(1, 101):
            batch = cast(list[dict[str, object]], json.loads(self.text(f"https://api.github.com/users/Psyche0920/repos?per_page=100&type=owner&page={page}")))
            for item in batch:
                language = item.get("language")
                records.append(Repository(str(item["name"]), str(language) if language else None, self.integer(item["stargazers_count"])))
            if len(batch) < 100:
                break
        calendar = self.text("https://github.com/users/Psyche0920/contributions")
        return self.parse(calendar, tuple(records), self.integer(user["followers"]))

    @staticmethod
    def integer(value: object) -> int:
        if not isinstance(value, int) or isinstance(value, bool) or value < 0:
            raise ProfileDataError("Expected a non-negative integer in GitHub response")
        return value

    @staticmethod
    def parse(calendar: str, repos: tuple[Repository, ...], followers: int) -> Snapshot:
        parser = CalendarParser()
        parser.feed(calendar)
        total = re.search(r'([\d,]+)\s+contributions?\s+in the last year', calendar)
        if total is None or not parser.days:
            raise ProfileDataError("GitHub calendar format changed; preserve the previous assets")
        return Snapshot(date.today().isoformat(), repos, followers, int(total[1].replace(",", "")), tuple(parser.days))


@dataclass(slots=True)
class Svg:
    width: int
    height: int
    title: str
    parts: list[str] = field(default_factory=list)

    def add(self, markup: str) -> None:
        self.parts.append(markup)

    def text(self, x: float, y: float, label: str, size: int = 18, color: str = INK, weight: int = 400, anchor: str = "start", mono: bool = False) -> None:
        self.add(f'<text x="{x}" y="{y}" fill="{color}" font-size="{size}" font-weight="{weight}" text-anchor="{anchor}" font-family="{MONO if mono else FONT}">{escape(label)}</text>')

    def rect(self, x: float, y: float, w: float, h: float, fill: str = PANEL, stroke: str = "#24314b", radius: int = 18) -> None:
        self.add(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{radius}" fill="{fill}" stroke="{stroke}"/>')

    def line(self, x1: float, y1: float, x2: float, y2: float, color: str = "#26344e") -> None:
        self.add(f'<path d="M{x1},{y1} L{x2},{y2}" stroke="{color}" fill="none"/>')

    def render(self) -> str:
        return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{self.width}" height="{self.height}" viewBox="0 0 {self.width} {self.height}" role="img" aria-labelledby="title">
<title id="title">{escape(self.title)}</title>
<defs>
<linearGradient id="border"><stop stop-color="{CYAN}"/><stop offset=".5" stop-color="{PURPLE}"/><stop offset="1" stop-color="{LIME}"/></linearGradient>
<radialGradient id="halo"><stop stop-color="#524389" stop-opacity=".4"/><stop offset="1" stop-color="{BG}" stop-opacity="0"/></radialGradient>
<pattern id="grid" width="40" height="40" patternUnits="userSpaceOnUse"><path d="M40 0H0V40" fill="none" stroke="#1c2944" stroke-width=".6"/></pattern>
<style>@keyframes pulse{{0%,100%{{opacity:.35}}50%{{opacity:1}}}} @keyframes orbit{{to{{transform:rotate(360deg)}}}} @keyframes flow{{to{{stroke-dashoffset:-120}}}} .pulse{{animation:pulse 4s ease-in-out infinite}} .flow{{stroke-dasharray:6 12;animation:flow 8s linear infinite}} .orbit{{transform-origin:950px 185px;animation:orbit 40s linear infinite}} @media(prefers-reduced-motion:reduce){{.pulse,.flow,.orbit{{animation:none}}}}</style>
</defs>
<rect x="1" y="1" width="{self.width-2}" height="{self.height-2}" rx="22" fill="{BG}" stroke="#293650"/>
{''.join(self.parts)}</svg>'''


@dataclass(frozen=True, slots=True)
class ProjectCard:
    slug: str
    number: str
    title: str
    category: str
    lines: tuple[str, str]
    stack: str
    status: str
    accent: str
    motif: str


PROJECTS = (
    ProjectCard("goalcoach", "01", "GoalCoach", "ADAPTIVE LEARNING / TEAM LEAD", ("From a learner goal to a persistent,", "adaptive plan-teach-assess loop."), "PYTHON / PYDANTICAI / FASTAPI / SQLITE", "MVP DEMONSTRATED", CYAN, "loop"),
    ProjectCard("rag", "02", "RAG against the Machine", "RETRIEVAL / LOCAL LLM", ("Codebase question answering with", "BM25 retrieval and local Qwen inference."), "PYTHON / AST / BM25 / QWEN", "IMPLEMENTED & EVALUATED", PURPLE, "search"),
    ProjectCard("tools", "03", "Call Me Maybe", "FUNCTION CALLING / STRUCTURED OUTPUT", ("Natural language to validated function", "calls through constrained decoding."), "PYTHON / LLM LOGITS / PYDANTIC", "IMPLEMENTED & TESTED", LIME, "braces"),
    ProjectCard("pastport", "04", "PastPort", "HERITAGE / FRAMEWORK & TEAM LEAD", ("Traceable research, interactive stories", "and a shared workflow framework."), "PYTHON / LANGGRAPH / JAVASCRIPT", "IN DEVELOPMENT / PRIVATE SOURCE", CYAN, "diamond"),
    ProjectCard("neckarus", "05", "Neckarus", "CITY ASSISTANT / PRODUCT & WORKFLOW", ("Environmental data, nearby facilities", "and a location-aware voice assistant."), "PYTHON / FASTAPI / AZURE SPEECH", "PROTOTYPE / PRIVATE SOURCE", PURPLE, "pin"),
    ProjectCard("pacman", "06", "Pac-Man", "TEAM PROJECT / MODULAR GAME", ("Procedural mazes, ghost behaviour,", "persistent scores and arcade gameplay."), "PYTHON / PYGAME / ALGORITHMS", "COMPLETED / PLAYABLE RELEASE", LIME, "pacman"),
)


class ProfileRenderer:
    def __init__(self, snapshot: Snapshot) -> None:
        self.snapshot = snapshot
        self.assets = ROOT / "assets"
        self.assets.mkdir(exist_ok=True)
        self.files: dict[str, str] = {}

    def save(self, name: str, canvas: Svg) -> None:
        content = canvas.render()
        digest = hashlib.sha256(content.encode("utf-8")).hexdigest()[:10]
        filename = f"{name}-{digest}.svg"
        self.files[name] = filename
        (self.assets / filename).write_text(content, encoding="utf-8")

    def hero(self) -> None:
        s = Svg(1200, 390, "Weijia Han | Applied AI and agentic systems | Heilbronn, Germany")
        s.add('<rect x="1" y="1" width="1198" height="388" rx="22" fill="url(#grid)"/>')
        s.add('<ellipse cx="950" cy="180" rx="330" ry="250" fill="url(#halo)"/>')
        s.text(45, 45, "PSYCHE0920  /  BUILDER PROFILE", 15, CYAN, mono=True)
        s.text(43, 144, "WEIJIA HAN", 85, INK, 800)
        s.text(47, 194, "APPLIED AI & AGENTIC SYSTEMS", 26, CYAN, 600)
        s.text(47, 230, "Product thinking. Working software. Real-world problems.", 20, MUTED)
        s.line(47, 263, 710, 263)
        for x, label, color in ((47, "42 HEILBRONN", CYAN), (258, "LEVEL3 AI", PURPLE), (469, "TUM · M&DS", LIME)):
            s.rect(x, 286, 188, 37, "#10192c", "#2a3854", 8)
            s.text(x+94, 310, label, 14, color, 600, "middle", True)
        s.text(47, 362, "HEILBRONN, DE  //  PYTHON · C · LLM SYSTEMS", 14, MUTED, mono=True)
        s.add(f'<g class="orbit"><circle cx="950" cy="185" r="126" fill="none" stroke="{PURPLE}" stroke-opacity=".5" stroke-dasharray="4 12"/><ellipse cx="950" cy="185" rx="149" ry="61" transform="rotate(40 950 185)" fill="none" stroke="{CYAN}" stroke-opacity=".5"/><circle cx="1076" cy="185" r="5" fill="{LIME}"/></g>')
        points = ((950,83),(1039,134),(1039,236),(950,287),(861,236),(861,134),(950,185))
        for i, (x,y) in enumerate(points):
            for xx,yy in points[i+1:]: s.line(x,y,xx,yy,"#283957")
        s.add(f'<path class="flow" d="M950 83L1039 134L950 185L861 236L950 287L1039 236L950 185L861 134Z" stroke="{CYAN}" stroke-width="2" fill="none"/>')
        for i,(x,y) in enumerate(points):
            s.add(f'<circle class="pulse" cx="{x}" cy="{y}" r="{9 if i==6 else 5}" fill="{CYAN if i%2 else PURPLE}" style="animation-delay:{i/3}s"/>')
        s.text(950, 345, "IDEA → SYSTEM → PRODUCT", 13, CYAN, anchor="middle", mono=True)
        self.save("hero", s)

    def snapshot_panel(self) -> None:
        s = Svg(1200, 172, "GitHub snapshot: public repositories, yearly contributions, earned achievements and portfolio focus areas")
        metrics = ((str(len(self.snapshot.repositories)), "PUBLIC REPOSITORIES", CYAN), (str(self.snapshot.contributions), "CONTRIBUTIONS / YEAR", PURPLE), (f"{len(ACHIEVEMENTS):02}", "EARNED ACHIEVEMENTS", LIME), ("06", "PORTFOLIO FOCUS AREAS", CYAN))
        for i,(number,label,color) in enumerate(metrics):
            x = 36+i*294
            if i: s.line(x-18, 30, x-18, 119)
            s.text(x, 81, number, 49, color, 700)
            s.text(x, 111, label, 13, MUTED, mono=True)
        s.text(36, 149, f"GITHUB PUBLIC SNAPSHOT  /  {self.snapshot.captured}  /  Statistics are not a skill rating", 13, MUTED, mono=True)
        self.save("snapshot", s)

    def radar(self) -> None:
        s = Svg(1200, 535, "Portfolio radar: number of evidenced projects per focus area; language chart: primary language of public source repositories")
        s.text(34, 47, "01 / PORTFOLIO RADAR", 20, CYAN, 600, mono=True)
        s.text(646, 47, "02 / LANGUAGE FOOTPRINT", 20, PURPLE, 600, mono=True)
        s.text(34, 78, "Breadth of project work, grounded in linked repositories", 16, MUTED)
        s.text(646, 78, "Primary language of public source repositories", 16, MUTED)
        s.line(607, 30, 607, 485)
        cx,cy,radius = 302,282,139
        def point(i: int, r: float) -> tuple[float,float]:
            angle = -math.pi/2+i*math.pi/3
            return cx+r*math.cos(angle),cy+r*math.sin(angle)
        for level in range(1,5):
            coords = " ".join(f"{x:.2f},{y:.2f}" for x,y in (point(i,radius*level/4) for i in range(6)))
            s.add(f'<polygon points="{coords}" fill="none" stroke="#263650"/>')
            s.text(cx+7, cy-radius*level/4+5, str(level*2), 11, MUTED)
        for i,focus in enumerate(FOCUSES):
            x,y=point(i,radius)
            s.line(cx,cy,x,y)
            lx,ly=point(i,radius+34)
            s.text(lx,ly,focus.label,15,INK,600,"middle")
            s.text(lx,ly+20,f"{len(focus.projects)} projects",13,CYAN,400,"middle")
        values=[point(i, radius*len(f.projects)/8) for i,f in enumerate(FOCUSES)]
        s.add('<polygon points="'+' '.join(f'{x:.2f},{y:.2f}' for x,y in values)+f'" fill="{CYAN}" fill-opacity=".16" stroke="{CYAN}" stroke-width="3"/>')
        for x,y in values: s.add(f'<circle class="pulse" cx="{x}" cy="{y}" r="5" fill="{LIME}"/>')
        s.text(34, 510, "Scale 0–8 projects / categories overlap / not proficiency", 13, MUTED)
        languages=Counter(r.language for r in self.snapshot.repositories if r.language and r.name!="Psyche0920")
        total=sum(languages.values())
        colors=(CYAN,PURPLE,LIME,"#ffb884","#f18dbb")
        offset=0.0
        circumference=2*math.pi*101
        s.add('<circle cx="900" cy="260" r="101" stroke="#1b2840" stroke-width="27" fill="none"/>')
        for (language,count),color in zip(languages.most_common(),colors,strict=False):
            length=count/total*circumference
            s.add(f'<circle cx="900" cy="260" r="101" fill="none" stroke="{color}" stroke-width="27" stroke-dasharray="{length} {circumference-length}" stroke-dashoffset="{-offset}" transform="rotate(-90 900 260)"/>')
            offset+=length
        s.text(900,252,str(total),53,INK,700,"middle")
        s.text(900,281,"SOURCE REPOS",13,MUTED,400,"middle",True)
        for i,((language,count),color) in enumerate(zip(languages.most_common(),colors,strict=False)):
            x=757+i*174
            s.add(f'<circle cx="{x}" cy="419" r="5" fill="{color}"/>')
            s.text(x+16,425,f"{language}  {count}/{total}",17,INK,600)
        s.text(646,486,"Repository count; not code volume or professional mastery",13,MUTED)
        s.text(646,510,f"Source: GitHub REST API · {self.snapshot.captured}",12,MUTED)
        self.save("radar-languages",s)

    def activity(self) -> None:
        s=Svg(1200,354,"Contribution skyline using GitHub's published daily contribution intensity")
        s.text(34,47,"03 / CONTRIBUTION SKYLINE",20,CYAN,600,mono=True)
        s.text(34,78,"A year of building, one contribution at a time.",17,MUTED)
        s.text(1160,47,str(self.snapshot.contributions),33,LIME,700,"end")
        s.text(1160,77,"contributions / last year",14,MUTED,400,"end")
        first=min(x.day for x in self.snapshot.days)
        colors=("#142137","#1b606e","#208e9a","#3ac9d0",CYAN)
        for d in sorted(self.snapshot.days,key=lambda x:x.day.weekday()):
            delta=(d.day-first).days
            col,row=delta//7,delta%7
            x,y=42+col*19+row*5,137+row*17
            h=d.level*8
            s.add(f'<g><title>{d.day.isoformat()} · GitHub intensity {d.level}/4</title><path d="M{x},{y-h}l14,-4l5,5l-14,4Z" fill="{colors[d.level]}"/><path d="M{x},{y-h}l14,-4v{h+4}l-14,4Z" fill="{colors[d.level]}" fill-opacity=".64"/><path d="M{x+14},{y-h-4}l5,5v{h+4}l-5,-5Z" fill="{colors[d.level]}" fill-opacity=".35"/></g>')
        s.text(34,303,f"{first.strftime('%b %Y').upper()} → {max(d.day for d in self.snapshot.days).strftime('%b %Y').upper()}",14,MUTED,mono=True)
        s.text(34,330,f"Public calendar snapshot · {self.snapshot.captured} · Heights reflect GitHub intensity levels, not commit counts",12,MUTED)
        for i,c in enumerate(colors): s.rect(1006+i*25,294,18,18,c,c,3)
        self.save("activity",s)

    def card(self, p: ProjectCard) -> None:
        s=Svg(580,272,p.title+" | "+p.category+" | "+p.status)
        s.add(f'<path d="M24 1H556" stroke="{p.accent}" stroke-width="2"/>')
        s.text(26,37,p.number+" / "+p.category,11,p.accent,mono=True)
        s.text(26,88,p.title,29 if len(p.title)<20 else 26,INK,700)
        for i,line in enumerate(p.lines): s.text(26,127+i*25,line,17,MUTED)
        s.text(26,194,p.stack,11,p.accent,mono=True)
        s.line(26,214,554,214)
        s.add(f'<circle class="pulse" cx="32" cy="241" r="4" fill="{p.accent}"/>')
        s.text(45,245,p.status,11,MUTED,mono=True)
        s.text(548,90,{"loop":"↻","search":"⌕","braces":"{ }","diamond":"◇","pin":"◎","pacman":"◉"}[p.motif],45,p.accent,anchor="end",mono=True)
        self.save("project-"+p.slug,s)

    def journey(self) -> None:
        s=Svg(1200,224,"Career journey: UNOV UNODC, BIGO, Huawei, 42 Heilbronn, LEVEL3 AI Engineering")
        s.text(34,43,"04 / FROM PEOPLE & PRODUCTS TO APPLIED AI",20,PURPLE,600,mono=True)
        milestones=(("2021–22","UNOV / UNODC","Multilingual policy tools"),("2022–23","BIGO LIVE","200+ team / 20+ countries"),("2023","HUAWEI","Digital services delivery"),("2025–NOW","42 + TUM","Software / data science"),("2026","LEVEL3 AI","GoalCoach MVP delivery"))
        s.line(54,107,1119,107,CYAN)
        for i,(year,name,caption) in enumerate(milestones):
            x=54+i*228
            s.add(f'<circle cx="{x}" cy="107" r="6" fill="{CYAN if i%2==0 else PURPLE}"/>')
            s.text(x-20,84,year,12,CYAN,mono=True)
            s.text(x-20,150,name,17,INK,700)
            s.text(x-20,178,caption,12,MUTED)
        self.save("journey",s)

    def stack(self) -> None:
        s=Svg(1200,203,"Working toolkit: Python, C, FastAPI, PydanticAI, LangGraph, SQLite, Git, Linux, pytest and Jira")
        s.text(34,42,"TOOLKIT / FROM LOW-LEVEL SYSTEMS TO AGENTIC PRODUCTS",18,CYAN,600,mono=True)
        tools=(("Py","Python",CYAN),("C","C",PURPLE),("API","FastAPI",LIME),("AI","PydanticAI",CYAN),("LG","LangGraph",PURPLE),("DB","SQLite",LIME),("G","Git",CYAN),("$","Linux",PURPLE),("✓","pytest",LIME),("J","Jira",CYAN))
        for i,(icon,label,color) in enumerate(tools):
            x,y=34+(i%5)*231,64+(i//5)*62
            s.rect(x,y,210,48,PANEL,"#25344e",10)
            s.text(x+16,y+31,icon,18,color,700,mono=True)
            s.text(x+64,y+31,label,16,INK,600)
        self.save("stack",s)

    def button(self,name: str,label: str,accent: str,width: int) -> None:
        s=Svg(width,48,label)
        s.rect(1,1,width-2,46,PANEL,accent,10)
        s.text(width/2,30,label,15,accent,600,"middle",True)
        self.save(name,s)

    def run(self) -> None:
        self.hero()
        self.snapshot_panel()
        self.radar()
        self.activity()
        self.journey()
        self.stack()
        for project in PROJECTS: self.card(project)
        self.button("email","hanweijia.ann@outlook.com",CYAN,330)
        self.button("linkedin","LinkedIn ↗",PURPLE,165)
        self.button("goalcoach-link","GoalCoach ↗",LIME,175)
        readme_path = ROOT / "README.md"
        if readme_path.exists():
            readme = readme_path.read_text(encoding="utf-8")
            for name, filename in self.files.items():
                readme = re.sub(rf'src="assets/{re.escape(name)}(?:-[0-9a-f]{{10}})?\.svg"', f'src="assets/{filename}"', readme)
            readme_path.write_text(readme, encoding="utf-8")
        for path in self.assets.glob("*.svg"):
            managed = any(re.fullmatch(rf"{re.escape(name)}(?:-[0-9a-f]{{10}})?\.svg", path.name) for name in self.files)
            if managed and path.name not in self.files.values():
                path.unlink()


def main() -> None:
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--refresh",action="store_true",help="Refresh from public GitHub APIs; no credentials required")
    args=parser.parse_args()
    source=PublicGitHubSource()
    if args.refresh:
        snapshot=source.fetch()
    elif (ROOT/"data/snapshot.json").exists():
        saved=cast(dict[str,object],json.loads((ROOT/"data/snapshot.json").read_text()))
        repo_rows=cast(list[dict[str,object]],saved["repositories"])
        day_rows=cast(list[dict[str,object]],saved["days"])
        snapshot=Snapshot(str(saved["captured"]),tuple(Repository(str(r["name"]),str(r["language"]) if r["language"] else None,source.integer(r["stars"])) for r in repo_rows),source.integer(saved["followers"]),source.integer(saved["contributions"]),tuple(ContributionDay(date.fromisoformat(str(d["date"])),source.integer(d["level"])) for d in day_rows))
    else:
        user=cast(dict[str,object],json.loads((ROOT/"data/user.json").read_text()))
        repos=cast(list[dict[str,object]],json.loads((ROOT/"data/repos.json").read_text()))
        snapshot=source.parse((ROOT/"data/contributions.html").read_text(),tuple(Repository(str(r["name"]),str(r["language"]) if r["language"] else None,source.integer(r["stargazers_count"])) for r in repos),source.integer(user["followers"]))
    ProfileRenderer(snapshot).run()
    stored={"captured":snapshot.captured,"followers":snapshot.followers,"contributions":snapshot.contributions,"repositories":[{"name":r.name,"language":r.language,"stars":r.stars} for r in snapshot.repositories],"days":[{"date":d.day.isoformat(),"level":d.level} for d in snapshot.days]}
    (ROOT/"data/snapshot.json").write_text(json.dumps(stored,indent=2)+"\n")
    evidence={"captured":snapshot.captured,"sources":["https://api.github.com/users/Psyche0920","https://api.github.com/users/Psyche0920/repos","https://github.com/users/Psyche0920/contributions"],"public_repositories":len(snapshot.repositories),"yearly_contributions":snapshot.contributions,"followers":snapshot.followers,"radar_unit":"number of linked projects, not a skill score","radar":[{"label":f.label,"projects":list(f.projects),"count":len(f.projects)} for f in FOCUSES],"earned_achievements":list(ACHIEVEMENTS),"achievement_source":"https://github.com/Psyche0920?tab=achievements"}
    (ROOT/"data/evidence.json").write_text(json.dumps(evidence,indent=2)+"\n")
    print(f"Rendered {len(tuple((ROOT/'assets').glob('*.svg')))} profile assets")


if __name__ == "__main__":
    main()
