from typing import Callable, Awaitable

from sentiment_analyze_service.engines.agent.insight.invoker import invoke_insight_agent
from sentiment_analyze_service.engines.agent.meida.invoker import invoke_media_agent
from sentiment_analyze_service.engines.common.llm import LLMClient
from sentiment_analyze_service.engines.common.log import execute_logger
from sentiment_analyze_service.engines.common.task import ResearchTask, task_manager
from sentiment_analyze_service.engines.common.utils import get_report_dir
from sentiment_analyze_service.engines.contract.role import RoleID

AGENT_INVOKER = Callable[[str, str, str, LLMClient, str], Awaitable[None]] # 变量的类型注解，role, query, task_id, llm_client, output_dir


class ResearchOrchestrator:
    def __init__(self):
        self.agent_invoker: dict[RoleID, AGENT_INVOKER] = {
            "insight": invoke_insight_agent,
            "media": invoke_media_agent
        }

    def dispatch_task(self, research_task: ResearchTask):
        """
        职责：将研究任务转发给两个研究Agent，并发执行
        :param research_task:
        :return:
        """
        for role in self.agent_invoker:
            task_manager.create_background_task(self.invoke_research_agent(role, research_task))

    def invoke_research_agent(self, role: RoleID, research_task: ResearchTask):
        llm_client = LLMClient.from_role(role)
        output_dir = get_report_dir(research_task.task_id, role)
        with execute_logger(role):
            self.agent_invoker[role](
                role,
                research_task.query,
                research_task.task_id,
                llm_client,
                output_dir
            )
