import sys
from loguru import logger
from app.config import settings

class Logger:
    def __init__(self):
        # Remove default handler
        logger.remove()
        
        # Console handler
        logger.add(
            sys.stdout,
            format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
            level="INFO" if not settings.DEBUG else "DEBUG",
            colorize=True
        )
        
        # File handler
        logger.add(
            "logs/oxlas.log",
            format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
            level="INFO",
            rotation="10 MB",
            retention="30 days",
            compression="zip",
            serialize=False
        )
        
        # Error file handler
        logger.add(
            "logs/oxlas_errors.log",
            format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
            level="ERROR",
            rotation="10 MB",
            retention="90 days",
            compression="zip",
            serialize=False
        )
    
    def get_logger(self, name: str = None):
        if name:
            return logger.bind(name=name)
        return logger

# Initialize logger
app_logger = Logger()

def get_logger(name: str = None):
    """Get logger instance"""
    return app_logger.get_logger(name)