from typing import Any

from typesafe_sdk import AsyncTypeSafeClient, Choice

from sentiment_analyze_service.engines.agent.insight.state import InsightState
from sentiment_analyze_service.engines.agent.insight.tools.db.repository import list_topic_keys
from sentiment_analyze_service.engines.contract.config import get_config_settings
from sentiment_analyze_service.engines.contract.context import ResearchBaseNode





class TopicRouteNode(ResearchBaseNode):
    """读取MySQL事件标签，并用jev选择本次研究范围"""
    async def __call__(self,state:InsightState)->dict[str,Any]:
        topics = await list_topic_keys()

        topic_key = await select_topic(self.context.query,topics)

        if topic_key not in topics:
            raise ValueError("Insight主题选择结果不再MySQL主题中")

        return {"topic_leu":topic_key}


async def select_topic(query:str, topics:list[str])->str:
    """用jev从已有标签选一个返回已有标签"""
    topic_keys = list(dict.fromkeys(topic.strip() for topic in topics if topic.strip()))
    if not topic_keys:
        raise ValueError("MySQL没有提供可供研究的主题")
    if len(topic_keys) == 1:
        return topic_keys[0]
    if len(topic_keys) > 255 :
        raise ValueError("主题超过jev单次选择的上限")

    choices = {f"topic_{index}": topic for index,topic in enumerate(topic_keys)}

    async with AsyncTypeSafeClient(
        api_key=get_config_settings().TYPESAFE_API_KEY,
        model="jev-latest",
        timeout=30.0
    ) as client:
        response = await client.system_one(
            state=query,
            questions={
                "topic":Choice(
                    instructions="从候选主题中选出用户希望研究的一个重要主题。",
                    criteria=choices
                )
            }
        )

    try:
        selected = response.choices["topic"].choice

        return choices[selected]
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError("Jev 没有返回有效的事件标签") from exc















