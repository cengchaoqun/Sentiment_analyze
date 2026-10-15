import asyncio
import logging

import jieba.analyse

from sentiment_analyze_service.engines.agent.insight.tools.db.repository import call_db
from sentiment_analyze_service.engines.agent.insight.tools.vector.repository import call_vector
from sentiment_analyze_service.engines.contract.config import get_config_settings
from sentiment_analyze_service.engines.contract.evidence import RetrievedEvidence, SourceDocument





async def retrieval_evidence(query:str,
                             topic_key:str
                             )->list[RetrievedEvidence]: #question:这个topic_key是什么东西
    """
    职责：从两个通道查询检索的结果，并且返回检索证据对象列表
    :param query:
    :param topic_key:
    :return:
    """
    # 1.分词
    query_terms = _extract_query_terms(query)

    # 2.并发执行MySQL通过、Milvus通道查询，获取两个通道的结果
    db_evidence,vector_evidence = await asyncio.gather(
        _retrieval_db_evidence(query_terms,topic_key),
        _retrieval_vector_evidence(query,topic_key)
    )

    # 3.将两个通道的结果组装一起，最终返回
    return [*db_evidence,*vector_evidence]

async def _retrieval_db_evidence(query_terms:list[str],
                           topic_key:str)->list[RetrievedEvidence]:
    """
    职责：从MySQL通道中获取检索结果，基于模糊查询
    :param query_terms:
    :param topic_key:
    :return:
    """
    try:
        # 1.获取词项查询结果
        db_docs = await _query_terms(query_terms,topic_key)

        # 2.遍历
        documents_score:dict[str,float] = dict()
        document_by_id:dict[str,SourceDocument] = {}
        for term_docs in db_docs:
            for rank,term_doc in enumerate(term_docs,start=1):
                doc_id = term_doc.doc_id
                documents_score[doc_id] = documents_score.get(doc_id,0.0) + _compute_rank(rank)
                document_by_id.setdefault(doc_id,term_doc)

        return [
            RetrievedEvidence(
                document=document_by_id[doc_id],
                channel_scores={"db_channel":rank}
            ) for doc_id,rank in documents_score.items()
        ]
    except Exception as e:
        raise ValueError(f"MySQL通道检索失败，原因：{e}")





async def _retrieval_vector_evidence(query:str,
                                     topic_key:str)->list[RetrievedEvidence]:
    """
    职责：从Milvus通道中获取检索结果，基于相似性检索结果
    :param query:
    :param topic_key:
    :return:
    """
    # 1.获取Milvus通道检索的开关
    config_settings = get_config_settings()
    if not config_settings.INSIGHT_VECTOR_ENABLED:
        return []
    try:
        # 2.异步查询Milvus获取检索结果
        vector_docs = await asyncio.to_thread(call_vector,query,100,_build_filter_expr(topic_key))

        # 3.返回
        return [
            RetrievedEvidence(document=doc,
                              channel_scores={"vector_channel":_compute_rank(rank)}
                              ) for rank,doc in enumerate(vector_docs,start=1)
        ]
    except Exception as e:
        logging.warning(f"Milvus通道检索失败，原因：{e}，回退到MySQL通道")
        return []




def _extract_query_terms(query:str)->list[str]:
    """
    职责：对query原始问题进行分词
    :param query:
    :return:
    """
    terms:list[str] = []
    terms.append(query) # 原始问题保留

    for term in jieba.analyse.extract_tags(query,topK=4):
        if 2<=len(term)<=6 and term not in terms:
            terms.append(term)
    return terms


def _build_filter_expr(topic_key:str)->str:
    return f"topic_key == '{topic_key}'" #question: 为什么要加这个过滤条件？



def _compute_rank(rank:int)->float:
    score =  1.0 / rank
    return score



async def _query_terms(query_terms:list[str], topic_key:str)->list[list[SourceDocument]]:
    db_docs = await asyncio.gather(
        *[call_db(topic_key=topic_key, query_term=term) for term in query_terms]
    )
    return db_docs #question:这个地方也没看懂









