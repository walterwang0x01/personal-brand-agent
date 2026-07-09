"""统一文章与平台稿件结构。"""

from __future__ import annotations

from typing import Any


EXPORT_ONLY_PLATFORMS = {"wechat", "juejin", "zhihu", "xiaohongshu", "weibo"}


def _normalize_tags(tags: list[str] | None) -> list[str]:
    if not tags:
        return []
    seen: list[str] = []
    for tag in tags:
        clean = str(tag).strip()
        if clean and clean not in seen:
            seen.append(clean)
    return seen


def build_platform_draft(
    *,
    platform: str,
    title: str,
    summary: str,
    body_markdown: str,
    tags: list[str] | None = None,
    title_candidates: list[str] | None = None,
    warnings: list[str] | None = None,
    manual_checklist: list[str] | None = None,
    cover_suggestions: list[str] | None = None,
    image_prompts: list[str] | None = None,
    comment_suggestions: list[str] | None = None,
    engagement_prompts: list[str] | None = None,
) -> dict[str, Any]:
    return {
        "platform": platform,
        "title": title.strip(),
        "title_candidates": title_candidates or [title.strip()],
        "summary": summary.strip(),
        "body_markdown": body_markdown.strip(),
        "tags": _normalize_tags(tags),
        "warnings": warnings or [],
        "manual_checklist": manual_checklist or [],
        "cover_suggestions": cover_suggestions or [],
        "image_prompts": image_prompts or [],
        "comment_suggestions": comment_suggestions or [],
        "engagement_prompts": engagement_prompts or [],
    }


def build_canonical_article(
    *,
    article_id: str,
    title: str,
    date: str,
    tags: list[str] | None = None,
    summary: str = "",
    body_markdown: str = "",
    source_type: str = "manual",
    source_briefing: str = "",
    source_topic: str = "",
    key_points: list[str] | None = None,
    references: list[str] | None = None,
    twitter_thread: list[str] | None = None,
    platform_drafts: dict[str, dict[str, Any]] | None = None,
    publish_pack_path: str = "",
    portfolio_url: str = "",
    extra_fields: dict[str, Any] | None = None,
) -> dict[str, Any]:
    article = {
        "id": article_id,
        "title": title.strip(),
        "date": date,
        "tags": _normalize_tags(tags),
        "excerpt": summary.strip()[:200],
        "summary": summary.strip(),
        "body": body_markdown.strip(),
        "body_markdown": body_markdown.strip(),
        "source_type": source_type,
        "source_briefing": source_briefing,
        "source_topic": source_topic,
        "key_points": key_points or [],
        "references": references or [],
        "twitter_thread": twitter_thread or [],
        "platform_drafts": platform_drafts or {},
        "publish_pack_path": publish_pack_path,
        "portfolio_url": portfolio_url,
    }
    if extra_fields:
        article.update(extra_fields)
    return article


def ensure_article_schema(article: dict[str, Any]) -> dict[str, Any]:
    """补齐旧文章对象缺失字段，兼容现有数据。"""
    normalized = dict(article)
    title = str(normalized.get("title", "")).strip()
    body_markdown = str(
        normalized.get("body_markdown")
        or normalized.get("body")
        or normalized.get("excerpt")
        or ""
    ).strip()
    summary = str(normalized.get("summary") or normalized.get("excerpt") or "").strip()
    normalized["title"] = title
    normalized["tags"] = _normalize_tags(normalized.get("tags"))
    normalized["excerpt"] = summary[:200]
    normalized["summary"] = summary
    normalized["body"] = body_markdown
    normalized["body_markdown"] = body_markdown
    normalized.setdefault("source_type", "manual")
    normalized.setdefault("source_briefing", "")
    normalized.setdefault("source_topic", "")
    normalized.setdefault("key_points", [])
    normalized.setdefault("references", [])
    normalized.setdefault("twitter_thread", [])
    normalized.setdefault("platform_drafts", {})
    normalized.setdefault("publish_pack_path", "")
    normalized.setdefault("portfolio_url", "")
    return normalized
