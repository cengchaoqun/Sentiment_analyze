from typing import Literal
from dataclasses import dataclass
RoleID = Literal["insight", "media", "host", "report"]




@dataclass(slots=True)
class RoleMetaData:
    """
    定义不同Agent角色的元信息
    """
    llm_config_prefix:str
    display_name:str

ROLE_METADATA: dict[RoleID, RoleMetaData] = {
    "insight": RoleMetaData(llm_config_prefix="INSIGHT_AGENT", display_name="私域检索专家"),
    "media": RoleMetaData(llm_config_prefix="MEDIA_AGENT", display_name="公域检索专家"),
    "host": RoleMetaData(llm_config_prefix="HOST_AGENT", display_name="研判专家"),
    "report": RoleMetaData(llm_config_prefix="REPORT_ENGINE", display_name="报告引擎")
}



def get_role_display_name(role_id:RoleID)->str:
    """返回角色的中文展示名"""
    return ROLE_METADATA[role_id].display_name
