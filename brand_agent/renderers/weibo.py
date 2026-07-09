"""微博稿件渲染。"""

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


def _to_hashtags(tags: list[str]) -> str:
    if not tags:
        return "#AI观察# #效率工具#"
    items = []
    for tag in tags[:4]:
        clean = tag.strip().replace(" ", "")
        if clean:
            items.append(f"#{clean}#")
    return " ".join(items)


def render_weibo(article: dict[str, Any]) -> dict[str, Any]:
    prepared = prepare_article(article)
    title = prepared["title"]
    summary = prepared["summary"]
    key_points = prepared["key_points"]
    tags = prepared["tags"]
    bullets = concise_key_points(key_points, max_items=3, max_len=34)
    rewritten_points = rewrite_paragraphs_with_llm(
        title=title,
        points=key_points,
        style="weibo",
        max_items=2,
    )

    opening = make_hook_line(title, bullets, style="weibo")
    lines = [f"{title}", "", opening, ""]
    if rewritten_points:
        lines.extend(rewritten_points)
    else:
        for idx, item in enumerate(bullets, 1):
            lines.append(f"{idx}. {item}")
    lines.extend(
        [
            "",
            make_takeaway_line(bullets, style="weibo"),
            "",
            make_cta_line(style="weibo"),
            "",
            _to_hashtags(tags),
        ]
    )
    body = "\n".join(lines).strip()
    if len(body) > 700:
        body = body[:697] + "..."

    title_candidates = [
        f"{title}：3 个关键信号",
        f"今天这几条变化，值得关注",
        f"{title}，我看到的重点是这些",
    ]

    return make_draft(
        platform="weibo",
        title=title_candidates[0],
        summary=opening,
        body_markdown=body,
        tags=tags[:4],
        title_candidates=title_candidates,
        warnings=[
            "微博更适合短内容导流，建议人工补配图或卡片图。",
            "正式发布前建议压缩措辞，减少过长句子。",
        ],
        manual_checklist=[
            "补配图或信息卡片",
            "确认标签是否适合当前账号定位",
            "检查正文长度与可读性",
        ],
        cover_suggestions=make_cover_suggestions(style="weibo", title=title),
        image_prompts=make_image_prompts(style="weibo", title=title, points=bullets),
        comment_suggestions=make_comment_suggestions(style="weibo", points=bullets),
        engagement_prompts=make_engagement_prompts(style="weibo"),
    )
