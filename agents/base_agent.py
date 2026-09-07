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


def make_audit_node(title: str, level_a: str, level_b: str, level_c: str, level_d: str) -> Dict[str, str]:
    """
    Constructs an institutional 4-tier audit parameter node.
    - Level A (historical_trend_and_metrics): Historical 3-to-5-year trajectory, specific figures, bps shifts.
    - Level B (operational_mechanics_and_drivers): Operational mechanics, business drivers, mix shifts, pass-through.
    - Level C (competitive_context_and_benchmarks): Peer group benchmarking, industry standards, relative moat.
    - Level D (thesis_implication_and_risks): Long-term compounding, RoA/RoE impact, multiples, downside risks.
    """
    return {
        "title": title.strip(),
        "historical_trend_and_metrics": level_a.strip(),
        "operational_mechanics_and_drivers": level_b.strip(),
        "competitive_context_and_benchmarks": level_c.strip(),
        "thesis_implication_and_risks": level_d.strip()
    }

