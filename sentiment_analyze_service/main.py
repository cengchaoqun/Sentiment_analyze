import uvicorn

from sentiment_analyze_service.engines.contract.config import get_config_settings

if __name__ == '__main__':
    config = get_config_settings()

    uvicorn.run(app="app.app:app",
                host=config.HOST,
                port=config.PORT
                )