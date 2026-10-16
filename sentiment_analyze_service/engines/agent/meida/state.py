from sentiment_analyze_service.engines.agent.meida.tools.catalog import SearchTool
from sentiment_analyze_service.engines.contract.evidence import RetrievedEvidence
from sentiment_analyze_service.engines.contract.state import SectionState, ResearchGraphState


class MediaSectionState(SectionState):
    """公域搜索策略的研究章节状态"""
    search_tool:SearchTool
    search_keywords:list[str]

class MediaState(ResearchGraphState[MediaSectionState],total=False):
    """公域搜索智能体langgraph全局状态定义"""
    section_evidence_records :list[list[RetrievedEvidence]]
    section_queries:list[str]