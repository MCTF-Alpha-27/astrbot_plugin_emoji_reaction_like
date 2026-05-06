# EmojiReactionLike

AstrBot 插件, 允许 bot 在接入 NapCat 平台时对 QQ 消息添加表情反应 (Reaction)。

支持手动指令触发、正则自动触发, 以及 LLM 通过函数工具自主决定添加表情反应。

## 功能

### 指令

| 指令 | 说明 |
|------|------|
| /react [emoji_id] | 回复一条消息并发送, 对被回复的消息添加表情反应。不指定 emoji_id 时使用第一条反应规则中的表情 |
| /reactlist | 列出互动反应表态 ID (443-448) 供参考 |
| /reactconfig | 查看当前插件配置 (仅管理员) |

### 自动反应

根据配置的正则规则, 自动对匹配的消息添加表情反应。支持多规则、多表情、多正则, 可配置仅群聊或仅私聊生效。

### LLM 函数工具

开启后, 插件注册两个函数工具供 LLM 通过 function calling 调用:

| 工具名 | 参数 | 作用 |
|--------|------|------|
| react_to_current_message | emoji_id | 对当前用户消息添加表情反应 |
| react_to_message | emoji_id, message_id | 对指定 msg_id 的历史消息添加表情反应 |

工具调用结果会返回给 LLM, LLM 继续正常生成对话回复, 用户不会看到工具调用过程。

### 消息 ID 参考表

开启 `enable_msg_id_prefix` 后, 插件会在每次 LLM 请求前自动注入一份包含近期消息 msg_id 的参考表, 使 LLM 能够识别并指定历史消息进行反应。

参考表格式示例:
```
[msg_id参考表]
msg_id:495891555 [pppopipupu]: 打火球术
msg_id:495891556 [pppopipupu]: ？
msg_id:495891557 [芸诺_ miss]: 不是怎么都这么快。
[/msg_id参考表]
```

## 配置项

所有配置可在 AstrBot WebUI 的插件配置页面中修改。

| 配置项 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| auto_react | bool | false | 是否启用自动表情反应 |
| react_rules | template_list | [] | 反应规则列表, 每条规则包含 emoji_ids 和 regex_list |
| react_scope | string | all | 自动反应范围: all / group / private |
| llm_react_enabled | bool | false | 是否启用 LLM 表情反应函数工具 |
| enable_msg_id_prefix | bool | true | 是否注入消息 ID 参考表 |

### react_rules 规则说明

每条规则包含两个字段:

- **emoji_ids**: 表情 ID 列表。QQ 原生表情填数字 (0-500), Unicode emoji 直接填字符, 插件自动用 `ord()` 转换。
- **regex_list**: 触发正则表达式列表。消息匹配列表中任意正则时触发反应。留空表示对所有消息反应。

### 人设提示词参考

在人格提示词中告知 LLM 可以使用函数工具, 例如:

```
当你想对消息进行表情反应时，可以参考上下文中的 [msg_id参考表] 获取对应消息的 msg_id 并调用 react_to_message 函数工具；如果是对当前最新消息反应，则调用 react_to_current_message。你可以多次调用来添加多个反应。可用的QQ数字表情ID: 448代表"火球术" 447代表"点赞" 446代表"摧心术" 445代表"魅惑怪物" 444代表"666" 443代表"死亡一指" 442代表"鸽子跳舞", 也可以使用Unicode emoji字符如😭。
```

## 平台支持

仅支持 aiocqhttp 平台 (NapCat / Lagrange 等 OneBot v11 实现)。
