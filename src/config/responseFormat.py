from dataclasses import dataclass


@dataclass
class ResponseFormat:
    """Response schema for the agent."""

    target: str
    tool_used: str
    summary: str
    detailed_report: str
