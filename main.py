"""Main application entry point for the AI Assistant System."""

import uvicorn
from loguru import logger

from app.config import settings
from app.api.endpoints import app


def setup_logging():
    """Configure logging for the application."""
    logger.remove()  # Remove default handler
    
    # Add console logging
    logger.add(
        sink=lambda msg: print(msg, end=""),
        level=settings.log_level,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        colorize=True
    )
    
    # Add file logging
    logger.add(
        settings.log_file,
        level=settings.log_level,
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        rotation="10 MB",
        retention="30 days"
    )


def main():
    """Main application entry point."""
    setup_logging()
    
    logger.info("=" * 60)
    logger.info("🤖 AI ASSISTANT SYSTEM")
    logger.info("=" * 60)
    logger.info("A modular, intelligent backend platform")
    logger.info("Powered by FastAPI with multi-agent architecture")
    logger.info("=" * 60)
    
    logger.info("🚀 Starting server...")
    logger.info(f"📍 Host: {settings.host}")
    logger.info(f"🔌 Port: {settings.port}")
    logger.info(f"🐛 Debug: {settings.debug}")
    logger.info(f"📊 API Documentation: http://{settings.host}:{settings.port}/docs")
    logger.info("=" * 60)
    
    # Run the FastAPI application
    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        log_level=settings.log_level.lower(),
        access_log=True
    )


if __name__ == "__main__":
    main()