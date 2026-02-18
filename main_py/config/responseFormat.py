from pydantic import BaseModel, Field


class ResponseFormat(BaseModel):
    target: str = Field(description="The target of the investigation")
    tool_used: str = Field(description="The name of the tool used")
    summary: str = Field(description="Brief summary of the findings")
    detailed_report: str = Field(description="The long-form investigative report")
