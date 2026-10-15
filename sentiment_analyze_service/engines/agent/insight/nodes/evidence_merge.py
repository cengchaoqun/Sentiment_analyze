from typing import Any

from loguru import logger

from sentiment_analyze_service.engines.agent.insight.state import InsightState
from sentiment_analyze_service.engines.contract.context import ResearchBaseNode
from sentiment_analyze_service.engines.contract.evidence import RetrievedEvidence
from sentiment_analyze_service.engines.contract.role import get_role_display_name




class EvidenceMergedNode(ResearchBaseNode):
    """
    把两通道召回合并成一份候选，并给出每条的相关性得分，
    这里先不排序：章节准备节点进行排序
    五个章节维度不一样（传播章节按热度排序，其余章节按相关性排序）
    """

    async def __call__(self, state: InsightState) -> dict[str, Any]:
        agent_name = get_role_display_name(self.context.role)
        logger.info(f"{agent_name}开始合并两通道检索证据")

        retrieved_records: list[RetrievedEvidence] = state.get("retrieved_records") or []

        records_by_id: dict[str,RetrievedEvidence] = _get_candidate_evidence(retrieved_records)
        relevance_score: dict[str, float] = _compute_relevance_scores(records_by_id.values())

        logger.info(f"{agent_name}合并两通道检索证据完成")

        return {
            "records_by_id": records_by_id,
            "relevance_scores": relevance_score
        }


def _get_candidate_evidence(retrieved_records: list[RetrievedEvidence]) -> dict[str, RetrievedEvidence]:
    """
    职责：根据两个检索通道的证据记录进行合并
    合并：创建一个新的RetrievedEvidence，给新对象的document、channel_scores赋值
    重复的情况：
    1. MySQL单通道检索会出现重复（不同的分词可能会查询到相同的检索结果）
    2. Milvus单通道检索一定不会出现重复
    3. MySQL+Milvus两个通道会出现重复(query：查询，各个分词查询到的相同的检索结果)

    :param retrieved_records:
    :return:
    """
    records_by_id:dict[str,RetrievedEvidence]={}
    for retrieved_record in retrieved_records:
        doc_id = retrieved_record.id
        retrieved_evidence = records_by_id.get(doc_id)
        if retrieved_evidence is None:
            records_by_id[doc_id] = retrieved_record
            continue
        exit_evidence = records_by_id[doc_id]
        new_evidence = RetrievedEvidence(
            document=retrieved_record.document,
            channel_scores={**exit_evidence.channel_scores, **retrieved_record.channel_scores}
        )
        records_by_id[doc_id] = new_evidence
    return records_by_id



def _compute_relevance_scores(retrieved_evidence:Any)->dict[str,float]:
    relevance_scores: dict[str,float] = {}
    for evidence in retrieved_evidence:
        relevance_scores[evidence.id] = evidence.channel_scores.get("db_channel", 0) + evidence.channel_scores.get("vector_channel", 0)
    return relevance_scores

























