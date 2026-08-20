# 龙虾故事

## Editorial Memory

深夜情感故事播客。每期聚焦一个具体的人和一段关系或经历；从普通生活里寻找隐秘但有共鸣的瞬间，重视细节、留白和情绪余韵。表达克制、安静、有画面感；不讲大道理、不灌鸡汤、不强行总结人生意义。候选选题要保持发散，避免近期连续使用高度相似的场景、关系和叙事视角。

## Workflow

**IDEA → WRITE → FREEZE → PREFLIGHT → BUILD → LISTEN → PUBLISH → VERIFY**。选题和故事先在对话中打磨；用户确认的定稿就是 TTS-ready canonical 稿，同时用于文字版与 Podcast。定稿前不进入 GitHub 发布流程；正式发布前再次确认。

## Canonical / TTS-ready

短句、自然段和留白优先；少用括号、分号、连续破折号。数字、英文、人名在定稿时处理成自然可朗读形式。正文与文字版 canonical 内容逐字一致。本节目不做冗长开场/结束介绍，不靠旁白强行拔高；目标约十分钟，但内容完整性和叙事节奏优先于机械凑时长。

## Voice & Pause Baseline

使用讯飞；默认 profile：`voice_profiles/default.json`，当前为 `x6_wennuancixingnansheng_mini`、speed 42、volume 52、pitch 47。长文正式主路径为 **自然段分段合成 + 段间约 350ms 静音**。自然段停顿必须显著长于普通句内/句末停顿；过长段落才按句号/问号/感叹号拆分，绝不拆断一句话，经验上约 240–420 字/segment。使用 `xfyun_segmented_run.py`；单段脚本仅用于短样片/排障。

TTS 前检查讯飞三个环境变量；首次新稿/新环境先跑第一段最小样本。350ms 是经过旧 SOP 实际使用的 baseline，可根据 Audio QA 微调，但不要通过添加奇怪标点修引擎停顿。

## QA & Publishing Guardrails

Preflight 检查 Editorial / Facts / TTS / Metadata；Audio QA 检查发音、数字、断句、句间停顿、段间停顿、整体语速/节奏。episode number 从 feed 推导，guid、音频文件名、文章音频链接一致；RSS description 使用真实换行。发布后验证 R2、Podcast RSS、文字 RSS 和文章。

README 是当前 source of truth；旧 OpenClaw SOP 只作历史参考，本机绝对路径、旧 rss-hosting/audio、消息平台交付和逐段进度回报等规则淘汰。
