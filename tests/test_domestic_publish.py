import json
from pathlib import Path

from brand_agent.agents.distributor import distribute_article
from brand_agent.agents.publish_pack import export_publish_pack
from brand_agent.article_schema import build_canonical_article, ensure_article_schema
from brand_agent.config import settings


def _write_article(tmp_path: Path, article_id: str = "sample-article") -> None:
    article = build_canonical_article(
        article_id=article_id,
        title="AI Agent 简报",
        date="2026-07-09",
        tags=["ai-agent", "briefing"],
        summary="今天最重要的是模型产品化和工具链收敛。",
        body_markdown="## 正文\n\n这是一个测试正文。",
        source_type="briefing",
        source_briefing="/tmp/source.md",
        source_topic="ai-agent",
        key_points=["模型产品化加速", "工具链继续收敛"],
        references=["https://example.com/a", "https://example.com/b"],
        twitter_thread=["thread 1", "thread 2"],
    )
    articles_dir = tmp_path / "data" / "articles"
    articles_dir.mkdir(parents=True, exist_ok=True)
    (articles_dir / f"{article_id}.json").write_text(
        json.dumps(article, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def test_ensure_article_schema_backfills_legacy_fields():
    legacy = {
        "id": "legacy",
        "title": "旧文章",
        "date": "2026-07-09",
        "tags": ["foo", "foo"],
        "excerpt": "旧摘要",
        "body": "旧正文",
    }
    normalized = ensure_article_schema(legacy)
    assert normalized["summary"] == "旧摘要"
    assert normalized["body_markdown"] == "旧正文"
    assert normalized["platform_drafts"] == {}
    assert normalized["tags"] == ["foo"]


def test_export_publish_pack_generates_domestic_files(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    _write_article(tmp_path)

    result = export_publish_pack(
        "sample-article",
        ["wechat", "juejin", "zhihu", "xiaohongshu", "weibo"],
    )

    assert Path(result["pack_dir"]).exists()
    assert Path(result["files"]["wechat"]).exists()
    assert Path(result["files"]["juejin"]).exists()
    assert Path(result["files"]["zhihu"]).exists()
    assert Path(result["files"]["xiaohongshu"]).exists()
    assert Path(result["files"]["weibo"]).exists()
    meta = json.loads(Path(result["meta_path"]).read_text(encoding="utf-8"))
    assert meta["article_id"] == "sample-article"
    assert set(meta["platforms"].keys()) == {
        "wechat",
        "juejin",
        "zhihu",
        "xiaohongshu",
        "weibo",
    }


def test_distribute_article_mixes_export_and_postiz_result(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    _write_article(tmp_path)
    monkeypatch.setattr(settings, "postiz_url", "")
    monkeypatch.setattr(settings, "postiz_api_key", "")

    result = distribute_article("sample-article", ["wechat", "x"])

    assert result["wechat"]["success"] is True
    assert result["wechat"]["mode"] == "export_bundle"
    assert result["x"]["success"] is False
    assert result["x"]["mode"] == "auto_publish"
