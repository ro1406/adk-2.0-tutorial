"""Pydantic schemas for structured intake and workflow state."""

from pydantic import BaseModel, Field


class ProcurementForm(BaseModel):
    """Structured procurement request extracted during multi-turn intake."""

    software_name: str = Field(description="Name of the software or SaaS product being requested.")
    cost: float = Field(description="Total cost in AED for the purchase (annual or one-time).")
    justification: str = Field(description="Business justification for why this software is needed.")
