"""知乎稿件渲染。"""

from __future__ import annotations

from typing import Any

from brand_agent.renderers.common import (
    concise_key_points,
    format_reference_list,
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


def render_zhihu(article: dict[str, Any]) -> dict[str, Any]:
    prepared = prepare_article(article)
    title = prepared["title"]
    summary = prepared["summary"]
    body = prepared["body_markdown"]
    key_points = prepared["key_points"]
    references = prepared["references"]
    tags = prepared["tags"]
    key_point_lines = [f"- {point}" for point in concise_key_points(key_points, max_items=4, max_len=70)]
    body_preview = "\n\n".join(
        rewrite_paragraphs_with_llm(
            title=title,
            points=key_points,
            style="zhihu",
            max_items=3,
        )
    )

    title_candidates = [
        f"{title}，这意味着什么？",
        f"如何看待 {title}？",
        f"{title} 背后有哪些值得关注的信号？",
    ]
    sections = [
        f"# {title_candidates[0]}",
        "",
        make_hook_line(title, [p[2:] for p in key_point_lines], style="zhihu"),
        "",
        "我的结论是：",
        "",
        make_takeaway_line([p[2:] for p in key_point_lines], style="zhihu"),
        "",
    ]
    if key_point_lines:
        sections.extend(["## 为什么我会这样判断", "", *key_point_lines, ""])
    sections.extend(
        [
            "## 展开说说",
            "",
            body_preview or "请补充展开分析。",
            format_reference_list(references),
            "",
            "## 最后",
            "",
            make_takeaway_line([p[2:] for p in key_point_lines], style="zhihu"),
            "",
            make_cta_line(style="zhihu"),
        ]
    )

    return make_draft(
        platform="zhihu",
        title=title_candidates[0],
        summary=summary,
        body_markdown="\n".join(part for part in sections if part is not None),
        tags=tags[:5],
        title_candidates=title_candidates,
        warnings=[
            "知乎更适合观点化表达，发布前建议加入你的判断和反例。",
            "如果内容过于像新闻摘要，建议增强“为什么重要”和“对谁有影响”。",
        ],
        manual_checklist=[
            "改成更像问题回答的开头",
            "加入个人观点或经验",
            "检查是否需要删减外链和营销式 CTA",
        ],
        cover_suggestions=make_cover_suggestions(style="zhihu", title=title),
        image_prompts=make_image_prompts(style="zhihu", title=title, points=key_points),
        comment_suggestions=make_comment_suggestions(style="zhihu", points=key_points),
        engagement_prompts=make_engagement_prompts(style="zhihu"),
    )
