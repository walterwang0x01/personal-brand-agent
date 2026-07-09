"""简报路径解析 — 从 tech-learning-and-projects 主仓读取，不再依赖本地采集副本。"""

from __future__ import annotations

import re
from datetime import datetime
from pathlib import Path

from brand_agent.config import settings

TOPICS = ("ai-agent", "china-tech", "global-tech")

TOPIC_NAMES = {
    "ai-agent": "AI Agent",
    "china-tech": "国内科技",
    "global-tech": "国际科技",
}

PORTFOLIO_BRIEFING_BASE = "https://walterwang0x01.github.io/portfolio/briefing"


def resolve_briefings_root() -> Path | None:
    """按优先级查找简报根目录。"""
    candidates: list[Path] = []
    if settings.briefings_dir:
        candidates.append(Path(settings.briefings_dir).expanduser())
    # personal-brand-agent 与 tech-learning-and-projects 同级
    here = Path(__file__).resolve().parent.parent
    candidates.extend([
        here.parent / "tech-learning-and-projects" / "learning-notes" / "briefings",
        here / "output" / "briefings",  # 遗留本地副本
    ])
    for path in candidates:
        if path.is_dir():
            return path
    return None


def briefing_file_path(topic: str, date_str: str | None = None) -> Path | None:
    """返回指定主题/日期的简报 md 路径。"""
    if topic not in TOPICS:
        return None
    root = resolve_briefings_root()
    if root is None:
        return None

    if date_str:
        try:
            dt = datetime.strptime(date_str, "%Y-%m-%d")
        except ValueError:
            return None
        path = root / topic / f"{dt.year:04d}" / f"{dt.month:02d}" / f"{date_str}.md"
        return path if path.is_file() else None

    # 默认今天，否则最近一篇
    today = datetime.now().strftime("%Y-%m-%d")
    today_path = briefing_file_path(topic, today)
    if today_path:
        return today_path

    topic_dir = root / topic
    if not topic_dir.exists():
        return None
    md_files = sorted(topic_dir.rglob("????-??-??.md"), reverse=True)
    return md_files[0] if md_files else None


def list_briefing_dates(topic: str, limit: int = 14) -> list[str]:
    """列出某主题最近 N 个简报日期（降序）。"""
    root = resolve_briefings_root()
    if root is None or topic not in TOPICS:
        return []
    dates: list[str] = []
    topic_dir = root / topic
    if not topic_dir.exists():
        return []
    for path in sorted(topic_dir.rglob("????-??-??.md"), reverse=True):
        m = re.match(r"(\d{4}-\d{2}-\d{2})\.md$", path.name)
        if m:
            dates.append(m.group(1))
        if len(dates) >= limit:
            break
    return dates


def portfolio_briefing_url(topic: str, date_str: str) -> str:
    return f"{PORTFOLIO_BRIEFING_BASE}/#{topic}/{date_str}"
