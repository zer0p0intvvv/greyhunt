import json
import logging
from dataclasses import dataclass, field
from typing import Optional

from openai import AsyncOpenAI

logger = logging.getLogger("tg_crawler")


@dataclass
class AnalysisResult:
    """Result of LLM analysis for a single message."""

    is_relevant: bool = False
    risk_type: str = ""
    risk_level: str = ""
    entities: dict = field(default_factory=dict)
    summary: str = ""


class LLMFilter:
    """LLM-based secondary filter using AsyncOpenAI-compatible API."""

    SYSTEM_PROMPT = """你是一个黑灰产情报分析专家，服务于合法的网络安全研究与平台风控治理。你需要分析以下消息是否与字节跳动/抖音/TikTok相关的黑灰产活动有关。

对每条消息，返回JSON数组，每个元素包含：
- index: 消息序号（从0开始）
- is_relevant: bool，是否与字节跳动黑灰产相关
- risk_type: 风险类型（账号交易/刷量作弊/引流诈骗/数据泄露/工具交易/其他），不相关则为空
- risk_level: 风险等级（high/medium/low），判定标准如下：
  - high: 直接提供黑灰产服务/交易（明确的买卖、接单、报价、招募），或涉及数据泄露/安全漏洞
  - medium: 分享黑灰产方法/教程/工具，或疑似在试探/招揽但未明确报价
  - low: 仅讨论/提及相关话题，未提供具体服务或交易信息
- entities: 提取的实体对象。这是情报核心，必须从原文中**穷尽提取所有出现的实体，不得遗漏、不得脱敏、不得掩码**，保留完整原始值（用于溯源处置）：
  - accounts: 涉及的平台账号列表，保留完整账号名/ID，例如 "抖音号:dy12345", "TikTok:@shopxxx", "小红书:xhs_abc"
  - contacts: 联系方式列表，**逐一提取每一个联系方式**，每项格式为 "平台:联系方式"，平台必须明确标注（QQ/微信/Telegram/WhatsApp/手机/邮箱/钉钉等），例如 "QQ:3908344109", "Telegram:@smmmaxx1", "微信:wx_abc123", "WhatsApp:+8613800138000"。同一条消息出现多个联系方式时全部列出。注意识别变体写法：微信(薇信/VX/v信/weixin)、电报(飞机/纸飞机/TG)、扣扣(QQ)等。
  - links: 所有链接列表，包含完整URL（http/https/t.me/短链等），并保留链接后紧跟的邀请码/口令（如有）
  - domains: 从链接或文本中提取的独立域名列表，例如 "xiaoerhao.com", "北境.top", "fensyun.com"
  - invite_codes: 邀请码/优惠码/口令列表（如"邀请码bbs888"）
  - tools: 工具/软件/平台名称列表
  - prices: 价格信息列表（含金额与单位，如"15元/个", "100/千粉"）

实体抽取要求（重要）：
1. 完整保留：所有账号、联系方式、域名一律输出**完整原始值**，严禁用 *** 掩码或省略，严禁脱敏。
2. 穷尽提取：宁可多抽不可漏抽，原文里每一个 @账号、微信号、QQ号、电报号、域名、邀请码都要进 entities。
3. 若某类不存在则返回空数组 []。

- summary: 一句话中文摘要，需点明所提供的服务类型与主要引流渠道（如有），不相关则为空

只返回JSON数组，不要其他内容。"""

    def __init__(self, config: dict):
        self._client = AsyncOpenAI(
            api_key=config["api_key"],
            base_url=config["base_url"],
        )
        self._model = config["model"]
        self._batch_size = config.get("batch_size", 15)

    @staticmethod
    def _build_prompt(messages: list[str]) -> str:
        """Build the user prompt with numbered messages."""
        lines = []
        for i, msg in enumerate(messages):
            lines.append(f"[{i}] {msg}")
        return "请分析以下消息:\n\n" + "\n".join(lines)

    @staticmethod
    def _parse_response(response_text: str) -> list[AnalysisResult]:
        """Parse LLM JSON response into AnalysisResult objects."""
        try:
            text = response_text.strip()
            if text.startswith("```"):
                text = text.split("\n", 1)[1]
                text = text.rsplit("```", 1)[0]

            data = json.loads(text)
            results = []
            for item in data:
                results.append(AnalysisResult(
                    is_relevant=item.get("is_relevant", False),
                    risk_type=item.get("risk_type", ""),
                    risk_level=item.get("risk_level", ""),
                    entities=item.get("entities", {}),
                    summary=item.get("summary", ""),
                ))
            return results
        except (json.JSONDecodeError, KeyError, TypeError) as e:
            logger.error(f"Failed to parse LLM response: {e}")
            return []

    async def analyze_batch(self, messages: list[str]) -> list[AnalysisResult]:
        """Send a batch of messages to LLM for analysis."""
        if not messages:
            return []

        prompt = self._build_prompt(messages)

        try:
            response = await self._client.chat.completions.create(
                model=self._model,
                messages=[
                    {"role": "system", "content": self.SYSTEM_PROMPT},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.1,
            )
            content = response.choices[0].message.content
            return self._parse_response(content)
        except Exception as e:
            logger.error(f"LLM API call failed: {e}")
            return []

    async def analyze(self, messages: list[str]) -> list[AnalysisResult]:
        """Analyze messages in batches."""
        all_results = []
        for i in range(0, len(messages), self._batch_size):
            batch = messages[i : i + self._batch_size]
            results = await self.analyze_batch(batch)
            all_results.extend(results)
        return all_results

    # ------------------------------------------------------------------
    # 多模态：从图片/视频封面提取黑灰产引流信息（OCR + 视觉理解）
    # ------------------------------------------------------------------

    VISION_PROMPT = (
        "你是黑灰产情报分析专家。请仔细识别这张图片中的所有信息，"
        "黑灰产广告常把关键引流信息印在图片上。请提取并以中文输出：\n"
        "1. 图中所有文字（OCR），尤其是：微信号/QQ/Telegram(飞机/纸飞机)账号、"
        "手机号、网址/域名、价目表、平台名、工作室/团队名、二维码旁的说明文字；\n"
        "2. 若有二维码，说明它是什么平台的（微信/Telegram/支付等）；\n"
        "3. 图中出现的 App/平台 logo（如抖音/TikTok/微信/小红书/快手/Telegram 等）。\n"
        "只输出图中实际可见的信息，简洁罗列，不要编造。若图片无有效信息，回复『无』。"
    )

    async def extract_from_image(self, image_url: str) -> str:
        """对单张图片做视觉提取，返回图中文字/账号/二维码等信息的中文描述。

        先本地下载图片转 base64 data URI 再传给模型——避免模型服务端
        （火山方舟）去访问 pbs.twimg.com 等境外图床时连接被重置/超时。
        失败返回空串。
        """
        if not image_url:
            return ""
        payload_url = await self._to_data_uri(image_url)
        if not payload_url:
            return ""
        try:
            response = await self._client.chat.completions.create(
                model=self._model,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": self.VISION_PROMPT},
                            {"type": "image_url", "image_url": {"url": payload_url}},
                        ],
                    }
                ],
                temperature=0.1,
            )
            text = (response.choices[0].message.content or "").strip()
            if text in ("无", "无。", ""):
                return ""
            return text
        except Exception as e:
            logger.warning(f"Vision extract failed for {image_url}: {e}")
            return ""

    @staticmethod
    async def _to_data_uri(image_url: str) -> str:
        """下载图片并转成 base64 data URI；失败返回空串。

        短超时（8s）避免个别慢图拖垮整批；超过 ~6MB 的图跳过（base64 后过大）。
        """
        import base64

        import httpx

        try:
            async with httpx.AsyncClient(
                timeout=httpx.Timeout(8.0, connect=5.0), follow_redirects=True
            ) as c:
                resp = await c.get(image_url)
                resp.raise_for_status()
                content = resp.content
                if len(content) > 6 * 1024 * 1024:
                    logger.warning(f"Image too large, skip: {image_url} ({len(content)} bytes)")
                    return ""
                ctype = resp.headers.get("content-type", "image/jpeg").split(";")[0]
                if not ctype.startswith("image/"):
                    ctype = "image/jpeg"
                b64 = base64.b64encode(content).decode("ascii")
                return f"data:{ctype};base64,{b64}"
        except Exception as e:
            logger.warning(f"Image download failed for {image_url}: {e}")
            return ""

    async def extract_from_images(self, image_urls: list[str], *, max_images: int = 2) -> str:
        """对一条推文的多张图片做视觉提取并汇总（限制张数控制成本）。"""
        if not image_urls:
            return ""
        parts: list[str] = []
        for url in image_urls[:max_images]:
            txt = await self.extract_from_image(url)
            if txt:
                parts.append(txt)
        return "\n".join(parts)
