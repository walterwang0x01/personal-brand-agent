"""公众号稿件渲染。"""

from __future__ import annotations

from typing import Any

from brand_agent.renderers.common import (
    compact_text,
    concise_key_points,
    format_reference_list,
    make_comment_suggestions,
    make_cover_suggestions,
    make_draft,
    make_engagement_prompts,
    make_image_prompts,
    prepare_article,
    rewrite_paragraphs_with_llm,
)


def render_wechat(article: dict[str, Any]) -> dict[str, Any]:
    prepared = prepare_article(article)
    title = prepared["title"]
    summary = prepared["summary"]
    body = prepared["body_markdown"]
    key_points = prepared["key_points"]
    references = prepared["references"]
    tags = prepared["tags"]
    short_summary = compact_text(summary, max_len=150)
    key_point_lines = [f"- {point}" for point in concise_key_points(key_points, max_items=5, max_len=76)]
    body_preview = "\n\n".join(
        rewrite_paragraphs_with_llm(
            title=title,
            points=key_points,
            style="wechat",
            max_items=4,
        )
    ) or compact_text(body, max_len=900)

    title_candidates = [
        title,
        f"{title}：今天最值得看的 3 个变化",
        f"{title}｜给技术从业者的关键信号",
    ]
    body_parts = [
        f"# {title}",
        "",
        "## 导语",
        "",
        short_summary or "这是一篇基于最新简报整理的公众号草稿，请发布前补充你的个人判断和首图。",
        "",
    ]
    if key_point_lines:
        body_parts.extend(["## 先看结论", "", *key_point_lines, ""])
    body_parts.extend(
        [
            "## 正文",
            "",
            body_preview or "请在此补充正文内容。",
            format_reference_list(references),
            "",
            "## 发布前补充",
            "",
            "- 结合你的观点补 1 段个人判断",
            "- 替换或补充首图、封面、摘要",
            "- 检查外链是否需要转成纯文本或阅读原文",
        ]
    )

    return make_draft(
        platform="wechat",
        title=title_candidates[0],
        summary=summary,
        body_markdown="\n".join(part for part in body_parts if part is not None),
        tags=tags,
        title_candidates=title_candidates,
        warnings=[
            "公众号排版、封面图和摘要建议在后台二次调整。",
            "如包含外链，请确认是否需要保留“阅读原文”或改写为参考资料。",
        ],
        manual_checklist=[
            "补充封面图与摘要",
            "加入你的观点或结论段",
            "检查引用链接和排版间距",
        ],
        cover_suggestions=make_cover_suggestions(style="wechat", title=title),
        image_prompts=make_image_prompts(style="wechat", title=title, points=key_points),
        comment_suggestions=make_comment_suggestions(style="wechat", points=key_points),
        engagement_prompts=make_engagement_prompts(style="wechat"),
    )
