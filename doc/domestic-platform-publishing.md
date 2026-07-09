# 国内平台半自动分发

本文说明 `personal-brand-agent` 第一阶段如何支持 `公众号 / 掘金 / 知乎 / 小红书 / 微博` 的半自动分发。

## 设计原则

- 不依赖不稳定的网页登录态或 Cookie 直发
- 保留现有 `X + Postiz` 自动发布链路
- 国内平台优先导出可审阅、可复制、可追踪的发布包
- 如果存在可用 LLM，则优先进行平台化重写；若模型不可用或报错，自动回退到规则重写

## 支持的平台

### 自动发布

- `x`
- `linkedin`
- `bluesky`
- `medium`
- 其他已在 Postiz 中绑定的平台

### 半自动发布

- `wechat`
- `juejin`
- `zhihu`
- `xiaohongshu`
- `weibo`

## 使用方式

### 1. 从简报生成国内平台发布包

```bash
cd /Users/administrator/PycharmProjects/personal-brand-agent
.venv/bin/python -m brand_agent.cli publish-briefing -t ai-agent -p wechat,juejin,zhihu,xiaohongshu,weibo
```

### 2. 对已有文章导出发布包

```bash
.venv/bin/python -m brand_agent.cli render-domestic -a latest -p wechat,juejin,zhihu,xiaohongshu,weibo
```

### 3. 预览单个平台稿件

```bash
.venv/bin/python -m brand_agent.cli preview-pack -a latest -p wechat
```

## LLM 重写与回退

- 已配置可用模型时：
  - 小红书、微博、知乎、掘金、公众号会优先尝试平台化 LLM 重写
- 未配置模型时：
  - 自动使用本地规则重写
- 模型调用失败时：
  - 终端打印 fallback 日志
  - 继续产出可用稿件，不会中断发布包导出

## 产物目录

发布包默认导出到：

```text
output/publish-packs/<article-id>/
```

目录内包含：

- `wechat.md`
- `juejin.md`
- `zhihu.md`
- `xiaohongshu.md`
- `weibo.md`
- `meta.json`
- `README.md`

## 每个平台会生成什么

### 公众号

- 长文版标题候选
- 导语
- 结论摘要
- 正文
- 参考链接
- 封面与人工检查建议

### 掘金

- 技术文章风格标题
- 更偏工程内容的开头
- Markdown 正文
- 标签与人工检查建议

### 知乎

- 问题化标题
- 观点先行的导语
- 更适合讨论的正文结构
- 人工补观点的建议

### 小红书

- 更口语化的标题候选
- 短笔记式正文
- 标签建议
- 配图与封面建议

### 微博

- 更短的导流型正文
- 热点化标题候选
- 话题标签建议
- 配图建议

## 人工发布建议

### 公众号

- 在后台补充封面、摘要和排版
- 增加 1 段个人判断
- 检查外链是否需要改成“阅读原文”

### 掘金

- 压缩标题长度
- 调整标签
- 如内容偏资讯，补工程视角分析

### 知乎

- 补充观点、反例或经验
- 把首段改得更像回答
- 减少营销式 CTA

### 小红书

- 补 3 到 5 张图文卡片或配图
- 把首段改得更像日常分享
- 检查标签是否和账号人设一致

### 微博

- 补单张信息卡片图或配图
- 压缩句子长度，提升扫读性
- 检查话题标签是否过多

## 当前边界

- 第一阶段不提供公众号/掘金/知乎/小红书/微博自动投稿
- 不提供视频号自动化
- 后续如果某个平台需要自动投稿，应基于现有发布包和平台稿件抽象继续扩展
