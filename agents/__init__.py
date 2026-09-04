"""
Equity Multi-Agent Architecture Package
Exports Agents 0 through 6 and the Master Pipeline.
"""

from agents.base_agent import BaseAgent
from agents.agent0_classifier import Agent0Classifier
from agents.agent1_qualitative import Agent1Qualitative
from agents.agent2_forensics import Agent2Forensics
from agents.agent3_solvency import Agent3Solvency
from agents.agent4_governance import Agent4Governance
from agents.agent5_industry_kpi import Agent5IndustryKPI
from agents.agent6_synthesizer import Agent6Synthesizer
from agents.pipeline import EquityAgentPipeline

# Backward compatibility alias
Agent1Forensics = Agent1Qualitative
Agent5Synthesizer = Agent6Synthesizer

__all__ = [
    "BaseAgent",
    "Agent0Classifier",
    "Agent1Qualitative",
    "Agent2Forensics",
    "Agent3Solvency",
    "Agent4Governance",
    "Agent5IndustryKPI",
    "Agent6Synthesizer",
    "EquityAgentPipeline"
]
