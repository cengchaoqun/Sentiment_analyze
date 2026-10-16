import json
from typing import Any

from langchain_core.prompts import PromptTemplate
from loguru import logger

from sentiment_analyze_service.engines.agent.meida.output import MediaSearchPlanOutput
from sentiment_analyze_service.engines.agent.meida.state import MediaState, MediaSectionState
from sentiment_analyze_service.engines.agent.meida.tools.catalog import SEARCH_TOOL_DESCRIPTIONS
from sentiment_analyze_service.engines.contract.context import ResearchBaseNode
from sentiment_analyze_service.engines.contract.role import get_role_display_name
from sentiment_analyze_service.engines.contract.section import SECTION_DEFINITIONS, get_section_definitions_for_role
from sentiment_analyze_service.engines.prompts.media import MEDIA_SEARCH_PLAN_USER_PROMPT, \
    MEDIA_SEARCH_PLAN_SYSTEM_PROMPT


class PlanSearchNode(ResearchBaseNode):
    """为固定media章节生成搜索工具和关键词"""

    async def __call__(self, state:MediaState)->dict[str,Any]:
        """调用LLM生成搜索策略，并与固定章节定义合并为运行状态"""
        agent_name = get_role_display_name(self.context.role)

        planned_output = await self._generate_search_plan(self.context.query)

        sections:list[MediaSectionState] = [
            MediaSectionState(
                section_key=section_definition.key,
                title=section_definition.title,
                search_tool=plan_section.search_tool,
                search_keywords=[keyword.strip() for keyword in plan_section.search_keywords]
            ) for section_definition,plan_section in zip(SECTION_DEFINITIONS.values(),
                                                         planned_output.sections)
        ]

        logger.info(f"{agent_name} 公域搜索策略规划完成")

        return {"sections": sections}

    async def _generate_search_plan(
            self,
            research_topic: str
    ) -> MediaSearchPlanOutput:
        """组装搜索规划提示词并调用 LLM 返回结构化搜索计划"""

        search_tools = [
            {"name": tool, "description": description}
            for tool, description in SEARCH_TOOL_DESCRIPTIONS.items()
        ]

        user_prompt = PromptTemplate.from_template(MEDIA_SEARCH_PLAN_USER_PROMPT).format(
            research_topic=research_topic,
            section_contexts=json.dumps(
                get_section_definitions_for_role("media"),
                ensure_ascii=False,
                indent=2
            ),
            search_tools=json.dumps(
                search_tools,
                ensure_ascii=False,
                indent=2
            )
        )

        return await self.context.llm_client.generate_object(
            system_prompt=MEDIA_SEARCH_PLAN_SYSTEM_PROMPT,
            user_prompt=user_prompt,
            structed_object=MediaSearchPlanOutput
        )
