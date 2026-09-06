from typing import List, Optional, Any
from pydantic import BaseModel, Field
from .classify_models import SafetyReportFields

class LiteratureSplitRequest(BaseModel):
    articleText: str
    filename: Optional[str] = ""
    tables: List[Any] = Field(default_factory=list)

class LiteratureCaseResult(BaseModel):
    caseIndex: int = 1
    isReportable: bool = True
    summary: str = Field(description="10-15 sentence plain-language summary of this case")
    relevanceReason: str = Field(description="One-line reason for reportability opinion")
    safetyReportFields: Optional[SafetyReportFields] = Field(default_factory=SafetyReportFields)

class LiteratureSplitResponse(BaseModel):
    filename: Optional[str] = ""
    cases: List[LiteratureCaseResult] = Field(default_factory=list)
