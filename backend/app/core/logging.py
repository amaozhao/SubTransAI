import logging
import sys
import os
from typing import Dict, Any, Optional
import structlog
from structlog.types import Processor

from app.core.config import settings


def configure_logging():
    """Configure structured logging for the application."""
    
    # Create logs directory if it doesn't exist
    os.makedirs("logs", exist_ok=True)
    
    # Configure standard logging
    logging.basicConfig(
        format="%(message)s",
        level=logging.INFO,
        handlers=[logging.NullHandler()]
    )
    
    # Define shared processors for all loggers
    shared_processors = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
    ]
    
    # Configure structlog
    structlog.configure(
        processors=shared_processors + [
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )
    
    # Create formatters
    json_formatter = structlog.stdlib.ProcessorFormatter(
        processor=structlog.processors.JSONRenderer(),
        foreign_pre_chain=shared_processors,
    )
    
    console_formatter = structlog.stdlib.ProcessorFormatter(
        processor=structlog.dev.ConsoleRenderer(colors=True),
        foreign_pre_chain=shared_processors,
    )
    
    # Create handlers for different log categories
    handlers = {
        "api": create_file_handler("logs/api.log", json_formatter),
        "service": create_file_handler("logs/service.log", json_formatter),
        "db": create_file_handler("logs/db.log", json_formatter),
        "console": create_console_handler(console_formatter),
    }
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.handlers = [handlers["console"]]
    root_logger.setLevel(logging.INFO)
    
    # Configure specific loggers
    configure_logger("app.api", [handlers["api"], handlers["console"]])
    configure_logger("app.services", [handlers["service"], handlers["console"]])
    configure_logger("app.db", [handlers["db"], handlers["console"]])
    
    # Configure SQLAlchemy logger
    configure_logger("sqlalchemy.engine", [handlers["db"]])


def create_file_handler(filename: str, formatter) -> logging.Handler:
    """Create a file handler for the given filename and formatter."""
    handler = logging.FileHandler(filename)
    handler.setFormatter(formatter)
    return handler


def create_console_handler(formatter) -> logging.Handler:
    """Create a console handler with the given formatter."""
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)
    return handler


def configure_logger(name: str, handlers: list) -> None:
    """Configure a logger with the given name and handlers."""
    logger = logging.getLogger(name)
    logger.handlers = handlers.copy()
    logger.propagate = False
    logger.setLevel(logging.INFO)


def get_logger(name: Optional[str] = None) -> structlog.stdlib.BoundLogger:
    """Get a structured logger with the given name.
    
    Args:
        name: Optional name for the logger. If not provided, the module name will be used.
              Use dot notation to categorize logs (e.g., "app.api.users").
    
    Returns:
        A structured logger instance.
    """
    if name is None:
        # Get the caller's module name
        import inspect
        frame = inspect.currentframe().f_back
        module = inspect.getmodule(frame)
        name = module.__name__ if module else "unknown"
    
    # Add request_id from context if available
    from contextvars import ContextVar
    request_id_var: ContextVar[str] = ContextVar("request_id", default="")
    request_id = request_id_var.get()
    
    logger = structlog.stdlib.get_logger(name)
    if request_id:
        logger = logger.bind(request_id=request_id)
    
    return logger
