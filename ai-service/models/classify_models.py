from typing import List, Optional, Any, Dict
from pydantic import BaseModel, Field

class PdfExtractionItem(BaseModel):
    attachmentId: int
    extractedText: str = ""
    tables: List[Any] = Field(default_factory=list)

class ClassifyRequest(BaseModel):
    emailBody: str
    sender: str = ""
    subject: str = ""
    pdfExtractions: List[PdfExtractionItem] = Field(default_factory=list)

class ClassificationItem(BaseModel):
    category: str = Field(description="SAFETY_REPORT | QUALITY_COMPLAINT | INFO_REQUEST | NOT_RELEVANT")
    confidence: float = Field(description="0.0-1.0 confidence")
    reason: str = Field(description="One-line human-readable reason")

class FieldValue(BaseModel):
    value: str = Field(default="Not stated")
    confidence: Optional[float] = Field(default=None)
    sourceRef: Optional[str] = Field(default=None, description="'email' or 'attachment:{id},page:{n}'")

class PatientFields(BaseModel):
    age: FieldValue = Field(default_factory=lambda: FieldValue(value="Not stated"))
    sex: FieldValue = Field(default_factory=lambda: FieldValue(value="Not stated"))
    weightHeight: FieldValue = Field(default_factory=lambda: FieldValue(value="Not stated"))
    relevantHistory: FieldValue = Field(default_factory=lambda: FieldValue(value="Not stated"))

class ReporterFields(BaseModel):
    name: FieldValue = Field(default_factory=lambda: FieldValue(value="Not stated"))
    role: FieldValue = Field(default_factory=lambda: FieldValue(value="Not stated"))
    country: FieldValue = Field(default_factory=lambda: FieldValue(value="Not stated"))

class ProductFields(BaseModel):
    name: FieldValue = Field(default_factory=lambda: FieldValue(value="Not stated"))
    dose: FieldValue = Field(default_factory=lambda: FieldValue(value="Not stated"))
    route: FieldValue = Field(default_factory=lambda: FieldValue(value="Not stated"))
    startDate: FieldValue = Field(default_factory=lambda: FieldValue(value="Not stated"))
    stopDate: FieldValue = Field(default_factory=lambda: FieldValue(value="Not stated"))

class ReactionFields(BaseModel):
    description: FieldValue = Field(default_factory=lambda: FieldValue(value="Not stated"))
    onset: FieldValue = Field(default_factory=lambda: FieldValue(value="Not stated"))
    outcome: FieldValue = Field(default_factory=lambda: FieldValue(value="Not stated"))

class SeverityFields(BaseModel):
    level: FieldValue = Field(default_factory=lambda: FieldValue(value="Not stated"))

class SafetyReportFields(BaseModel):
    patient: Optional[PatientFields] = Field(default_factory=PatientFields)
    reporter: Optional[ReporterFields] = Field(default_factory=ReporterFields)
    product: Optional[ProductFields] = Field(default_factory=ProductFields)
    reaction: Optional[ReactionFields] = Field(default_factory=ReactionFields)
    severity: Optional[SeverityFields] = Field(default_factory=SeverityFields)
    narrative: Optional[FieldValue] = Field(default_factory=lambda: FieldValue(value="Not stated"))

class QualityComplaintFields(BaseModel):
    productBatchLot: FieldValue = Field(default_factory=lambda: FieldValue(value="Not stated"))
    defectDescription: FieldValue = Field(default_factory=lambda: FieldValue(value="Not stated"))
    photoMentioned: FieldValue = Field(default_factory=lambda: FieldValue(value="Not stated"))

class InfoRequestQuestion(BaseModel):
    question: str
    productTopic: str = "Not stated"
    confidence: Optional[float] = 0.9
    sourceRef: Optional[str] = "email"

class InfoRequestFields(BaseModel):
    questions: List[InfoRequestQuestion] = Field(default_factory=list)

class ClassifyResponse(BaseModel):
    classifications: List[ClassificationItem] = Field(default_factory=list)
    safetyReportFields: Optional[SafetyReportFields] = None
    qualityComplaintFields: Optional[QualityComplaintFields] = None
    infoRequestFields: Optional[InfoRequestFields] = None
