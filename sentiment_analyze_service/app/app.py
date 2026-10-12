from fastapi import FastAPI

from sentiment_analyze_service.app.exceptions.exception_handlers import register_exception_handlers
from sentiment_analyze_service.app.routers.hello import router
from sentiment_analyze_service.app.routers import system

app = FastAPI(description="FastAPI实例")

app.include_router(router)
app.include_router(system.router)


register_exception_handlers(app)