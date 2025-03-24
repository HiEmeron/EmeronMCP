from loguru import logger

# Configure logger settings
logger.add("emeron_mcp_server.log", level="INFO")

# You can define custom formats or sinks as needed
logger_format = "{time} - {level} - {message}"

logger.configure(handlers=[{"sink": "emeron_mcp_server.log", "format": logger_format, "level": "INFO"}])

# Export the logger instance
logger = logger  # This line is optional, but makes it explicitly clear what's being exported
