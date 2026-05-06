# EmojiReactionLike

AstrBot 插件, 允许 bot 在接入 NapCat 平台时对 QQ 消息添加表情反应 (Reaction)。可在回复时或正则匹配关键字触发。

## 功能

- **/react [emoji_id]** - 回复一条消息并发送此指令, 对被回复的消息添加表情反应。不指定 emoji_id 时使用第一条反应规则中的表情。
- **/reactlist** - 列出常用的 QQ 表情反应 ID 供参考。
- **/reactconfig** - 查看当前插件配置 (仅管理员)。
- **自动反应** - 根据配置的正则规则, 自动对匹配的消息添加表情反应。
- **LLM 输出反应** - 拦截 LLM 回复, 通过正则匹配提取标记并执行反应, 同时从回复中移除标记文本。

## 配置项

所有配置可在 AstrBot WebUI 的插件配置页面中修改。

| 配置项 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| auto_react | bool | false | 是否启用自动表情反应 |
| react_rules | template_list | [] | 反应规则列表, 每条规则包含 emoji_ids (表情ID列表) 和 regex_list (触发正则列表) |
| react_scope | string | all | 自动反应范围: all / group / private |
| llm_react_enabled | bool | false | 是否启用 LLM 输出表情反应 |
| enable_msg_id_prefix | bool | true | 是否为 LLM 注入消息 ID 前缀 |
| llm_react_regex | string | `\[react:([^\]]+)\]` | 匹配 LLM 简单反应标记的正则 (反应当前消息) |
| llm_react_targeted_regex | string | `\[react:([^\],]+),id:([^\]]+)\]` | 匹配 LLM 指定目标反应标记的正则 (反应指定消息) |

### react_rules 规则说明

每条规则包含两个字段:

- **emoji_ids**: 表情 ID 列表。QQ 原生表情填数字 (如 `76` 表示赞), Unicode emoji 直接填字符, 插件会自动用 `ord()` 转换。
- **regex_list**: 触发正则表达式列表。消息匹配列表中任意正则时触发反应。留空表示对所有消息反应。

### LLM 输出反应用法

开启 `llm_react_enabled` 后, 插件会自动在用户消息发送给 LLM 前添加 `msg_id:xxx` 前缀, 使 LLM 可以感知消息 ID。

LLM 输出支持两种反应格式:

| 格式 | 作用 |
|------|------|
| `[react:表情ID]` | 对当前用户消息添加表情反应 |
| `[react:表情ID,id:消息ID]` | 对指定 msg_id 的消息添加表情反应 |

两种格式的正则表达式均可在配置中自定义。

#### 人设提示词参考

在人格提示词中告知 LLM 可以使用这些格式, 例如:

```
用户消息会以 msg_id:xxx 开头, 这是消息的唯一标识。
当你想对用户发送的消息进行表情反应时, 可以在回复中插入反应标记:
- [react:表情ID] 对当前消息反应
- [react:表情ID,id:消息ID] 对指定消息反应
你可以插入多个标记来添加多个反应。
可用的QQ数字表情ID: [react:448]代表“火球术” [react:447]代表“点赞” [react:446]代表“摧心术” [react:445]代表“魅惑怪物” [react:444]代表“666” [react:443]代表“死亡一指” [react:442]代表“鸽子跳舞”
也可以直接使用Unicode emoji字符, 如 [react:😭]
```

插件会自动提取标记、执行反应, 并从最终回复中移除标记文本。

## 平台支持

仅支持 aiocqhttp 平台 (NapCat / Lagrange 等 OneBot v11 实现)。
