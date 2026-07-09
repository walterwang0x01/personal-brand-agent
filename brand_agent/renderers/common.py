"""国内平台稿件渲染公共逻辑。"""

from __future__ import annotations

import re
from typing import Any

from brand_agent.article_schema import build_platform_draft, ensure_article_schema

_LLM_REWRITE_DISABLED = False


def _strip_hash_prefix(tags: list[str]) -> list[str]:
    return [tag[1:] if tag.startswith("#") else tag for tag in tags]


def prepare_article(article: dict[str, Any]) -> dict[str, Any]:
    normalized = ensure_article_schema(article)
    title = normalized.get("title", "")
    summary = normalized.get("summary") or normalized.get("excerpt") or ""
    body = normalized.get("body_markdown") or normalized.get("body") or ""
    key_points = normalized.get("key_points") or []
    references = normalized.get("references") or []
    tags = _strip_hash_prefix(normalized.get("tags", []))
    return {
        "raw": normalized,
        "title": title,
        "summary": summary.strip(),
        "body_markdown": body.strip(),
        "key_points": key_points,
        "references": references,
        "tags": tags,
    }


def format_reference_list(references: list[str]) -> str:
    if not references:
        return ""
    lines = ["", "## 参考链接", ""]
    for idx, ref in enumerate(references, 1):
        lines.append(f"{idx}. {ref}")
    return "\n".join(lines)


def markdown_to_text(text: str) -> str:
    cleaned = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)
    cleaned = re.sub(r"^#+\s*", "", cleaned, flags=re.MULTILINE)
    cleaned = re.sub(r"^\s*[-*]\s+", "", cleaned, flags=re.MULTILINE)
    cleaned = re.sub(r"`([^`]+)`", r"\1", cleaned)
    cleaned = re.sub(r"\n{2,}", "\n", cleaned)
    return cleaned.strip()


def compact_text(text: str, max_len: int = 120) -> str:
    compacted = " ".join(markdown_to_text(text).split())
    if len(compacted) <= max_len:
        return compacted
    return compacted[: max_len - 1].rstrip("，,、；;：:。.!? ") + "…"


def concise_key_points(
    key_points: list[str],
    *,
    max_items: int = 3,
    max_len: int = 60,
) -> list[str]:
    points: list[str] = []
    for point in key_points:
        text = compact_text(point, max_len=max_len)
        text = re.sub(r"^(今天|今日|这篇|这条|该)\s*", "", text)
        if text and text not in points:
            points.append(text)
        if len(points) >= max_items:
            break
    return points


def fallback_summary(summary: str, *, max_len: int = 90) -> str:
    text = compact_text(summary, max_len=max_len)
    if text:
        return text
    return "这篇内容里有几个值得马上关注的变化，我先帮你提炼重点。"


def make_hook_line(title: str, points: list[str], *, style: str) -> str:
    if style == "xiaohongshu":
        if points:
            return f"刷完《{compact_text(title, 28)}》，我先记住这 {min(len(points), 3)} 个点。"
        return f"今天花了点时间看《{compact_text(title, 28)}》，有些感受想记下来。"
    if style == "weibo":
        if points:
            return f"{compact_text(title, 34)}，先看 {min(len(points), 3)} 个重点。"
        return compact_text(title, 38)
    if style == "zhihu":
        return f"如果只看一个结论，我会说：{compact_text(title, 36)}值得继续跟。"
    if style == "wechat":
        return f"这篇内容可以先看结论，再决定是否展开读完整分析。"
    if style == "juejin":
        return f"先把最重要的信号拎出来，再看细节。"
    return compact_text(title, 40)


def make_takeaway_line(points: list[str], *, style: str) -> str:
    lead = points[0] if points else "变化正在加速"
    if style == "xiaohongshu":
        return f"我自己的感受是：{lead}，而且这个趋势短期内不会停。"
    if style == "weibo":
        return f"我的判断：{lead}，这事值得继续盯。"
    if style == "zhihu":
        return f"这背后真正值得看的，不是单条新闻，而是 {lead} 这类趋势。"
    if style == "wechat":
        return f"如果只总结一句话，我会把它归纳成：{lead}。"
    if style == "juejin":
        return f"把它翻译成工程语境，就是：{lead}。"
    return lead


