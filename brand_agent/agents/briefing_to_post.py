"""简报 → 社交内容 生成器

从 tech-learning-and-projects 主仓最新简报提取头条，生成：
- X/Twitter Thread（5-8 条，每条 ≤ 280 字符）
- 博客摘要（Markdown）

有 LLM API key 时用 LLM 改写，否则用规则提取。保存到 data/articles/，供 distribute 分发。
"""

from __future__ import annotations

import json
import re
from datetime import datetime
from pathlib import Path
from typing import TypedDict

from langgraph.graph import END, StateGraph

from brand_agent.article_schema import build_canonical_article
from brand_agent.briefings import (
    TOPIC_NAMES,
    briefing_file_path,
    portfolio_briefing_url,
)


class BriefToPostState(TypedDict):
    topic: str
    date: str
    briefing_path: str
    briefing_content: str
    headlines: list[dict]
    twitter_thread: list[str]
    blog_excerpt: str
    article: dict
    saved_path: str


def _key_points_from_headlines(headlines: list[dict]) -> list[str]:
    return [h.get("summary", "").strip() for h in headlines if h.get("summary")]


def _headline_references(headlines: list[dict]) -> list[str]:
    return [h.get("url", "").strip() for h in headlines if h.get("url")]


def _extract_links(text: str) -> list[str]:
    return re.findall(r"\((https?://[^)]+)\)", text)


def _first_paragraph(body: str) -> str:
    lines = []
    for line in body.strip().splitlines():
        s = line.strip()
        if not s or s.startswith("→") or s.startswith("|"):
            break
        lines.append(s)
    return " ".join(lines)[:400]


def parse_headlines(content: str) -> list[dict]:
    """解析 Kiro 简报格式：## 📌 头条 + ### 标题 + 正文 + → 链接。"""
    headlines: list[dict] = []

    section = re.search(r"##\s*📌\s*头条\s*\n(.*?)(?=\n##\s)", content, re.DOTALL)
    block = section.group(1) if section else ""

    for match in re.finditer(
        r"###\s+(.+?)\n\n(.*?)(?=\n---\n|\n###\s|\Z)",
        block,
        re.DOTALL,
    ):
        title = match.group(1).strip()
        body = match.group(2).strip()
        urls = _extract_links(body)
        headlines.append({
            "title": title,
            "url": urls[0] if urls else "",
            "summary": _first_paragraph(body),
        })

    if len(headlines) >= 2:
        return headlines[:3]

    # 快讯兜底
    brief_section = re.search(r"##\s*⚡\s*快讯\s*\n(.*?)(?=\n##\s)", content, re.DOTALL)
    if brief_section:
        for line in brief_section.group(1).splitlines():
            m = re.match(r"^-\s+\*\*(.+?)\*\*[：:](.+)$", line.strip())
            if not m:
                continue
            subject, rest = m.group(1), m.group(2)
            urls = _extract_links(rest)
            text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", rest)
            text = re.sub(r"→\s*", "", text).strip()
            headlines.append({
                "title": subject,
                "url": urls[0] if urls else "",
                "summary": text[:200],
            })
            if len(headlines) >= 3:
                break

    return headlines[:3]


def load_briefing(state: BriefToPostState) -> BriefToPostState:
    topic = state.get("topic", "ai-agent")
    date = state.get("date") or datetime.now().strftime("%Y-%m-%d")
    path = briefing_file_path(topic, date)
    if not path:
        state["briefing_content"] = ""
        state["briefing_path"] = ""
        state["date"] = date
        return state

    state["briefing_path"] = str(path)
    state["briefing_content"] = path.read_text(encoding="utf-8")
    state["date"] = date
    return state


def extract_headlines(state: BriefToPostState) -> BriefToPostState:
    content = state.get("briefing_content", "")
    state["headlines"] = parse_headlines(content) if content else []
    return state


def _rule_based_thread(topic: str, date: str, headlines: list[dict]) -> list[str]:
    topic_name = TOPIC_NAMES.get(topic, topic)
    portfolio_url = portfolio_briefing_url(topic, date)

    tweets = [
        f"🧵 {topic_name} 简报 · {date}\n\n"
        f"今日 {len(headlines)} 条值得关注，摘要 👇"
    ]

    for i, item in enumerate(headlines, 1):
        title = item.get("title", "")[:100]
        summary = item.get("summary", "")[:120]
        url = item.get("url", "")
        tweet = f"{i}/ {title}"
        if summary:
            tweet += f"\n\n{summary}"
        if url:
            tweet += f"\n\n🔗 {url}"
        tweets.append(tweet[:278] + ".." if len(tweet) > 280 else tweet)

    tweets.append(
        f"📰 完整简报：{portfolio_url}\n\n"
        "💬 你关注哪条？欢迎讨论"
    )
    return tweets


