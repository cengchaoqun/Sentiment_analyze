from datetime import datetime
from typing import Any, Dict

from sentiment_analyze_service.engines.agent.insight.tools.db.sql_statement import db_sql_statement, \
    topic_keys_sql_statement
from sentiment_analyze_service.engines.contract.evidence import SourceDocument, ENGAGEMENT_FIELDS
from sentiment_analyze_service.engines.infra.mysql import connection_manager




async def call_db(
        topic_key: str,
        query_term: str,
        limit: int = 100
) -> list[SourceDocument]:
    """
    职责：从数据库中根据主题进行词项内容的模糊查询
    :param topic_key:
    :param query_term:
    :param limit:
    :return:
    """
    # 1.获取SQL语句
    sql_statement = db_sql_statement()

    # 2.构建查询参数
    query_params: Dict[str, Any] = {
        "topic_key": topic_key,
        "search_term": f"%{query_term}%",  # 筛选内容中包含“query_term”的记录
        "raw_search_term": query_term, # 排序时，让内容完全等于“query_term”的记录优先
        "prefix_search_term": f"{query_term}%",  # 排序时，让以“query_term”开头的记录其次
        "limit": limit
    }

    # 3.执行SQL语句(list[dict[str,Any]])
    rows: list[dict[str, Any]] = await _get_db_rows(sql_statement, query_params)

    # 4.处理结果
    return [_mapping_row_to_document(row) for row in rows]


async def list_topic_keys() -> list[str]:
    """读取原帖采集关键词"""
    rows = await _get_db_rows(topic_keys_sql_statement(),{})
    return [row["topic_key"] for row in rows]

async def _get_db_rows(sql_statement: str,
                       query_params: Dict[str, Any]) -> list[dict[str, Any]]:
    """
    职责：执行SQL语句查询，返回数据库的字典对象列表
    :param sql_statement:
    :param query_params:
    :return:
    """
    # 1.获取Session工厂
    session_factory =connection_manager.get_async_session_factory()
    async with session_factory() as session:
        cursor_result = await session.execute(sql_statement,query_params)
        return [dict(row_mapping) for row_mapping in cursor_result.mappings().all()]






def _mapping_row_to_document(row: dict[str, Any]) -> SourceDocument:
    return SourceDocument(
        platform=row["platform"],
        source_type=row["source_type"],
        source_id=row["mysql_primary_key"],
        content=row.get("content") or "",
        published_at=datetime.fromtimestamp(int(row["published_at"])),
        engagement_counts={
            filed:float(row[f"eng_{filed}"]) for filed in ENGAGEMENT_FIELDS
        },
        hotness=float(row["hotness"]),
        url=row.get("url") or "",
        title=row.get("title") or "",
    )






