def make_cta_line(*, style: str) -> str:
    if style == "xiaohongshu":
        return "如果你最近也在做内容、做产品，这几条真的可以收藏起来慢慢看。"
    if style == "weibo":
        return "你更关注哪一条？欢迎一起聊。"
    if style == "zhihu":
        return "如果你有不同判断，也欢迎把你的视角补在评论区。"
    if style == "wechat":
        return "如果你也在跟这条赛道，可以把你的判断一起补进来。"
    if style == "juejin":
        return "如果你也在做这类方向，欢迎把你的观察补在评论区。"
    return ""


def make_cover_suggestions(*, style: str, title: str) -> list[str]:
    if style == "xiaohongshu":
        return [
            f"封面标题建议：{compact_text(title, 18)}",
            "首图做成 3 屏卡片：结论、变化、建议",
        ]
    if style == "weibo":
        return [
            "封面建议一张信息卡，写上 2-3 个关键词",
            f"卡片标题建议：{compact_text(title, 16)}",
        ]
    if style == "zhihu":
        return ["知乎可不放封面，优先打磨标题和首段。"]
    if style == "wechat":
        return [
            f"封面主文案建议：{compact_text(title, 20)}",
            "首图可放趋势关键词或三点结论",
        ]
    if style == "juejin":
        return ["可选单张信息图，强调工程信号或技术关键词。"]
    return []


def make_image_prompts(*, style: str, title: str, points: list[str]) -> list[str]:
    focus_points = concise_key_points(points, max_items=3, max_len=28)
    focus = "、".join(focus_points) if focus_points else compact_text(title, 24)
    if style == "xiaohongshu":
        return [f"设计一组小红书图文卡片，主题《{compact_text(title, 18)}》，突出：{focus}。"]
    if style == "weibo":
        return [f"设计微博信息卡，主题《{compact_text(title, 18)}》，突出：{focus}。"]
    if style == "wechat":
        return [f"设计公众号头图，标题《{compact_text(title, 20)}》，关键词：{focus}。"]
    if style == "juejin":
        return [f"设计技术文章首图，主题《{compact_text(title, 20)}》，关键词：{focus}。"]
    if style == "zhihu":
        return [f"如需配图，做一张极简观点图，主题《{compact_text(title, 18)}》，关键词：{focus}。"]
    return []


def make_comment_suggestions(*, style: str, points: list[str]) -> list[str]:
    lead = points[0] if points else "这件事"
    if style == "xiaohongshu":
        return [f"首评建议：你最近最关注的是哪一点？我自己最在意的是“{compact_text(lead, 24)}”。"]
    if style == "weibo":
        return [f"首评建议：你更关注“{compact_text(lead, 22)}”还是另一条？"]
    if style == "zhihu":
        return [f"首评建议：如果你在一线使用这些工具，欢迎补充你对“{compact_text(lead, 24)}”的判断。"]
    if style == "wechat":
        return [f"留言引导：如果你也在关注“{compact_text(lead, 24)}”，欢迎分享你的看法。"]
    if style == "juejin":
        return [f"评论引导：你在实际工程里最在意“{compact_text(lead, 24)}”的哪一面？"]
    return []


def make_engagement_prompts(*, style: str) -> list[str]:
    if style == "xiaohongshu":
        return ["互动建议：文末加一句“想看完整版我再继续更”。"]
    if style == "weibo":
        return ["互动建议：可在末尾加投票式提问。"]
    if style == "zhihu":
        return ["互动建议：鼓励读者补充不同观点或实际案例。"]
    if style == "wechat":
        return ["互动建议：文末可加“欢迎留言告诉我你最关注哪一条”。"]
    if style == "juejin":
        return ["互动建议：邀请读者补充工程实践或链接。"]
    return []


