"""掘金稿件渲染。"""

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


def render_juejin(article: dict[str, Any]) -> dict[str, Any]:
    prepared = prepare_article(article)
    title = prepared["title"]
    summary = prepared["summary"]
    body = prepared["body_markdown"]
    key_points = prepared["key_points"]
    references = prepared["references"]
    tags = prepared["tags"]
    key_point_lines = [f"- {point}" for point in concise_key_points(key_points, max_items=5, max_len=68)]
    opening = "这篇内容不是完整新闻搬运，而是我筛过之后留下的几个工程信号。"
    body_preview = "\n".join(
        rewrite_paragraphs_with_llm(
            title=title,
            points=key_points,
            style="juejin",
            max_items=4,
        )
    )

    title_candidates = [
        title,
        f"{title}：今天有哪些值得工程师关注的变化？",
        f"{title}，我提炼出了这几个信号",
    ]
    sections = [
        f"# {title}",
        "",
        make_hook_line(title, [p[2:] for p in key_point_lines], style="juejin"),
        "",
        opening,
        "",
    ]
    if key_point_lines:
        sections.extend(["## 先说结论", "", *key_point_lines, ""])
    sections.extend(
        [
            "## 详细拆解",
            "",
            body_preview or "请补充详细内容。",
            format_reference_list(references),
            "",
            "## 写在最后",
            "",
            make_takeaway_line([p[2:] for p in key_point_lines], style="juejin"),
            "",
            make_cta_line(style="juejin"),
        ]
    )

    return make_draft(
        platform="juejin",
        title=title_candidates[0],
        summary=opening,
        body_markdown="\n".join(part for part in sections if part is not None),
        tags=tags[:5],
        title_candidates=title_candidates,
        warnings=[
            "掘金标题建议更问题化或更具体，发布前可再压缩 5 到 10 个字。",
            "如果正文偏资讯摘要，建议补 1 段工程视角分析。",
        ],
        manual_checklist=[
            "确认标题是否足够技术导向",
            "补充标签与系列归档",
            "检查 Markdown 标题层级和引用格式",
        ],
        cover_suggestions=make_cover_suggestions(style="juejin", title=title),
        image_prompts=make_image_prompts(style="juejin", title=title, points=key_points),
        comment_suggestions=make_comment_suggestions(style="juejin", points=key_points),
        engagement_prompts=make_engagement_prompts(style="juejin"),
    )
