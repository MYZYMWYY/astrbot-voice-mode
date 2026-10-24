"""按需语音：默认不出声，只有你让它说的时候才回语音。

两种触发：
  1. 关键词（最省事）：消息里出现"语音/说给我听/念给我听"等，这一条就出声，说完自动关
  2. 指令：/voice on 常开、/voice off 关闭、/voice once 只说这一条

关键词可在面板配置里改。
"""

from __future__ import annotations

from astrbot.api import logger
from astrbot.api.event import AstrMessageEvent, filter
from astrbot.api.star import Context, Star, register
from astrbot.core.star.session_llm_manager import SessionServiceManager

PLUGIN_NAME = "astrbot_plugin_voice_mode"
DEFAULT_SCOPE = ""
DEFAULT_KEYWORDS = [
    "语音",
    "说给我听",
    "念给我听",
    "读给我听",
    "用声音",
    "出个声",
    "说话给我听",
]


@register(PLUGIN_NAME, "按需语音", "关键词或指令触发语音回复", "1.1.0")
class VoiceModePlugin(Star):
    def __init__(self, context: Context, config: dict | None = None) -> None:
        super().__init__(context)
        self.config = config or {}
        self._once: set[str] = set()

    def _in_scope(self, umo: str) -> bool:
        prefix = str(self.config.get("scope_prefix", DEFAULT_SCOPE))
        return umo.startswith(prefix) if prefix else True

    def _keywords(self) -> list[str]:
        kw = self.config.get("keywords")
        if isinstance(kw, list) and kw:
            return [str(x).strip() for x in kw if str(x).strip()]
        return DEFAULT_KEYWORDS

    @filter.event_message_type(filter.EventMessageType.PRIVATE_MESSAGE, priority=60)
    async def keyword_trigger(self, event: AstrMessageEvent):
        """消息里带了触发词，就为这一条打开语音，发完由 reset_once 关掉。"""
        umo = event.unified_msg_origin
        if not self._in_scope(umo):
            return
        text = (event.message_str or "").strip()
        if not text or text.lower().startswith(("voice", "/voice")):
            return
        hit = next((k for k in self._keywords() if k in text), None)
        if not hit:
            return
        try:
            await SessionServiceManager.set_tts_status_for_session(umo, True)
            self._once.add(umo)
            logger.info(f"[voice_mode] 命中关键词「{hit}」，本条启用语音")
        except Exception as exc:  # noqa: BLE001
            logger.warning(f"[voice_mode] 开启语音失败: {exc}")

    @filter.command("voice")
    async def voice_cmd(self, event: AstrMessageEvent):
        umo = event.unified_msg_origin
        if not self._in_scope(umo):
            return

        raw = (event.message_str or "").strip().lower()
        arg = raw
        for token in ("/voice", "voice"):
            if arg.startswith(token):
                arg = arg[len(token):]
                break
        arg = arg.strip().strip("/").strip()

        if arg in ("on", "开", "开启"):
            await SessionServiceManager.set_tts_status_for_session(umo, True)
            yield event.plain_result("好，以后都用语音回你。")
        elif arg in ("off", "关", "关闭"):
            await SessionServiceManager.set_tts_status_for_session(umo, False)
            yield event.plain_result("行，不说话了，改回打字。")
        elif arg in ("once", "一次"):
            await SessionServiceManager.set_tts_status_for_session(umo, True)
            self._once.add(umo)
            yield event.plain_result("就这一条用语音。")
        else:
            enabled = await SessionServiceManager.is_tts_enabled_for_session(umo)
            state = "开（每条都语音）" if enabled else "关（只发文字）"
            yield event.plain_result(
                f"语音状态：{state}\n"
                "用法：/voice on（常开）、/voice off（关闭）、/voice once（只说这一条）"
            )

    @filter.after_message_sent()
    async def reset_once(self, event: AstrMessageEvent) -> None:
        """once 模式：这条发完就自动关回去。"""
        umo = event.unified_msg_origin
        if umo in self._once:
            self._once.discard(umo)
            try:
                await SessionServiceManager.set_tts_status_for_session(umo, False)
                logger.info(f"[voice_mode] once 已用完，{umo} 恢复静音")
            except Exception as exc:  # noqa: BLE001
                logger.warning(f"[voice_mode] 恢复静音失败: {exc}")
