from pathlib import Path

from sentiment_analyze_service.engines.contract.config import get_config_settings
from sentiment_analyze_service.engines.contract.role import RoleID


def get_report_dir(task_id:str,role:RoleID)->str:
    config = get_config_settings()
    log_dir = config.RUNTIME_DIR
    return str(Path(log_dir) / f"{task_id}" / f"{role}" / "report.md")
