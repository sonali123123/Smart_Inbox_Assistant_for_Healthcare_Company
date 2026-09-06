from typing import List, Optional, Any
from pydantic import BaseModel, Field

class EmailContext(BaseModel):
    subject: Optional[str] = ""
    bodySnippet: Optional[str] = ""

class ProcessDocumentRequest(BaseModel):
    pdfBase64: str
    filename: str
    emailContext: Optional[EmailContext] = Field(default_factory=EmailContext)

class TableData(BaseModel):
    page: Optional[int] = 1
    rows: List[List[Any]] = Field(default_factory=list)

class ImageData(BaseModel):
    page: Optional[int] = 1
    description: str
    reviewFlag: bool = True

class TranslationData(BaseModel):
    sourceLanguage: str
    originalTextRef: Optional[str] = "page:1"
    translatedText: str

class ProcessDocumentResponse(BaseModel):
    pdfType: str = Field(description="DIGITAL | SCANNED | ARTICLE | NON_ENGLISH")
    ocrConfidence: Optional[float] = Field(default=None, description="0.0-1.0 float confidence for scanned/OCR")
    extractedText: str = Field(description="Structured full text with label:value pairing")
    tables: List[TableData] = Field(default_factory=list)
    images: List[ImageData] = Field(default_factory=list)
    translation: Optional[TranslationData] = None
    summary: str = Field(description="10-15 sentence comprehensive summary")
    relevanceOpinion: str = Field(description="RELEVANT | NOT_RELEVANT | UNCLEAR")
    relevanceReason: str = Field(description="One-line human-readable reason")
