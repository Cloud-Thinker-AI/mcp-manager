import logging
from mcp_manager.server.globals import settings 

def setup_logging():
    # Remove all handlers associated with the root logger object.
    for handler in logging.root.handlers[:]:
        logging.root.removeHandler(handler)

    # Log file will be written to .cache/mcp_manager_daemon.log
    logging.basicConfig(
        level=logging.DEBUG,  # Use DEBUG to capture all logs
        format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
        handlers=[
            logging.FileHandler(settings.LOG_FILE, mode='a', encoding='utf-8'),
            logging.StreamHandler()
        ],
        force=True  # Overwrites any prior logging config (Python 3.8+)
    )

    # Ensure uvicorn loggers use the same handlers and level
    for name in ("uvicorn", "uvicorn.error", "uvicorn.access"):
        logger = logging.getLogger(name)
        logger.handlers.clear()
        for handler in logging.getLogger().handlers:
            logger.addHandler(handler)
        logger.setLevel(logging.DEBUG)
        logger.propagate = True  # Ensure propagation to root