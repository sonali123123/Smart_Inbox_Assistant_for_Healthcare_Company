export interface Classification {
  id: number;
  category: string; // 'SAFETY_REPORT' | 'QUALITY_COMPLAINT' | 'INFO_REQUEST' | 'NOT_RELEVANT'
  confidence: number;
  reason: string;
  reviewerStatus: string; // 'PENDING' | 'ACCEPTED' | 'OVERRIDDEN'
}

export interface ExtractedField {
  id: number;
  attachmentId?: number;
  fieldGroup: string;
  fieldName: string;
  fieldValue: string;
  confidence?: number;
  sourceType?: string; // 'EMAIL' | 'PDF_PAGE'
  sourceRef?: string;
  reviewerEdited: boolean;
}

export interface PdfTable {
  id: number;
  pageNumber: number;
  tableJson: string;
  parsedRows?: any[][];
}

export interface PdfImage {
  id: number;
  pageNumber: number;
  description: string;
  reviewFlag: boolean;
}

export interface PdfTranslation {
  id: number;
  sourceLanguage: string;
  originalTextRef: string;
  translatedText: string;
}

export interface PdfSummary {
  id: number;
  summaryText: string;
  relevanceOpinion: string;
  relevanceReason: string;
}

export interface Attachment {
  id: number;
  filename: string;
  contentType: string;
  isPdf?: boolean;
  pdf?: boolean;
  pdfType?: string; // 'DIGITAL' | 'SCANNED' | 'ARTICLE' | 'NON_ENGLISH'
  loggedOnly: boolean;
  summary?: PdfSummary;
  tables?: PdfTable[];
  images?: PdfImage[];
  translation?: PdfTranslation;
}

export interface ReviewAction {
  id: number;
  reviewerName: string;
  action: string;
  targetRef: string;
  previousValue?: string;
  newValue?: string;
  timestamp: string;
}

export interface MessageListItem {
  id: number;
  sourceType: string;
  sender: string;
  subject: string;
  receivedDate: string;
  classifications: Classification[];
  topSummary: string;
  status: string; // 'PENDING_REVIEW' | 'REVIEWED'
  attachmentCount: number;
  urgencyLevel?: 'CRITICAL' | 'WARNING' | 'INFO' | 'ROUTINE';
  slaRemainingText?: string;
  slaExpired?: boolean;
  patientSnippet?: string;
  productSnippet?: string;
}

export interface BatchSummaryMetrics {
  totalDocs: number;
  completedDocs: number;
  failedDocs: number;
  processingDocs: number;
  avgDurationMs: number;
  totalDurationMs: number;
  successRate: number;
}

export interface MessageDetail {
  id: number;
  sourceType: string;
  sender: string;
  subject: string;
  receivedDate: string;
  bodyText: string;
  messageIdHeader: string;
  createdAt: string;
  status: string;
  classifications: Classification[];
  attachments: Attachment[];
  extractedFields: ExtractedField[];
  reviewActions: ReviewAction[];
}

export interface AuditLogEntry {
  id: number;
  entityType: string;
  entityId: number;
  action: string;
  actor: string;
  detailsJson?: string;
  timestamp: string;
}

export interface BatchStatusResponse {
  batchId: string;
  documents: {
    filename: string;
    status: string;
    durationMs?: number;
    errorMessage?: string;
    messageId?: number;
  }[];
}
