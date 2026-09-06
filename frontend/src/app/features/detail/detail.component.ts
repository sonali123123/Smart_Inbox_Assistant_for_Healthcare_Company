import { Component, OnInit, HostListener } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ActivatedRoute, Router, RouterModule } from '@angular/router';
import { MatCardModule } from '@angular/material/card';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatSelectModule } from '@angular/material/select';
import { MatExpansionModule } from '@angular/material/expansion';
import { MatDividerModule } from '@angular/material/divider';
import { MatSnackBar, MatSnackBarModule } from '@angular/material/snack-bar';
import { MatProgressBarModule } from '@angular/material/progress-bar';
import { MatDialogModule } from '@angular/material/dialog';
import { MatTabsModule } from '@angular/material/tabs';
import { MatTooltipModule } from '@angular/material/tooltip';
import { MatChipsModule } from '@angular/material/chips';

import { MessageService } from '../../core/services/message.service';
import { ReviewService } from '../../core/services/review.service';
import { MessageDetail, ExtractedField, Classification, Attachment } from '../../core/models/message.model';
import { SafeUrlPipe } from '../../core/pipes/safe-url.pipe';

@Component({
  selector: 'app-detail',
  standalone: true,
  imports: [
    CommonModule,
    FormsModule,
    RouterModule,
    MatCardModule,
    MatButtonModule,
    MatIconModule,
    MatFormFieldModule,
    MatInputModule,
    MatSelectModule,
    MatExpansionModule,
    MatDividerModule,
    MatSnackBarModule,
    MatProgressBarModule,
    MatDialogModule,
    MatTabsModule,
    MatTooltipModule,
    MatChipsModule,
    SafeUrlPipe
  ],
  templateUrl: './detail.component.html',
  styleUrls: ['./detail.component.scss']
})
export class DetailComponent implements OnInit {
  messageId!: number;
  message: MessageDetail | null = null;
  loading = false;
  savingFieldId: number | null = null;
  reviewerName = 'Dr. Sarah Lin (Safety Officer)';

  // Left Pane Evidence State
  selectedLeftTab = 0;
  selectedAttachment: Attachment | null = null;
  activePdfUrl: string | null = null;
  activePdfTitle: string | null = null;
  activePageNumber: number | null = null;

  // Override dialog state
  overrideTargetClassification: Classification | null = null;
  overrideNewCategory = 'QUALITY_COMPLAINT';

  // GxP Reason for Change Modal state
  reasonPromptField: ExtractedField | null = null;
  selectedReason = 'Correction of OCR / AI extraction';
  customReason = '';
  standardReasons: string[] = [
    'Correction of OCR / AI extraction',
    'Information clarified via physician follow-up',
    'Standardized to MedDRA preferred terminology',
    'Discrepancy resolved via primary document check',
    'Other clinical rationale'
  ];

  // Original field values tracking for Undo/Cancel
  fieldOriginalValues: { [key: number]: string } = {};

  // Controlled Vocabularies
  sexOptions = ['Male', 'Female', 'Unknown', 'Not stated'];
  severityOptions = ['Hospitalization', 'Fatal', 'Life-threatening', 'Disability', 'Congenital Anomaly', 'Other Medically Important', 'Not stated'];
  routeOptions = ['Oral', 'Intravenous', 'Intramuscular', 'Subcutaneous', 'Topical', 'Inhalation', 'Not stated'];

  constructor(
    private route: ActivatedRoute,
    private router: Router,
    public messageService: MessageService,
    private reviewService: ReviewService,
    private snackBar: MatSnackBar
  ) {}

  ngOnInit(): void {
    const savedReviewer = localStorage.getItem('pv_reviewer_name');
    if (savedReviewer) {
      this.reviewerName = savedReviewer;
    }

    this.route.paramMap.subscribe(params => {
      const id = params.get('id');
      if (id) {
        this.messageId = Number(id);
        this.loadMessage();
      }
    });
  }

  saveReviewerIdentity(): void {
    if (this.reviewerName) {
      localStorage.setItem('pv_reviewer_name', this.reviewerName.trim());
      this.snackBar.open('Reviewer identity saved for audit logging', 'OK', { duration: 2500 });
    }
  }

