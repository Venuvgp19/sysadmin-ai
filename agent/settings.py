"""Agent configuration and settings."""

import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.resolve()

AGENT_CONFIG = {
    "model": os.environ.get("SYSADMIN_MODEL", "tinyllama"),  # Use local tinyllama for fast responses
    "ollama_host": os.environ.get("OLLAMA_HOST", "http://localhost:11434"),
    "logs_dir": PROJECT_ROOT / "logs",
    "knowledge_dir": PROJECT_ROOT / "knowledge",
    "vector_db_dir": PROJECT_ROOT / "vector_db",
    "max_command_timeout": int(os.environ.get("SYSADMIN_TIMEOUT", "30")),
    "max_output_length": int(os.environ.get("SYSADMIN_MAX_OUTPUT", "5000")),
}
