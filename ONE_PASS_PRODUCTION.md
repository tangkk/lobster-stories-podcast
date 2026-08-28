# One-Pass Production Checklist

这份清单是《龙虾头条》《龙虾心声》《龙虾故事》《龙虾人物》四档播客的共用生产 SOP。目标是下一期尽量一次走通，避免重复 TTS、半发布、RSS metadata 错误，以及文字版与 Podcast 发布阶段混淆。

## 1. Canonical 先天 TTS-ready
- 定稿就是 Podcast 与文字版共用 canonical，不再派生朗读版或文章改写版。
- 数字、金额、百分比、年份、人名、英文缩写在 FREEZE 前做 spoken-form pass；连续数字属于一个语义单元，禁止因排版或预处理拆开。
- 空行只表示真的需要明显长停顿/转场；普通短停顿靠标点和引擎 prosody。不要为了视觉强调多分段。

## 2. Voice/profile 必须显式确定
- 每档以 repo voice profile 为 source of truth，不凭记忆猜参数。
- 多 profile 节目每期显式声明 profile；Preview 禁止硬编码 default。

## 3. Draft PR 是唯一 staging boundary
- Preview 只由 PR 更新触发。
- Preview 阶段只生成 TTS artifact，不写正式 Podcast 的 R2/RSS。
- Audio QA 批准具体 artifact；记录 run_id、artifact_name、audio_filename、SHA256。

## 4. 固定交付节奏：Preview 试听时发布文字版
标准流程固定为：

`开始制作 → canonical 定稿 → TTS Preview → 用户收到 Preview 完成通知 → 用户要求“发来听一下” → 发送试听 MP3 + 发布带 Preview 音频播放器的文字版 → 用户试听确认 → 发布 Podcast`

- **用户说“发来听一下”时，必须在发送 Preview MP3 的同时发布该期文字版。**
- **文字版必须嵌入当前这次 TTS Preview 的音频播放器，并提供可直接访问的备用音频链接。**
- Preview 音频必须使用独立 preview R2 路径；不得写入正式 Podcast RSS，不得冒充正式 enclosure。
- 文字版正文逐字使用当前 Preview 对应 canonical，禁止摘要、改写、删节。
- 此阶段只发布文字站与 preview 音频；**不得发布正式 Podcast，不得写正式 Podcast RSS。**
- 文字站发布后完成 Pages VERIFY，并验证线上文章实际包含播放器和当前 preview audio URL。
- 用户明确说“发布”或等价确认后，才进入正式 Podcast 发布。

## 5. “发布”默认指最终 Podcast 发布
- 用户说“发布”，默认批准当前试听 artifact 并发布正式 Podcast。
- 正式 Podcast 必须复用用户刚试听并批准的 artifact，不重新 TTS。
- 正式 Podcast 发布后，将文字页播放器/音频链接安全切换到最终 approved R2 音频 URL；正文不得改变。
- 若 Preview 后 canonical 有任何修改，必须重新 Preview，并同步更新文字版和 Preview 音频后再请求最终批准。

## 6. 发布只复用 approved artifact
- 新一期走常驻 `Publish Approved Artifact` + request JSON。
- request 锁定 run_id / artifact_name / audio_filename / SHA256 / slug / title / description / article_url / prefix。
- 发布前验证 GUID、episode number、SHA256、MP3、ffprobe 真时长和文件字节数。

## 7. 新一期与重制是两条流程
- 已存在 GUID 禁止走 normal publish。
- 重制走 replace workflow；GUID/title/article/R2 URL 不变，只替换 approved MP3，并更新 length/duration。

## 8. 文字版发布与 VERIFY
- **文字版正文必须逐字使用当前 Preview 对应的 canonical 口播稿原文。**
- **Preview 阶段文字版必须带当前 Preview 音频播放器与备用链接。** 缺播放器、URL 不匹配、音频不可访问都视为文字版发布失败。
- Preview 阶段文字版不依赖正式 Podcast enclosure；Preview 音频走独立 preview R2 object，不得为了等待正式音频而延迟文字发布。
- 正式 Podcast 发布后，可安全更新播放器/音频链接指向最终 approved R2 object；正文不得改变。
- `draft: false`；Hugo 构建使用 `--buildFuture`，避免时区导致文章静默过滤。
- VERIFY：source entry → preview audio URL reachable → generated page contains audio player → Pages deployment success → article URL → 首页/列表 entry。

## 9. 最终 VERIFY
Preview/文字阶段：`canonical ✓ → preview artifact ✓ → Preview MP3 发给用户 ✓ → preview R2 ✓ → text = canonical verbatim ✓ → player uses current preview audio ✓ → Pages ✓ → online article/list ✓`

Podcast 阶段：`user approval ✓ → approved SHA ✓ → final R2 ✓ → RSS ✓ → duration/length ✓ → text still matches canonical ✓ → text player switched to final audio ✓`

## 10. 操作纪律
- 每个有副作用步骤只走一条明确路径，不并行写同一资源。
- 不盲目 rerun；先判断失败发生在副作用前还是后。