  @HostListener('window:keydown', ['$event'])
  handleKeyboardShortcuts(event: KeyboardEvent): void {
    if (event.altKey && (event.key === 'a' || event.key === 'A')) {
      event.preventDefault();
      this.acceptAllClassifications();
    } else if (event.altKey && (event.key === 'o' || event.key === 'O')) {
      event.preventDefault();
      if (this.message?.classifications && this.message.classifications.length > 0) {
        this.openOverrideDialog(this.message.classifications[0]);
      }
    } else if (event.altKey && (event.key === 'Enter' || event.key === 'n' || event.key === 'N')) {
      event.preventDefault();
      this.approveAndNextCase();
    } else if (event.altKey && (event.key === 'q' || event.key === 'Q')) {
      event.preventDefault();
      this.router.navigate(['/messages']);
    } else if (event.key === 'Escape') {
      if (this.reasonPromptField) {
        this.cancelReasonPrompt();
      } else if (this.overrideTargetClassification) {
        this.cancelOverride();
      }
    }
  }

  loadMessage(): void {
    this.loading = true;
    this.messageService.getMessage(this.messageId).subscribe({
      next: (data) => {
        this.message = data;
        this.loading = false;

        // Cache original field values
        if (this.message.extractedFields) {
          for (const f of this.message.extractedFields) {
            this.fieldOriginalValues[f.id] = f.fieldValue;
          }
        }

        // Parse table rows if needed
        if (this.message.attachments) {
          for (const att of this.message.attachments) {
            if (att.tables) {
              for (const tbl of att.tables) {
                try {
                  tbl.parsedRows = JSON.parse(tbl.tableJson);
                } catch (e) {
                  tbl.parsedRows = [];
                }
              }
            }
          }

          // Default active attachment to first PDF (or first attachment if available)
          const firstPdf = this.message.attachments.find(a => this.isPdfAttachment(a));
          if (firstPdf) {
            this.selectAttachment(firstPdf);
          } else if (this.message.attachments.length > 0) {
            this.selectAttachment(this.message.attachments[0]);
          } else {
            // Default to email tab if no attachments
            this.selectedLeftTab = 1;
          }
        }
      },
      error: (err) => {
        this.loading = false;
        this.snackBar.open('Failed to load message detail', 'Close', { duration: 4000 });
      }
    });
  }

  isPdfAttachment(att: Attachment | null | undefined): boolean {
    if (!att) return false;
    if (att.isPdf === true || att.pdf === true) return true;
    if (att.contentType && att.contentType.toLowerCase().includes('pdf')) return true;
    if (att.filename && att.filename.toLowerCase().endsWith('.pdf')) return true;
    return false;
  }

  compareAttachments(a: Attachment, b: Attachment): boolean {
    return a && b ? a.id === b.id : a === b;
  }

  onTabChanged(index: number): void {
    this.selectedLeftTab = index;
    if (index === 0 && !this.selectedAttachment && this.message?.attachments && this.message.attachments.length > 0) {
      const firstPdf = this.message.attachments.find(a => this.isPdfAttachment(a)) || this.message.attachments[0];
      this.selectAttachment(firstPdf);
    }
  }

  selectAttachment(att: Attachment, pageNum?: number): void {
    if (!att) return;
    this.selectedAttachment = att;
    this.activePdfTitle = att.filename;
    this.activePageNumber = pageNum || 1;
    const baseFileUrl = this.messageService.getAttachmentFileUrl(att.id);
    this.activePdfUrl = pageNum ? `${baseFileUrl}#page=${pageNum}` : baseFileUrl;
    this.selectedLeftTab = 0; // Switch to PDF viewer tab
  }

  acceptClassification(c: Classification): void {
    this.reviewService.reviewClassification(this.messageId, c.id, 'ACCEPT', undefined, this.reviewerName).subscribe({
      next: () => {
        c.reviewerStatus = 'ACCEPTED';
        this.snackBar.open(`Classification ${c.category} Accepted`, 'OK', { duration: 2500 });
        this.loadMessage();
      },
      error: (err) => {
        this.snackBar.open('Failed to accept: ' + err.message, 'Close', { duration: 4000 });
      }
    });
  }

