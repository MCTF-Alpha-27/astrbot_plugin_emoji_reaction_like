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
            f"LLM输出反应: {self.config.get('llm_react_enabled', False)}\n"
            f"LLM简单反应正则: {self.config.get('llm_react_regex', '')}\n"
            f"LLM指定目标正则: {self.config.get('llm_react_targeted_regex', '')}\n"
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

    @filter.platform_adapter_type(filter.PlatformAdapterType.AIOCQHTTP)
    @filter.event_message_type(filter.EventMessageType.ALL)
    async def on_msg_id_prefix(self, event: AstrMessageEvent):
        """在OneBot消息到达时为消息添加msg_id前缀"""
        if not self.config.get("llm_react_enabled", False) or not self.config.get("enable_msg_id_prefix", True):
            return

        message_id = event.message_obj.message_id
        event.message_str = f"msg_id:{message_id} {event.message_str}"

    @filter.on_llm_response()
    async def on_llm_response(self, event: AstrMessageEvent, resp):
        """拦截LLM输出，正则匹配表情反应标记"""
        if not self.config.get("llm_react_enabled", False):
            return

        if event.get_platform_name() != "aiocqhttp":
            return

        resp_text = getattr(resp, 'completion_text', None) or ""
        if not resp_text:
            return

        current_message_id = event.message_obj.message_id

        targeted_pattern = self.config.get("llm_react_targeted_regex", r"\[react:([^\],]+),id:([^\]]+)\]")
        try:
            targeted_matches = re.findall(targeted_pattern, resp_text)
        except re.error as e:
            logger.error(f"Invalid regex for targeted LLM react: {e}")
            targeted_matches = []

        for emoji_raw, target_id in targeted_matches:
            emoji_id = self._parse_emoji_id(emoji_raw.strip())
            await self._do_emoji_reaction(event, target_id.strip(), emoji_id)
            logger.info(f"LLM react (targeted): emoji_id={emoji_id} on message_id={target_id.strip()}")

        resp_text = re.sub(targeted_pattern, "", resp_text)

        simple_pattern = self.config.get("llm_react_regex", r"\[react:([^\]]+)\]")
        if simple_pattern:
            try:
                simple_matches = re.findall(simple_pattern, resp_text)
            except re.error as e:
                logger.error(f"Invalid regex for simple LLM react: {e}")
                simple_matches = []

            for match in simple_matches:
                emoji_id = self._parse_emoji_id(match.strip())
                await self._do_emoji_reaction(event, current_message_id, emoji_id)
                logger.info(f"LLM react (simple): emoji_id={emoji_id} on message_id={current_message_id}")

            resp_text = re.sub(simple_pattern, "", resp_text)

        cleaned_text = resp_text.strip()
        if hasattr(resp, 'completion_text'):
            resp.completion_text = cleaned_text

