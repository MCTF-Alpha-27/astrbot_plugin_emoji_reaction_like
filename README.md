# EmojiReactionLike

AstrBot 插件, 允许 bot 在接入 NapCat 平台时对 QQ 消息添加表情反应 (Reaction)。可在回复时或正则匹配关键字触发。

## 功能

- **/react [emoji_id]** - 回复一条消息并发送此指令, 对被回复的消息添加表情反应。不指定 emoji_id 时使用第一条反应规则中的表情。
- **/reactlist** - 列出常用的 QQ 表情反应 ID 供参考。
- **/reactconfig** - 查看当前插件配置 (仅管理员)。
- **自动反应** - 根据配置的正则规则, 自动对匹配的消息添加表情反应。
- **LLM 输出反应** - 拦截 LLM 回复, 通过正则匹配提取 `[react:xxx]` 标记并执行反应, 同时从回复中移除标记文本。

## 配置项

所有配置可在 AstrBot WebUI 的插件配置页面中修改。

| 配置项 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| auto_react | bool | false | 是否启用自动表情反应 |
| react_rules | template_list | [] | 反应规则列表, 每条规则包含 emoji_ids (表情ID列表) 和 regex_list (触发正则列表) |
| react_scope | string | all | 自动反应范围: all / group / private |
| llm_react_enabled | bool | false | 是否启用 LLM 输出表情反应 |
| llm_react_regex | string | `\[react:([^\]]+)\]` | 匹配 LLM 输出中表情标记的正则表达式 |

### react_rules 规则说明

每条规则包含两个字段:

- **emoji_ids**: 表情 ID 列表。QQ 原生表情填数字 (如 `76` 表示赞), Unicode emoji 直接填字符, 插件会自动用 `ord()` 转换。
- **regex_list**: 触发正则表达式列表。消息匹配列表中任意正则时触发反应。留空表示对所有消息反应。

### LLM 输出反应用法

开启 `llm_react_enabled` 后, 在人格提示词中告知 LLM 可以使用 `[react:表情ID]` 格式, 例如:

```
当你想对用户发送的消息进行反应时，可以在回复末尾添加 [react:id] 来对用户消息添加表情反应。你可以插入多个[react:id]来添加多个反应，反应的emoji可以自由改变，如[react:😭]是合法的。你也可以使用QQ的数字表情ID，例如[react:448]代表“火球术”[react:447]代表“点赞”[react:446]代表“摧心术”[react:445]代表“魅惑怪物”[react:444]代表“666”[react:443]代表“死亡一指”[react:442]代表“鸽子跳舞”
```

插件会自动提取标记、执行反应, 并从最终回复中移除标记文本。

## 平台支持

仅支持 aiocqhttp 平台 (NapCat / Lagrange 等 OneBot v11 实现)。