  acceptAllClassifications(): void {
    if (!this.message?.classifications) return;
    const pendingList = this.message.classifications.filter(c => c.reviewerStatus === 'PENDING');
    if (pendingList.length === 0) {
      this.snackBar.open('All classifications are already reviewed.', 'OK', { duration: 2500 });
      return;
    }

    let completed = 0;
    for (const c of pendingList) {
      this.reviewService.reviewClassification(this.messageId, c.id, 'ACCEPT', undefined, this.reviewerName).subscribe({
        next: () => {
          c.reviewerStatus = 'ACCEPTED';
          completed++;
          if (completed === pendingList.length) {
            this.snackBar.open(`All ${completed} classifications Accepted!`, 'OK', { duration: 3000 });
            this.loadMessage();
          }
        }
      });
    }
  }

  openOverrideDialog(c: Classification): void {
    this.overrideTargetClassification = c;
    this.overrideNewCategory = c.category === 'SAFETY_REPORT' ? 'QUALITY_COMPLAINT' : 'SAFETY_REPORT';
  }

  confirmOverride(): void {
    if (!this.overrideTargetClassification) return;
    const c = this.overrideTargetClassification;
    this.reviewService.reviewClassification(this.messageId, c.id, 'OVERRIDE', this.overrideNewCategory, this.reviewerName).subscribe({
      next: () => {
        this.overrideTargetClassification = null;
        this.snackBar.open(`Classification Overridden to ${this.overrideNewCategory}`, 'OK', { duration: 3000 });
        this.loadMessage();
      },
      error: (err) => {
        this.snackBar.open('Failed to override: ' + err.message, 'Close', { duration: 4000 });
      }
    });
  }

  cancelOverride(): void {
    this.overrideTargetClassification = null;
  }

  promptEditField(field: ExtractedField): void {
    const original = this.fieldOriginalValues[field.id];
    // If value changed from original, prompt for Reason for Change
    if (field.fieldValue !== original) {
      this.reasonPromptField = field;
      this.selectedReason = this.standardReasons[0];
      this.customReason = '';
    } else {
      // No change, just save directly
      this.executeSaveField(field, 'Confirmed unchanged');
    }
  }

  confirmSaveWithReason(): void {
    if (!this.reasonPromptField) return;
    const field = this.reasonPromptField;
    const reasonText = this.selectedReason === 'Other clinical rationale' && this.customReason.trim()
      ? this.customReason.trim()
      : this.selectedReason;

    this.executeSaveField(field, reasonText);
    this.reasonPromptField = null;
  }

  cancelReasonPrompt(): void {
    if (this.reasonPromptField) {
      // Revert to original cached value
      this.reasonPromptField.fieldValue = this.fieldOriginalValues[this.reasonPromptField.id];
      this.reasonPromptField = null;
    }
  }

  executeSaveField(field: ExtractedField, reason: string): void {
    this.savingFieldId = field.id;
    this.reviewService.editField(this.messageId, field.id, field.fieldValue, this.reviewerName, reason).subscribe({
      next: () => {
        this.savingFieldId = null;
        field.reviewerEdited = true;
        this.fieldOriginalValues[field.id] = field.fieldValue;
        this.snackBar.open(`Field "${field.fieldName}" updated`, 'OK', { duration: 2500 });
        this.loadMessage();
      },
      error: (err) => {
        this.savingFieldId = null;
        this.snackBar.open('Failed to update field: ' + err.message, 'Close', { duration: 4000 });
      }
    });
  }

  revertField(field: ExtractedField): void {
    const orig = this.fieldOriginalValues[field.id];
    if (orig !== undefined) {
      field.fieldValue = orig;
      this.snackBar.open(`Reverted "${field.fieldName}" to original value`, 'OK', { duration: 2000 });
    }
  }