def rewrite_point(point: str, *, style: str) -> str:
    core = compact_text(point, max_len=54)
    if style == "xiaohongshu":
        return f"我先记住的是：{core}。"
    if style == "weibo":
        return f"重点是：{core}。"
    if style == "zhihu":
        return f"先看这一点：{core}。"
    if style == "juejin":
        return f"- {core}"
    if style == "wechat":
        return f"- {core}"
    return core


def rewrite_paragraphs(
    points: list[str],
    *,
    style: str,
    max_items: int = 3,
) -> list[str]:
    selected = concise_key_points(points, max_items=max_items, max_len=52)
    if not selected:
        return []
    if style in {"xiaohongshu", "weibo", "zhihu"}:
        return [rewrite_point(point, style=style) for point in selected]
    return selected


def rewrite_paragraphs_with_llm(
    *,
    title: str,
    points: list[str],
    style: str,
    max_items: int = 3,
) -> list[str]:
    global _LLM_REWRITE_DISABLED
    selected = concise_key_points(points, max_items=max_items, max_len=72)
    if not selected:
        return []
    if _LLM_REWRITE_DISABLED:
        return rewrite_paragraphs(selected, style=style, max_items=max_items)

    try:
        from brand_agent.llm_factory import create_llm, get_backend_name
    except Exception:
        return rewrite_paragraphs(selected, style=style, max_items=max_items)

    llm = create_llm(temperature=0.6, timeout=20, max_tokens=900)
    if llm is None:
        return rewrite_paragraphs(selected, style=style, max_items=max_items)

    separator = "===BLOCK==="
    style_guide = {
        "xiaohongshu": "写成口语化生活笔记，每段 1 句，像真人随手记下的观察。",
        "weibo": "写成短促的信息流句子，每段 1 句，适合微博导流。",
        "zhihu": "写成观点化短段，每段 1 句，像回答中的核心论点。",
        "juejin": "写成工程视角的简洁 bullet，每段 1 句，适合技术社区。",
        "wechat": "写成适合公众号正文的小段落，每段 1 句，偏总结和判断。",
    }
    prompt = f"""你在给中文内容平台改写短段落。

平台: {style}
标题: {title}
要求: {style_guide.get(style, '改写成简洁自然的中文短段落。')}

把下面这些信息点分别改写成 {len(selected)} 段中文短句：
- 不要照抄原文
- 不要保留 Markdown 标记
- 每段 18 到 50 字
- 每段都要像人写的，不要像机器摘要
- 输出时严格用 `{separator}` 分隔，每段只写一句

原始信息点:
{chr(10).join(f"{i+1}. {point}" for i, point in enumerate(selected))}
"""
    try:
        response = llm.invoke(prompt)
        text = response.content if hasattr(response, "content") else str(response)
        parts = [compact_text(p, max_len=72) for p in text.split(separator) if p.strip()]
        if len(parts) >= 1:
            cleaned = parts[: len(selected)]
            if len(cleaned) == len(selected):
                return cleaned
        print(f"[Domestic Rewrite/{get_backend_name()}] 输出不足，fallback 到规则重写")
    except Exception as e:
        _LLM_REWRITE_DISABLED = True
        print(f"[Domestic Rewrite] LLM 重写失败，fallback 到规则重写: {e}")

    return rewrite_paragraphs(selected, style=style, max_items=max_items)


def make_draft(
    *,
    platform: str,
    title: str,
    summary: str,
    body_markdown: str,
    tags: list[str],
    title_candidates: list[str],
    warnings: list[str],
    manual_checklist: list[str],
    cover_suggestions: list[str],
    image_prompts: list[str] | None = None,
    comment_suggestions: list[str] | None = None,
    engagement_prompts: list[str] | None = None,
) -> dict[str, Any]:
    return build_platform_draft(
        platform=platform,
        title=title,
        summary=summary,
        body_markdown=body_markdown,
        tags=tags,
        title_candidates=title_candidates,
        warnings=warnings,
        manual_checklist=manual_checklist,
        cover_suggestions=cover_suggestions,
        image_prompts=image_prompts,
        comment_suggestions=comment_suggestions,
        engagement_prompts=engagement_prompts,
    )
