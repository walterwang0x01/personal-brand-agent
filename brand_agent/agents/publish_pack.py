"""国内平台半自动发布包导出。"""

from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Any

from brand_agent.article_schema import EXPORT_ONLY_PLATFORMS, ensure_article_schema
from brand_agent.renderers import render_platform_draft


def _load_article(article_id: str) -> tuple[dict[str, Any], Path]:
    if article_id == "latest":
        articles_dir = Path("data/articles")
        files = sorted(articles_dir.glob("*.json"), reverse=True)
        if not files:
            raise FileNotFoundError("未找到任何文章")
        path = files[0]
    else:
        path = Path(f"data/articles/{article_id}.json")
        if not path.exists():
            raise FileNotFoundError(f"文章未找到: {article_id}")

    return ensure_article_schema(json.loads(path.read_text(encoding="utf-8"))), path


def _pack_readme(article: dict[str, Any], platforms: list[str]) -> str:
    title = article.get("title", "")
    lines = [
        f"# {title} 发布包",
        "",
        "## 包含平台",
        "",
    ]
    for platform in platforms:
        lines.append(f"- {platform}")
    lines.extend(
        [
            "",
            "## 使用方式",
            "",
            "1. 先阅读对应平台稿件文件。",
            "2. 根据 `meta.json` 里的检查项补充标题、摘要和个人观点。",
            "3. 在各平台后台粘贴、排版并人工终审后发布。",
        ]
    )
    return "\n".join(lines)


def _append_asset_summary(lines: list[str], platform: str, draft: dict[str, Any]) -> None:
    lines.extend([f"", f"## {platform} 素材建议", ""])
    for label, key in [
        ("封面建议", "cover_suggestions"),
        ("配图提示词", "image_prompts"),
        ("首评建议", "comment_suggestions"),
        ("互动建议", "engagement_prompts"),
    ]:
        values = draft.get(key, [])
        if values:
            lines.append(f"### {label}")
            lines.append("")
            for value in values:
                lines.append(f"- {value}")
            lines.append("")
    artifacts = _platform_artifacts(platform, draft)
    if artifacts:
        lines.append("### 导出文件")
        lines.append("")
        for filename in artifacts:
            lines.append(f"- {platform}/{filename}")
        lines.append("")


def _platform_artifacts(platform: str, draft: dict[str, Any]) -> dict[str, str]:
    artifacts: dict[str, str] = {}
    body = draft.get("body_markdown", "").strip()
    titles = draft.get("title_candidates", [])
    cover = draft.get("cover_suggestions", [])
    image_prompts = draft.get("image_prompts", [])
    comments = draft.get("comment_suggestions", [])
    engagement = draft.get("engagement_prompts", [])

    if platform == "weibo":
        artifacts["weibo_post.txt"] = body + "\n"
        if comments:
            artifacts["weibo_comment.txt"] = "\n".join(comments) + "\n"
    elif platform == "wechat":
        artifacts["wechat_title.txt"] = (titles[0] if titles else draft.get("title", "")) + "\n"
        artifacts["wechat_summary.txt"] = draft.get("summary", "").strip() + "\n"
        if cover:
            artifacts["wechat_cover.txt"] = "\n".join(cover) + "\n"
    elif platform == "xiaohongshu":
        artifacts["xiaohongshu_caption.txt"] = body + "\n"
        if image_prompts:
            artifacts["xiaohongshu_image_script.txt"] = "\n".join(image_prompts) + "\n"
    elif platform == "zhihu":
        artifacts["zhihu_title.txt"] = (titles[0] if titles else draft.get("title", "")) + "\n"
        if comments:
            artifacts["zhihu_comment_seed.txt"] = "\n".join(comments) + "\n"
    elif platform == "juejin":
        artifacts["juejin_title.txt"] = (titles[0] if titles else draft.get("title", "")) + "\n"
        if engagement:
            artifacts["juejin_discussion_seed.txt"] = "\n".join(engagement) + "\n"

    if cover:
        artifacts[f"{platform}_cover_suggestions.txt"] = "\n".join(cover) + "\n"
    if image_prompts:
        artifacts[f"{platform}_image_prompts.txt"] = "\n".join(image_prompts) + "\n"
    if comments:
        artifacts[f"{platform}_comment_suggestions.txt"] = "\n".join(comments) + "\n"
    if engagement:
        artifacts[f"{platform}_engagement_prompts.txt"] = "\n".join(engagement) + "\n"
    return artifacts


def export_publish_pack(
    article_id: str,
    platforms: list[str],
    *,
    persist_article: bool = True,
) -> dict[str, Any]:
    article, article_path = _load_article(article_id)
    target_platforms = [p for p in platforms if p in EXPORT_ONLY_PLATFORMS]
    if not target_platforms:
        raise ValueError("没有可导出的国内平台，请使用 wechat/juejin/zhihu/xiaohongshu/weibo")

    pack_dir = Path("output/publish-packs") / article["id"]
    if pack_dir.exists():
        shutil.rmtree(pack_dir)
    pack_dir.mkdir(parents=True, exist_ok=True)

    drafts: dict[str, dict[str, Any]] = dict(article.get("platform_drafts", {}))
    exported_files: dict[str, str] = {}
    meta: dict[str, Any] = {
        "article_id": article["id"],
        "title": article.get("title", ""),
        "source_type": article.get("source_type", ""),
        "source_briefing": article.get("source_briefing", ""),
        "platforms": {},
    }

    for platform in target_platforms:
        draft = render_platform_draft(platform, article)
        drafts[platform] = draft
        platform_dir = pack_dir / platform
        platform_dir.mkdir(parents=True, exist_ok=True)

        output_path = platform_dir / f"{platform}.md"
        output_path.write_text(draft["body_markdown"] + "\n", encoding="utf-8")
        exported_files[platform] = str(output_path)
        artifact_files: dict[str, str] = {}
        for filename, content in _platform_artifacts(platform, draft).items():
            artifact_path = platform_dir / filename
            artifact_path.write_text(content, encoding="utf-8")
            artifact_files[filename] = str(artifact_path)
        meta["platforms"][platform] = {
            "title": draft["title"],
            "title_candidates": draft.get("title_candidates", []),
            "tags": draft.get("tags", []),
            "warnings": draft.get("warnings", []),
            "manual_checklist": draft.get("manual_checklist", []),
            "cover_suggestions": draft.get("cover_suggestions", []),
            "image_prompts": draft.get("image_prompts", []),
            "comment_suggestions": draft.get("comment_suggestions", []),
            "engagement_prompts": draft.get("engagement_prompts", []),
            "artifact_files": artifact_files,
        }

    readme_lines = [_pack_readme(article, target_platforms)]
    for platform in target_platforms:
        _append_asset_summary(readme_lines, platform, drafts[platform])

    meta_path = pack_dir / "meta.json"
    meta_path.write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
    readme_path = pack_dir / "README.md"
    readme_path.write_text("\n".join(readme_lines).rstrip() + "\n", encoding="utf-8")
    zip_path = shutil.make_archive(
        str(pack_dir.parent / pack_dir.name),
        "zip",
        root_dir=pack_dir.parent,
        base_dir=pack_dir.name,
    )

    if persist_article:
        article["platform_drafts"] = drafts
        article["publish_pack_path"] = str(pack_dir)
        article_path.write_text(json.dumps(article, ensure_ascii=False, indent=2), encoding="utf-8")

    return {
        "success": True,
        "article_id": article["id"],
        "pack_dir": str(pack_dir),
        "files": exported_files,
        "meta_path": str(meta_path),
        "readme_path": str(readme_path),
        "zip_path": zip_path,
    }
