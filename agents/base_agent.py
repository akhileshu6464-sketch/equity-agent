"""
Base Agent Definition
Provides standard interface, risk pill scoring schema, prompt loading, and execution contract.
"""

import os
from abc import ABC, abstractmethod
from typing import Dict, Any, Literal

RiskLevel = Literal["GREEN", "YELLOW", "RED"]


class BaseAgent(ABC):
    """Abstract base class for all equity analysis agents."""

    def __init__(self, name: str, role: str, prompt_file: str = ""):
        self.name = name
        self.role = role
        self.prompt_file = prompt_file
        self.system_prompt = self.load_prompt(prompt_file) if prompt_file else ""

    def load_prompt(self, filename: str) -> str:
        """Dynamically loads system prompt from the corresponding .txt file."""
        if not filename:
            return ""
        current_dir = os.path.dirname(os.path.abspath(__file__))
        file_path = os.path.join(current_dir, filename)
        if os.path.exists(file_path):
            with open(file_path, "r", encoding="utf-8") as f:
                return f.read().strip()
        return ""

    @abstractmethod
    def analyze(self, company_data: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Executes domain audit and returns structured findings.
        Must return a dictionary containing:
        - agent_name: str
        - risk_pill: 'GREEN' | 'YELLOW' | 'RED'
        - summary: str
        - audit_metrics: Dict[str, Any]
        - flags: List[str]
        """
        pass
