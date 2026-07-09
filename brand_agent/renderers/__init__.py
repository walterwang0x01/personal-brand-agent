"""平台稿件渲染入口。"""

from __future__ import annotations

from typing import Any

from brand_agent.renderers.juejin import render_juejin
from brand_agent.renderers.weibo import render_weibo
from brand_agent.renderers.wechat import render_wechat
from brand_agent.renderers.xiaohongshu import render_xiaohongshu
from brand_agent.renderers.zhihu import render_zhihu


DOMESTIC_RENDERERS = {
    "wechat": render_wechat,
    "juejin": render_juejin,
    "zhihu": render_zhihu,
    "xiaohongshu": render_xiaohongshu,
    "weibo": render_weibo,
}


def render_platform_draft(platform: str, article: dict[str, Any]) -> dict[str, Any]:
    renderer = DOMESTIC_RENDERERS.get(platform)
    if renderer is None:
        raise ValueError(f"未找到平台渲染器: {platform}")
    return renderer(article)
