# One-Pass Production Checklist

四档播客共用的生产经验，目标是下一期尽量一次走通。

## Canonical / TTS
- 定稿就是 Podcast 与文字版共用 canonical；数字、年份、人名、英文缩写在 FREEZE 前做 spoken-form pass。
- 连续数字属于一个语义单元，禁止被排版/预处理拆开。
- 空行只表示真实长停顿/转场；短停顿靠标点和 TTS prosody。调长停顿改 paragraph pause，不用奇怪标点。

## Voice/profile
- voice profile 是 source of truth；不凭记忆猜参数。
- 多 profile 节目每期必须显式声明 profile；Preview 禁止硬编码 default。
- 新 voice/endpoint/11200 授权异常先做极短 smoke test，优先查具体 voice/private capability/APPID entitlement。

## Preview
- Draft PR 是唯一 staging boundary。
- Preview 只由 PR 更新触发；不同时监听 build push + PR。
- 使用 `concurrency + cancel-in-progress: true`，连续改稿只保留最新 Preview。
- Preview 不写 R2/RSS/文字站。Audio QA 批准具体 artifact，并记录 run_id / artifact_name / audio_filename / SHA256。

## New episode publish
- 只复用 approved artifact；使用常驻 `Publish Approved Artifact` + request JSON。
- request 锁定 run_id / artifact_name / audio_filename / SHA256 / slug / title / description / article_url / prefix。
- 发布前验证 Secrets、GUID 未存在、episode number、SHA256、MP3 非空、ffprobe 真时长、bytes。
- metadata validation 后才允许 R2/RSS mutation；失败 fail closed。
- 禁止 `SECONDS` 特殊变量，改用 `AUDIO_SECONDS`；复杂逻辑用独立 Python 脚本，不把 heredoc 塞进 command substitution。

## Remake existing episode
- 已存在 GUID 禁止走 normal publish。
- 走 `replace-*.json` + `Replace Approved Episode Audio`；GUID/title/article/R2 URL 不变，只替换 approved MP3 并更新 enclosure length / itunes:duration。
- 覆盖 R2 前备份旧对象；RSS commit/push 失败必须恢复旧 R2。

## Text site / Pages
- 文字 repo source commit 不等于线上已发布。
- **文字版正文必须逐字使用最终批准的 canonical 口播稿原文，禁止摘要、改写、二次生成或删节。** 网页只允许额外增加 front matter、音频播放器、备用音频链接等展示层内容。
- 发布前必须验证 `web_article_body == approved_canonical_text`；不一致直接 fail closed。
- 文章必须 `draft: false`，播放器与 podcast enclosure 指向同一 R2 object。
- Hugo front matter `date` 不得晚于实际 build 时间；建议使用实际当前时间或回拨 1–2 分钟，避免被 Hugo 当 future content 跳过。
- VERIFY：source entry → Pages deployment success → article URL → 首页/列表 entry。source 正确但 Pages 未更新时只 retrigger Pages，不重复发布 Podcast。

## Final VERIFY
`canonical ✓ → preview artifact ✓ → audio QA ✓ → approved SHA ✓ → merge ✓ → R2 ✓ → podcast RSS ✓ → duration/length ✓ → text source = canonical verbatim ✓ → Pages ✓ → online article/list ✓`

Workflow success 不是最终成功；生产端实际可见且 metadata 一致才算成功。

## Operation discipline
- 每个有副作用步骤只走一条明确路径，不并行写同一资源。
- 不盲目 rerun；先判断失败发生在副作用前还是后。
- 临时排障 workflow 用完删除；长期只保留 Preview / Publish Approved Artifact / Replace Approved Episode Audio 三类通用入口。
