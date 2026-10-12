from sentiment_analyze_service.engines.common.llm import LLMClient


async def invoke_insight_agent(
        role:str,
        query:str,
        task_id:str,
        llm_client:LLMClient,
        output_dir:str
):
    # 驱动insight Agent定义的langgraph图
    pass
