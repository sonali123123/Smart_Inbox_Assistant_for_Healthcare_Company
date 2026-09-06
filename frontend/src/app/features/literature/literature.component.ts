import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule, Router } from '@angular/router';
import { MatCardModule } from '@angular/material/card';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatProgressBarModule } from '@angular/material/progress-bar';
import { MatSnackBar, MatSnackBarModule } from '@angular/material/snack-bar';
import { MatTableModule } from '@angular/material/table';
import { MatTabsModule } from '@angular/material/tabs';

import { LiteratureService } from '../../core/services/literature.service';
import { MessageListItem } from '../../core/models/message.model';

@Component({
  selector: 'app-literature',
  standalone: true,
  imports: [
    CommonModule,
    RouterModule,
    MatCardModule,
    MatButtonModule,
    MatIconModule,
    MatProgressBarModule,
    MatSnackBarModule,
    MatTableModule,
    MatTabsModule
  ],
  templateUrl: './literature.component.html',
  styleUrls: ['./literature.component.scss']
})
export class LiteratureComponent {
  selectedFiles: File[] = [];
  uploading = false;
  batchId: string | null = null;
  cases: MessageListItem[] = [];
  isDraggingOver = false;

  displayedColumns = ['id', 'subject', 'status', 'summary', 'action'];

  constructor(
    private literatureService: LiteratureService,
    private router: Router,
    private snackBar: MatSnackBar
  ) {}

  onFilesSelected(event: any): void {
    const files = event.target.files;
    if (files) {
      this.selectedFiles = Array.from(files);
    }
  }

  onDragOver(event: DragEvent): void {
    event.preventDefault();
    event.stopPropagation();
    this.isDraggingOver = true;
  }

  onDragLeave(event: DragEvent): void {
    event.preventDefault();
    event.stopPropagation();
    this.isDraggingOver = false;
  }

  onFileDrop(event: DragEvent): void {
    event.preventDefault();
    event.stopPropagation();
    this.isDraggingOver = false;

    if (event.dataTransfer?.files && event.dataTransfer.files.length > 0) {
      const droppedFiles = Array.from(event.dataTransfer.files).filter(f =>
        f.type === 'application/pdf' || f.name.toLowerCase().endsWith('.pdf')
      );
      if (droppedFiles.length > 0) {
        this.selectedFiles = droppedFiles;
        this.snackBar.open(`${droppedFiles.length} PDF file(s) attached via drag-and-drop!`, 'OK', { duration: 3000 });
      } else {
        this.snackBar.open('Please drop valid PDF article files.', 'Close', { duration: 3000 });
      }
    }
  }

  uploadAndScreen(): void {
    if (this.selectedFiles.length === 0) {
      this.snackBar.open('Please select at least one article PDF', 'OK', { duration: 3000 });
      return;
    }

    this.uploading = true;
    this.literatureService.uploadBatch(this.selectedFiles).subscribe({
      next: (res) => {
        this.batchId = res.batchId;
        this.snackBar.open(`Uploaded batch ${res.batchId}. Loading cases...`, 'OK', { duration: 3000 });
        this.loadCases(res.batchId);
      },
      error: (err) => {
        this.uploading = false;
        this.snackBar.open('Upload failed: ' + (err.error?.message || err.message), 'Close', { duration: 5000 });
      }
    });
  }

  loadCases(batchId: string): void {
    this.literatureService.getBatchCases(batchId).subscribe({
      next: (res) => {
        this.cases = res.cases;
        this.uploading = false;
        this.snackBar.open(`Identified and split ${res.totalCases} cases!`, 'OK', { duration: 4000 });
      },
      error: (err) => {
        this.uploading = false;
        this.snackBar.open('Failed to load batch cases', 'Close', { duration: 4000 });
      }
    });
  }

  get reportableCases(): MessageListItem[] {
    return this.cases.filter(c =>
      !c.subject.toLowerCase().includes('not_reportable') &&
      !c.topSummary.toLowerCase().includes('not reportable') &&
      !c.classifications?.some(cl => cl.category === 'NOT_RELEVANT')
    );
  }

  get excludedArticles(): MessageListItem[] {
    return this.cases.filter(c =>
      c.subject.toLowerCase().includes('not_reportable') ||
      c.topSummary.toLowerCase().includes('not reportable') ||
      c.classifications?.some(cl => cl.category === 'NOT_RELEVANT')
    );
  }

  viewCase(item: MessageListItem): void {
    this.router.navigate(['/messages', item.id]);
  }
}

