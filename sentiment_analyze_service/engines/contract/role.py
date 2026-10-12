from typing import Literal
from dataclasses import dataclass
RoleID = Literal["insight", "media", "host", "report"]




@dataclass(slots=True)
class RoleMetaData:
    """
    定义不同Agent角色的元信息
    """
    llm_config_prefix:str

ROLE_METADATA:dict[RoleID,RoleMetaData] = {
    "insight": RoleMetaData(llm_config_prefix="INSIGHT_AGENT"),
    "media": RoleMetaData(llm_config_prefix="MEDIA_AGENT"),
    "host": RoleMetaData(llm_config_prefix="HOST_AGENT"),
    "report": RoleMetaData(llm_config_prefix="REPORT_ENGINE"),
}