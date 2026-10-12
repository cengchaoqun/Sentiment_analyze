from fastapi import APIRouter

from sentiment_analyze_service.app.dependencies import ResearchServiceDep
from sentiment_analyze_service.app.schemas.research import ResearchResponse, ResearchRequest

router = APIRouter(prefix="/api/research",tags=["研究路由"])

@router.post("",response_model=ResearchResponse)
async def start_research_endpoint(payload:ResearchRequest,service:ResearchServiceDep):
    task_id = service.start_research(payload.query)
    return ResearchResponse(task_id=task_id)


