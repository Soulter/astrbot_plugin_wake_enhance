import time
import re
from astrbot.api.event import filter, AstrMessageEvent
from astrbot.api.star import Context, Star, register
from astrbot.api import logger
@register(
    "astrbot_plugin_wake_enhance",
    "Soulter",
    "让 AstrBot 支持正则匹配唤醒、唤醒后持续与机器人对话和交互",
    "v1.0.0",
    "https://github.com/Soulter/astrbot_plugin_wake_enhance",
)
class MyPlugin(Star):
    def __init__(self, context: Context, config: dict):
        super().__init__(context)
        self.waking_group_ids = {} # 处于唤醒状态的群聊 ID 列表
        self.waking_regex = config.get("waking_regex", [])
        self.c_awake = config.get("continuous_awakening", {})
        self.whitelist = config.get("whitelist", [])

    @filter.command("wbegin")
    async def wbegin(self, event: AstrMessageEvent):
        '''进入持续唤醒状态'''
        if event.is_private_chat():
            yield event.plain_result("私聊使用此功能没有意义~") 
        group_id = event.message_obj.group_id
        if self.whitelist and group_id not in self.whitelist:
            yield event.plain_result("此群聊不在唤醒增强插件白名单内哦~")
        
        if group_id in self.waking_group_ids:
            yield event.plain_result("我在哦~")
        self.waking_group_ids[group_id] = {
            "last_time": time.time()
        }
        yield event.plain_result("我来啦！")
        
    @filter.command("wexit")
    async def wexit(self, event: AstrMessageEvent):
        '''退出持续唤醒状态'''
        if event.is_private_chat():
            yield event.plain_result("私聊使用此功能没有意义~") 
        group_id = event.message_obj.group_id
        if self.whitelist and group_id not in self.whitelist:
            yield event.plain_result("此群聊不在唤醒增强插件白名单内哦~")
        
        if group_id not in self.waking_group_ids:
            yield event.plain_result("拜拜~")
            return
        self.waking_group_ids.pop(group_id)
        yield event.plain_result("拜拜~")
        
    @filter.command("wgid")
    async def wgroup(self, event: AstrMessageEvent):
        '''查看白名单 ID'''
        yield event.plain_result(str(event.message_obj.group_id))
        
    async def check_regex(self, message_str: str):
        '''检查正则表达式'''
        for regex in self.waking_regex:
            if re.match(regex, message_str):
                return True
        return False
        
    @filter.event_message_type(filter.EventMessageType.ALL)
    async def on_message(self, event: AstrMessageEvent):
        '''持续唤醒监听器'''
        if event.is_private_chat():
            return
        group_id = event.message_obj.group_id
        if self.whitelist and group_id not in self.whitelist:
            return
        
        if await self.check_regex(event.message_str):
            event.is_at_or_wake_command = True
            if self.c_awake.get("enable", False):
                self.waking_group_ids[group_id] = {
                    "last_time": time.time()
                }
        
        # 持续唤醒相关逻辑
        if group_id not in self.waking_group_ids:
            # 不在持续唤醒状态
            return
        if time.time() - self.waking_group_ids[group_id]["last_time"] > float(self.c_awake.get("waking_interval", 30)):
            self.waking_group_ids.pop(group_id)
            logger.info(f"由于超时，群聊 {group_id} 退出持续唤醒状态。")
            return
        
        event.is_at_or_wake_command = True
        
        if self.c_awake.get("reset_when_reply", False):
            self.waking_group_ids[group_id]["last_time"] = time.time()