def _llm_rewrite_thread(topic: str, date: str, headlines: list[dict]) -> list[str] | None:
    from brand_agent.llm_factory import create_llm, get_backend_name

    if not headlines:
        return None

    llm = create_llm(temperature=0.7, timeout=60, max_tokens=3000)
    if llm is None:
        return None

    topic_name = TOPIC_NAMES.get(topic, topic)
    portfolio_url = portfolio_briefing_url(topic, date)
    items_text = "\n\n".join(
        f"{i}. {h['title']}\n摘要: {h.get('summary', '')}\n链接: {h.get('url', '')}"
        for i, h in enumerate(headlines, 1)
    )
    separator = "===TWEET==="
    prompt = f"""你是技术博主 Walter Wang，擅长在 X/Twitter 上传播 {topic_name} 相关内容。

基于以下 {len(headlines)} 条今日要闻，生成一条高质量的 Twitter Thread（中文）：
1. 第一条：吸引人的开场（≤ 240 字符）
2. 接下来每条：一条要闻一个推文，给出你的解读（≤ 260 字符，保留链接）
3. 最后一条：引导阅读完整简报 {portfolio_url}

要求：每条 ≤ 280 字符；技术术语可用英文；语气真诚。

今日要闻:
{items_text}

输出格式：每条推文用 `{separator}` 分隔。"""

    try:
        response = llm.invoke(prompt)
        text = response.content if hasattr(response, "content") else str(response)
        parts = [p.strip() for p in text.split(separator) if p.strip()]
        cleaned = []
        for p in parts:
            p = re.sub(r"^```\w*\s*", "", p)
            p = re.sub(r"\s*```$", "", p).strip()
            if p:
                cleaned.append(p)
        if len(cleaned) < 2:
            return None
        tweets = [t[:278] + ".." if len(t) > 280 else t for t in cleaned]
        print(f"[LLM 改写 Thread/{get_backend_name()}] 生成 {len(tweets)} 条")
        return tweets
    except Exception as e:
        print(f"[LLM 改写 Thread] 失败，fallback 到规则模板: {e}")
        return None


def generate_twitter_thread(state: BriefToPostState) -> BriefToPostState:
    headlines = state.get("headlines", [])
    topic = state.get("topic", "ai-agent")
    date = state.get("date", datetime.now().strftime("%Y-%m-%d"))
    thread = _llm_rewrite_thread(topic, date, headlines)
    if not thread:
        thread = _rule_based_thread(topic, date, headlines)
    state["twitter_thread"] = thread
    return state


def generate_blog_excerpt(state: BriefToPostState) -> BriefToPostState:
    headlines = state.get("headlines", [])
    topic = state.get("topic", "ai-agent")
    date = state.get("date", datetime.now().strftime("%Y-%m-%d"))
    topic_name = TOPIC_NAMES.get(topic, topic)

    lines = [f"## {topic_name} 简报摘要 — {date}", ""]
    for i, h in enumerate(headlines, 1):
        title = h.get("title", "")
        url = h.get("url", "")
        summary = h.get("summary", "")
        if url:
            lines.append(f"### {i}. [{title}]({url})")
        else:
            lines.append(f"### {i}. {title}")
        lines.append("")
        if summary:
            lines.append(summary)
            lines.append("")
    lines.append(f"📰 [阅读完整简报]({portfolio_briefing_url(topic, date)})")
    state["blog_excerpt"] = "\n".join(lines)
    return state


def save_article(state: BriefToPostState) -> BriefToPostState:
    topic = state.get("topic", "ai-agent")
    date = state.get("date", datetime.now().strftime("%Y-%m-%d"))
    article_id = f"briefing-{topic}-{date}"
    blog_excerpt = state.get("blog_excerpt", "")
    headlines = state.get("headlines", [])

    article = build_canonical_article(
        article_id=article_id,
        title=f"{TOPIC_NAMES.get(topic, topic)} 简报 · {date}",
        date=date,
        tags=[topic, "briefing", "daily"],
        summary=blog_excerpt,
        body_markdown=blog_excerpt,
        source_type="briefing",
        source_briefing=state.get("briefing_path", ""),
        source_topic=topic,
        key_points=_key_points_from_headlines(headlines),
        references=_headline_references(headlines),
        twitter_thread=state.get("twitter_thread", []),
        platform_drafts={},
        publish_pack_path="",
        portfolio_url=portfolio_briefing_url(topic, date),
        extra_fields={
            "headlines": headlines,
            "headlines_count": len(headlines),
        },
    )

    save_dir = Path("data/articles")
    save_dir.mkdir(parents=True, exist_ok=True)
    save_path = save_dir / f"{article_id}.json"
    save_path.write_text(json.dumps(article, ensure_ascii=False, indent=2), encoding="utf-8")

    state["article"] = article
    state["saved_path"] = str(save_path)
    return state


def build_briefing_to_post_graph():
    graph = StateGraph(BriefToPostState)
    graph.add_node("load_briefing", load_briefing)
    graph.add_node("extract", extract_headlines)
    graph.add_node("twitter", generate_twitter_thread)
    graph.add_node("blog", generate_blog_excerpt)
    graph.add_node("save", save_article)
    graph.set_entry_point("load_briefing")
    graph.add_edge("load_briefing", "extract")
    graph.add_edge("extract", "twitter")
    graph.add_edge("twitter", "blog")
    graph.add_edge("blog", "save")
    graph.add_edge("save", END)
    return graph.compile()


def generate_post_from_briefing(topic: str = "ai-agent", date: str | None = None) -> dict:
    workflow = build_briefing_to_post_graph()
    result = workflow.invoke({
        "topic": topic,
        "date": date or datetime.now().strftime("%Y-%m-%d"),
        "briefing_path": "",
        "briefing_content": "",
        "headlines": [],
        "twitter_thread": [],
        "blog_excerpt": "",
        "article": {},
        "saved_path": "",
    })
    return {
        "article": result["article"],
        "saved_path": result["saved_path"],
        "briefing_path": result["briefing_path"],
        "headlines_count": len(result["headlines"]),
        "twitter_thread": result["twitter_thread"],
    }
