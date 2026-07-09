"""小红书稿件渲染。"""

from __future__ import annotations

from typing import Any

from brand_agent.renderers.common import (
    concise_key_points,
    make_comment_suggestions,
    make_cover_suggestions,
    make_draft,
    make_cta_line,
    make_engagement_prompts,
    make_hook_line,
    make_image_prompts,
    make_takeaway_line,
    prepare_article,
    rewrite_paragraphs_with_llm,
)


def _format_tags(tags: list[str]) -> str:
    if not tags:
        return "#AI #效率工具 #个人成长"
    formatted = []
    for tag in tags[:6]:
        clean = tag.strip().replace(" ", "")
        if not clean:
            continue
        formatted.append(clean if clean.startswith("#") else f"#{clean}")
    return " ".join(formatted)


def render_xiaohongshu(article: dict[str, Any]) -> dict[str, Any]:
    prepared = prepare_article(article)
    title = prepared["title"]
    summary = prepared["summary"]
    key_points = prepared["key_points"]
    tags = prepared["tags"]
    short_points = concise_key_points(key_points, max_items=4, max_len=42)
    rewritten_points = rewrite_paragraphs_with_llm(
        title=title,
        points=key_points,
        style="xiaohongshu",
        max_items=3,
    )

    title_candidates = [
        f"{title}，今天最值得关注的 3 个点",
        f"今天刷完 {title}，我记下了这几点",
        f"{title}：普通人也值得关注吗？",
    ]
    opening = make_hook_line(title, short_points, style="xiaohongshu")
    bullet_lines = [f"{idx}. {point}" for idx, point in enumerate(short_points, 1) if point]
    note_parts = [
        f"# {title_candidates[0]}",
        "",
        opening,
        "",
        "如果你和我一样也在关注 AI、效率工具和内容生产，这几条信息值得看一下：",
        "",
    ]
    if rewritten_points:
        note_parts.extend(rewritten_points)
        note_parts.append("")
    elif bullet_lines:
        note_parts.extend(bullet_lines)
        note_parts.append("")
    note_parts.extend(
        [
            "我的感受：",
            make_takeaway_line(short_points, style="xiaohongshu"),
            "",
            make_cta_line(style="xiaohongshu"),
            "",
            _format_tags(tags),
        ]
    )

    return make_draft(
        platform="xiaohongshu",
        title=title_candidates[0],
        summary=opening,
        body_markdown="\n".join(note_parts),
        tags=tags[:6],
        title_candidates=title_candidates,
        warnings=[
            "小红书暂无稳定官方直发能力，建议人工发布。",
            "正式发布前建议补 3 到 5 张配图或卡片封面。",
            "内容语气可再口语化，减少资讯摘要感。",
        ],
        manual_checklist=[
            "补封面图和配图",
            "把首段改得更口语化、更生活化",
            "检查标签是否符合账号定位",
        ],
        cover_suggestions=make_cover_suggestions(style="xiaohongshu", title=title),
        image_prompts=make_image_prompts(style="xiaohongshu", title=title, points=short_points),
        comment_suggestions=make_comment_suggestions(style="xiaohongshu", points=short_points),
        engagement_prompts=make_engagement_prompts(style="xiaohongshu"),
    )
