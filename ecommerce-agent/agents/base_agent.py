"""Abstract base class for all marketing agents."""

import time
from abc import ABC, abstractmethod


class BaseAgent(ABC):
    def __init__(self, db_manager, claude_service, config: dict = None):
        self.db = db_manager
        self.claude = claude_service
        self.config = config or {}
        self.agent_name = self.__class__.__name__.replace("Agent", "").lower()

    @abstractmethod
    def run(self, **kwargs) -> dict:
        ...

    def log_run(
        self,
        status: str,
        input_summary: str = "",
        output_summary: str = "",
        duration_ms: int = 0,
        error: str = None,
    ):
        self.db.insert("agent_runs", {
            "agent_name": self.agent_name,
            "status": status,
            "input_summary": input_summary[:500],
            "output_summary": output_summary[:1000],
            "duration_ms": duration_ms,
            "error": error,
        })