  formatSourceRef(sourceRef?: string): string {
    if (!sourceRef) return '';
    const ref = sourceRef.trim();
    if (ref.toLowerCase() === 'email') return 'Email Body';

    const pageMatch = ref.match(/page[:=](\d+)/i);
    const pageStr = pageMatch ? `Page ${pageMatch[1]}` : '';

    if (ref.toLowerCase().startsWith('attachment:')) {
      const attMatch = ref.match(/attachment:([^,:]+)/i);
      const target = attMatch ? attMatch[1].trim() : '';
      if (target.toLowerCase().endsWith('.pdf')) {
        return pageStr ? `${pageStr} (${target})` : target;
      }
      return pageStr ? `PDF ${pageStr}` : ref;
    }
    return ref;
  }

  handleSourceNavigation(sourceRef?: string): void {
    if (!sourceRef) return;
    const ref = sourceRef.trim();

    if (ref.toLowerCase() === 'email') {
      this.selectedLeftTab = 1; // Switch to Email tab
      this.snackBar.open('Navigated to Raw Email Content', 'OK', { duration: 2000 });
      return;
    }

    if (ref.toLowerCase().startsWith('attachment:')) {
      const pageMatch = ref.match(/page[:=](\d+)/i);
      const pageNum = pageMatch ? Number(pageMatch[1]) : 1;

      const attMatch = ref.match(/attachment:([^,:]+)/i);
      const attTarget = attMatch ? attMatch[1].trim() : '';

      let matchedAtt: Attachment | undefined = undefined;
      if (/^\d+$/.test(attTarget)) {
        const attId = Number(attTarget);
        matchedAtt = this.message?.attachments?.find(a => a.id === attId);
      } else if (attTarget && this.message?.attachments) {
        matchedAtt = this.message.attachments.find(a => a.filename.toLowerCase().includes(attTarget.toLowerCase()));
      }

      // Fallback to first attachment if only one exists or none matched
      if (!matchedAtt && this.message?.attachments && this.message.attachments.length > 0) {
        matchedAtt = this.message.attachments[0];
      }

      if (matchedAtt) {
        this.selectAttachment(matchedAtt, pageNum);
        this.snackBar.open(`Navigated to ${matchedAtt.filename} (Page ${pageNum})`, 'OK', { duration: 2500 });
      } else {
        this.snackBar.open(`Source reference: ${ref}`, 'OK', { duration: 2000 });
      }
    }
  }

  approveAndNextCase(): void {
    // 1. Accept all classifications first
    if (this.message?.classifications) {
      const pendingList = this.message.classifications.filter(c => c.reviewerStatus === 'PENDING');
      for (const c of pendingList) {
        this.reviewService.reviewClassification(this.messageId, c.id, 'ACCEPT', undefined, this.reviewerName).subscribe();
      }
    }

    // 2. Fetch pending queue and route to the next pending item
    this.messageService.getMessages({ status: 'PENDING_REVIEW' }).subscribe({
      next: (res) => {
        const nextItem = res.items.find(m => m.id !== this.messageId);
        if (nextItem) {
          this.snackBar.open(`Approved! Opening next pending case #${nextItem.id}...`, 'OK', { duration: 2500 });
          this.router.navigate(['/messages', nextItem.id]);
        } else {
          this.snackBar.open('Review completed! All cases in queue are reviewed.', 'OK', { duration: 4000 });
          this.router.navigate(['/messages']);
        }
      },
      error: () => {
        this.router.navigate(['/messages']);
      }
    });
  }

  getFieldsByGroup(group: string): ExtractedField[] {
    if (!this.message?.extractedFields) return [];
    return this.message.extractedFields.filter(f => f.fieldGroup === group);
  }

  getConfidenceClass(confidence?: number): string {
    if (!confidence) return 'low';
    if (confidence >= 0.8) return 'high';
    if (confidence >= 0.5) return 'medium';
    return 'low';
  }

  hasTranslations(): boolean {
    return !!this.message?.attachments?.some(a => a.translation);
  }

  hasTables(): boolean {
    return !!this.message?.attachments?.some(a => a.tables && a.tables.length > 0);
  }

  hasImages(): boolean {
    return !!this.message?.attachments?.some(a => a.images && a.images.length > 0);
  }
}

