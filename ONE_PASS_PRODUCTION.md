# One-Pass Production Checklist

这份清单是《龙虾头条》《龙虾心声》《龙虾故事》《龙虾人物》四档播客的共用生产 SOP。目标是下一期尽量一次走通，避免重复 TTS、半发布、RSS metadata 错误，以及 Podcast 已上线但文字版遗漏的情况。

## 1. Canonical 先天 TTS-ready
- 定稿就是 Podcast 与文字版共用 canonical，不再派生朗读版或文章改写版。
- 数字、金额、百分比、年份、人名、英文缩写在 FREEZE 前做 spoken-form pass；连续数字属于一个语义单元，禁止因排版或预处理拆开。
- 空行只表示真的需要明显长停顿/转场；普通短停顿靠标点和引擎 prosody。不要为了视觉强调多分段。
- 调长长停顿优先改 segmented synthesis 的 paragraph pause，不用重复/奇怪标点 hack。

## 2. Voice/profile 必须显式确定
- 每档以 repo voice profile 为 source of truth，不凭记忆猜参数。
- 多 profile 节目每期显式声明 profile；Preview 禁止硬编码 default。
- 新 voice/endpoint/授权异常先做极短 smoke test；11200 LiccCheck 优先检查 voice/private capability/APPID entitlement。

## 3. Draft PR 是唯一 staging boundary
- Preview 只由 PR 更新触发，不同时监听 build push + PR。
- `concurrency + cancel-in-progress: true`，连续改稿只保留最新 Preview。
- Preview 不写 R2/RSS/文字站。
- Audio QA 批准具体 artifact；记录 run_id、artifact_name、audio_filename、SHA256。

## 4. “发布”是 Podcast + 文字版的统一动作
- **用户说“发布”时，默认语义不是只发布 Podcast，而是一次完整发布：approved artifact → merge → Podcast/R2/RSS → 同步 canonical 到对应文字站 → Pages deploy → 双端 VERIFY。**
- 除非用户明确说“只发布 Podcast”或“只发布文字版”，否则不得省略任何一端。
- Podcast 与文字版可以由不同 workflow / repo 执行，但它们属于同一次发布事务；执行时保持单一路径、按顺序推进，不并行重复写同一资源。
- **只有 Podcast 和文字版两端都完成并通过 VERIFY，才允许向用户报告“发布完成”。**
- 如果 Podcast 已成功但文字版失败/排队/未验证，必须报告“Podcast 已发布，文字版未完成/待验证”，不得简称为“已发布”。反之亦然。
- 任一端失败时，不盲目重复另一端已经成功的有副作用步骤；只修复失败的那一端，并继续最终 VERIFY。

## 5. 发布只复用 approved artifact
- 新一期走常驻 `Publish Approved Artifact` + request JSON。
- request 锁定 run_id / artifact_name / audio_filename / SHA256 / slug / title / description / article_url / prefix。
- 发布前验证 Secrets、GUID、episode number、SHA256、MP3 非空、ffprobe 真时长、文件字节数。
- metadata validation 全通过后才允许 R2/RSS mutation；失败 fail closed。
- 禁用 `SECONDS` 特殊变量；使用 `AUDIO_SECONDS`。复杂逻辑放 Python，不在 YAML command substitution 中嵌 heredoc。

## 6. 新一期与重制是两条流程
- 已存在 GUID 禁止走 normal publish。
- 重制走 `replace-*.json` + `Replace Approved Episode Audio`；GUID/title/article/R2 URL 不变，只替换 approved MP3，并更新 length/duration。
- 覆盖 R2 前备份旧对象；RSS push 失败必须恢复旧 R2。

## 7. 文字版发布与 VERIFY
- 文字 repo source commit 不等于线上已发布；Pages 是发布链路的一部分，不只是可选验证。
- **文字版正文必须逐字使用最终批准的 canonical 口播稿原文，禁止摘要、改写、二次生成或删节。** 网页只允许额外增加 front matter、音频播放器、备用音频链接等展示层内容。
- 发布前必须验证 `web_article_body == approved_canonical_text`；不一致直接 fail closed。
- `draft: false`，播放器与 enclosure 指向同一个 R2 object。
- Hugo front matter `date` 不得晚于实际 build 时间；建议实际当前时间或安全回拨 1–2 分钟，避免被 Hugo 当 future content 跳过。
- VERIFY：source entry → Pages deployment success → article URL → 首页/列表 entry。
- source 正确但 Pages 未更新时只安全 retrigger Pages，不重复文章/Podcast 发布。

## 8. 最终 VERIFY
`canonical ✓ → preview artifact ✓ → audio QA ✓ → approved SHA ✓ → merge ✓ → R2 ✓ → podcast RSS ✓ → duration/length ✓ → text source = canonical verbatim ✓ → Pages ✓ → online article/list ✓`

**以上全部打勾才是“发布完成”。** Workflow success 不是最终成功定义；生产端实际可见且 metadata 一致才算成功。

## 9. 操作纪律
- 每个有副作用步骤只走一条明确路径，不并行写同一资源。
- 不盲目 rerun；先判断失败发生在副作用前还是后。
- 临时排障 workflow 用完删除；长期只保留 Preview / Publish Approved Artifact / Replace Approved Episode Audio 三类通用入口。
