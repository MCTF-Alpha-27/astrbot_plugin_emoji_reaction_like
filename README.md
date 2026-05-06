# EmojiReactionLike

AstrBot 插件, 允许 bot 在接入 NapCat 平台时对 QQ 消息添加表情反应 (Reaction)。可在回复时或正则匹配关键字触发。

## 功能

- **/react [emoji_id]** - 回复一条消息并发送此指令, 对被回复的消息添加表情反应。不指定 emoji_id 时使用第一条反应规则中的表情。
- **/reactlist** - 列出常用的 QQ 表情反应 ID 供参考。
- **/reactconfig** - 查看当前插件配置 (仅管理员)。
- **自动反应** - 根据配置的正则规则, 自动对匹配的消息添加表情反应。
- **LLM 函数工具** - 注册 react_to_current_message 和 react_to_message 两个函数工具, LLM 通过 function calling 调用来添加表情反应。

## 配置项

所有配置可在 AstrBot WebUI 的插件配置页面中修改。

| 配置项 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| auto_react | bool | false | 是否启用自动表情反应 |
| react_rules | template_list | [] | 反应规则列表, 每条规则包含 emoji_ids (表情ID列表) 和 regex_list (触发正则列表) |
| react_scope | string | all | 自动反应范围: all / group / private |
| llm_react_enabled | bool | false | 是否启用 LLM 表情反应函数工具 |
| enable_msg_id_prefix | bool | true | 是否为消息注入消息 ID 前缀 |

### react_rules 规则说明

每条规则包含两个字段:

- **emoji_ids**: 表情 ID 列表。QQ 原生表情填数字 (如 `76` 表示赞), Unicode emoji 直接填字符, 插件会自动用 `ord()` 转换。
- **regex_list**: 触发正则表达式列表。消息匹配列表中任意正则时触发反应。留空表示对所有消息反应。

### LLM 函数工具

开启 `llm_react_enabled` 后, 插件会注册两个函数工具供 LLM 调用:

| 工具名 | 参数 | 作用 |
|--------|------|------|
| react_to_current_message | emoji_id | 对当前用户消息添加表情反应 |
| react_to_message | emoji_id, message_id | 对指定 msg_id 的消息添加表情反应 |

开启 `enable_msg_id_prefix` 后, 用户消息会自动添加 `msg_id:xxx` 前缀, 使 LLM 能获取消息 ID 来调用 react_to_message。

#### 人设提示词参考

在人格提示词中告知 LLM 可以使用这些函数工具, 例如:

```
用户消息会以 msg_id:xxx 开头, 这是消息的唯一标识。当你想对消息进行表情反应时, 请调用react_to_current_message或react_to_message函数工具。你可以多次调用来添加多个反应。可用的QQ数字表情ID: 448代表"火球术" 447代表"点赞" 446代表"摧心术" 445代表"魅惑怪物" 444代表"666" 443代表"死亡一指" 442代表"鸽子跳舞", 也可以使用Unicode emoji字符如😭。
```

## 平台支持

仅支持 aiocqhttp 平台 (NapCat / Lagrange 等 OneBot v11 实现)。
