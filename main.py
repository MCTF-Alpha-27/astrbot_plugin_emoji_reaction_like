import re
from astrbot.api.event import filter, AstrMessageEvent, MessageEventResult
from astrbot.api.star import Context, Star, register
from astrbot.api import logger, AstrBotConfig

@register("emoji_like", "pppopipupu", "允许bot在napcat平台使用QQ表情反应消息。", "1.0.0")
class EmojiReactionLike(Star):
    def __init__(self, context: Context, config: AstrBotConfig):
        super().__init__(context)
        self.config = config

    def _parse_emoji_id(self, emoji_input: str) -> str:
        emoji_input = emoji_input.strip()
        if emoji_input.isdigit():
            return emoji_input
        if len(emoji_input) >= 1:
            return str(ord(emoji_input[0]))
        return emoji_input

    async def _do_emoji_reaction(self, event: AstrMessageEvent, message_id, emoji_id: str):
        if event.get_platform_name() != "aiocqhttp":
            return None

        from astrbot.core.platform.sources.aiocqhttp.aiocqhttp_message_event import AiocqhttpMessageEvent
        if not isinstance(event, AiocqhttpMessageEvent):
            return None

        client = event.bot
        payloads = {
            "message_id": message_id,
            "emoji_id": emoji_id,
        }
        try:
            ret = await client.api.call_action('set_msg_emoji_like', **payloads)
            logger.info(f"set_msg_emoji_like: message_id={message_id}, emoji_id={emoji_id}, ret={ret}")
            return ret
        except Exception as e:
            logger.error(f"set_msg_emoji_like failed: {e}")
            return None

    def _get_reply_message_id(self, event: AstrMessageEvent):
        raw = event.message_obj.raw_message
        if isinstance(raw, dict):
            messages = raw.get('message', [])
            if isinstance(messages, list):
                for seg in messages:
                    if isinstance(seg, dict) and seg.get('type') == 'reply':
                        return seg.get('data', {}).get('id')
        for comp in event.get_messages():
            if hasattr(comp, 'type') and getattr(comp, 'type', None) == 'reply':
                if hasattr(comp, 'id'):
                    return comp.id
        return None

    @filter.command("react")
    async def react(self, event: AstrMessageEvent, emoji_id: str = ""):
        """对引用的消息添加表情反应。用法: 回复一条消息并发送 /react [emoji_id]"""
        if event.get_platform_name() != "aiocqhttp":
            yield event.plain_result("该功能仅支持 QQ 平台 (aiocqhttp)。")
            return

        reply_msg_id = self._get_reply_message_id(event)
        if not reply_msg_id:
            yield event.plain_result("请回复一条消息后使用此指令。")
            return

        if not emoji_id:
            react_rules = self.config.get("react_rules", [])
            if react_rules and react_rules[0].get("emoji_ids"):
                emoji_id = react_rules[0].get("emoji_ids")[0]
            else:
                emoji_id = "76"

        parsed_id = self._parse_emoji_id(emoji_id)
        ret = await self._do_emoji_reaction(event, reply_msg_id, parsed_id)
        if ret is not None:
            yield event.plain_result(f"已对消息添加表情反应 (emoji_id: {parsed_id})")
        else:
            yield event.plain_result("表情反应失败，请检查日志。")

    @filter.command("reactlist")
    async def reactlist(self, event: AstrMessageEvent):
        """列出常用的QQ表情反应ID"""
        text = (
            "QQ表情反应ID参考:\n"
            "--- 互动反应表态 (443-448) ---\n"
            "443: 戳一戳  444: 666  445: 展示爱心\n"
            "446: 捏碎爱心  447: 点赞  448: 放大招\n"
            "--- Unicode Emoji ---\n"
            "直接使用emoji字符即可, 插件会自动使用 ord() 转换"
        )
        yield event.plain_result(text)

    @filter.permission_type(filter.PermissionType.ADMIN)
    @filter.command("reactconfig")
    async def reactconfig(self, event: AstrMessageEvent):
        """查看当前表情反应配置（仅管理员）"""
        react_rules = self.config.get("react_rules", [])
        rules_text = ""
        for rule in react_rules:
            emoji_inputs = rule.get("emoji_ids", [])
            regex_list = rule.get("regex_list", [])
            emoji_str = ", ".join(emoji_inputs) if emoji_inputs else "(无表情)"
            reg_str = ", ".join(regex_list) if regex_list else "(所有消息)"
            rules_text += f"  [{emoji_str}] -> {reg_str}\n"
        if not rules_text:
            rules_text = "  (未配置)\n"
        text = (
            "当前表情反应配置:\n"
            f"自动反应: {self.config.get('auto_react', False)}\n"
            f"反应范围: {self.config.get('react_scope', 'all')}\n"
            f"反应规则:\n{rules_text}"
            f"LLM函数工具: {self.config.get('llm_react_enabled', False)}\n"
            f"消息ID前缀: {self.config.get('enable_msg_id_prefix', True)}\n"
            "\n请在 AstrBot WebUI 中修改配置。"
        )
        yield event.plain_result(text)

    @filter.platform_adapter_type(filter.PlatformAdapterType.AIOCQHTTP)
    @filter.event_message_type(filter.EventMessageType.ALL)
    async def on_all_message(self, event: AstrMessageEvent):
        """自动表情反应监听器"""
        if not self.config.get("auto_react", False):
            return

        scope = self.config.get("react_scope", "all")
        is_group = bool(event.message_obj.group_id)
        if scope == "group" and not is_group:
            return
        if scope == "private" and is_group:
            return

        react_rules = self.config.get("react_rules", [])
        if not react_rules:
            return

        message_str = event.message_str
        message_id = event.message_obj.message_id

        for rule in react_rules:
            emoji_inputs = rule.get("emoji_ids", [])
            regex_list = rule.get("regex_list", [])
            if not emoji_inputs:
                continue
            
            should_react = False
            if not regex_list:
                should_react = True
            else:
                for reg in regex_list:
                    try:
                        if re.search(reg, message_str):
                            should_react = True
                            break
                    except re.error as e:
                        logger.error(f"Invalid regex in react_rules: {reg}, error: {e}")
            
            if should_react:
                for emoji_input in emoji_inputs:
                    parsed_id = self._parse_emoji_id(str(emoji_input))
                    await self._do_emoji_reaction(event, message_id, parsed_id)

    @filter.on_llm_request()
    async def on_llm_request(self, event: AstrMessageEvent, req):
        """在LLM请求前注入msg_id前缀"""
        if not self.config.get("llm_react_enabled", False) or not self.config.get("enable_msg_id_prefix", True):
            return
        if event.get_platform_name() != "aiocqhttp":
            return

        message_id = event.message_obj.message_id
        prefix = f"msg_id:{message_id} "

        if hasattr(req, 'prompt') and req.prompt:
            req.prompt = prefix + req.prompt
        elif hasattr(req, 'messages') and req.messages:
            last_msg = req.messages[-1]
            if hasattr(last_msg, 'content') and isinstance(last_msg.content, str):
                last_msg.content = prefix + last_msg.content

    @filter.llm_tool(name="react_to_current_message")
    async def react_to_current_message(self, event: AstrMessageEvent, emoji_id: str) -> MessageEventResult:
        '''对用户当前发送的消息添加表情反应。
        Args:
            emoji_id(string): 表情ID。QQ原生表情使用数字如448代表火球术、447代表点赞、446代表摧心术、445代表魅惑怪物、444代表666、443代表死亡一指、442代表鸽子跳舞，也可以使用Unicode emoji字符。
        '''
        if event.get_platform_name() != "aiocqhttp":
            yield event.plain_result("不支持")
            return

        current_message_id = event.message_obj.message_id
        parsed_id = self._parse_emoji_id(emoji_id)
        ret = await self._do_emoji_reaction(event, current_message_id, parsed_id)
        if ret is not None:
            yield event.plain_result(f"已成功对用户当前消息添加了表情反应(emoji_id={parsed_id})，用户不会看到这条工具调用结果，请继续正常回复用户的消息。")
        else:
            yield event.plain_result("表情反应添加失败，可能是表情ID无效或权限不足，请继续正常回复用户。")

    @filter.llm_tool(name="react_to_message")
    async def react_to_message(self, event: AstrMessageEvent, emoji_id: str, message_id: str) -> MessageEventResult:
        '''对指定消息ID的消息添加表情反应。用于对历史消息进行反应，需要提供目标消息的msg_id。
        Args:
            emoji_id(string): 表情ID。QQ原生表情使用数字如448代表火球术、447代表点赞、446代表摧心术、445代表魅惑怪物、444代表666、443代表死亡一指、442代表鸽子跳舞，也可以使用Unicode emoji字符。
            message_id(string): 目标消息的ID，从用户消息的msg_id前缀中获取。
        '''
        if event.get_platform_name() != "aiocqhttp":
            yield event.plain_result("不支持")
            return

        parsed_id = self._parse_emoji_id(emoji_id)
        ret = await self._do_emoji_reaction(event, message_id.strip(), parsed_id)
        if ret is not None:
            yield event.plain_result(f"已成功对消息(msg_id={message_id})添加了表情反应(emoji_id={parsed_id})，用户不会看到这条工具调用结果，请继续正常回复用户的消息。")
        else:
            yield event.plain_result("表情反应添加失败，可能是消息ID或表情ID无效，请继续正常回复用户。")
