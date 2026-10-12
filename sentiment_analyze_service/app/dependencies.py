from typing import Annotated

from fastapi import Depends

from sentiment_analyze_service.app.servies.research import ResearchService
from sentiment_analyze_service.app.servies.system import SystemConfigService


def get_system_config_service():

    return SystemConfigService()

SystemConfigServiceDep = Annotated[SystemConfigService,Depends(get_system_config_service)]

def get_research_service():
    return ResearchService()

ResearchServiceDep = Annotated[ResearchService,Depends(get_research_service)]