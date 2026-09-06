import { Component, OnDestroy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { RouterModule } from '@angular/router';
import { MatCardModule } from '@angular/material/card';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatTableModule } from '@angular/material/table';
import { MatProgressBarModule } from '@angular/material/progress-bar';
import { MatSnackBar, MatSnackBarModule } from '@angular/material/snack-bar';

import { BatchService } from '../../core/services/batch.service';
import { BatchStatusResponse, BatchSummaryMetrics } from '../../core/models/message.model';
import { Router } from '@angular/router';

@Component({
  selector: 'app-batch',
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
    MatTableModule,
    MatProgressBarModule,
    MatSnackBarModule
  ],
  templateUrl: './batch.component.html',
  styleUrls: ['./batch.component.scss']
})
export class BatchComponent implements OnDestroy {
  sourceDir = 'test-data/emails';
  running = false;
  batchId: string | null = null;
  batchStatus: BatchStatusResponse | null = null;
  metrics: BatchSummaryMetrics | null = null;
  displayedColumns = ['filename', 'status', 'durationMs', 'actions'];

  private pollInterval: any;

  constructor(
    private batchService: BatchService,
    private snackBar: MatSnackBar,
    private router: Router
  ) {}

  runBatch(): void {
    this.running = true;
    this.batchStatus = null;
    this.metrics = null;
    this.batchService.runBatch(this.sourceDir).subscribe({
      next: (res) => {
        this.batchId = res.batchId;
        this.snackBar.open(`Batch started with ID: ${res.batchId}`, 'OK', { duration: 3000 });
        this.startPolling(res.batchId);
      },
      error: (err) => {
        this.running = false;
        this.snackBar.open('Batch run error: ' + (err.error?.message || err.message), 'Close', { duration: 5000 });
      }
    });
  }

  startPolling(batchId: string): void {
    this.stopPolling();
    this.fetchStatus(batchId);
    this.pollInterval = setInterval(() => this.fetchStatus(batchId), 2500);
  }

  fetchStatus(batchId: string): void {
    this.batchService.getBatchStatus(batchId).subscribe({
      next: (status) => {
        this.batchStatus = status;
        this.computeMetrics(status);
        const allDone = status.documents.length > 0 && status.documents.every(d => d.status === 'DONE' || d.status === 'FAILED');
        if (allDone) {
          this.running = false;
          this.stopPolling();
          this.snackBar.open('Batch processing completed for all documents!', 'OK', { duration: 4000 });
        }
      },
      error: () => this.stopPolling()
    });
  }

  computeMetrics(status: BatchStatusResponse): void {
    const docs = status.documents || [];
    const total = docs.length;
    const completed = docs.filter(d => d.status === 'DONE').length;
    const failed = docs.filter(d => d.status === 'FAILED').length;
    const processing = docs.filter(d => d.status === 'PROCESSING' || d.status === 'QUEUED').length;

    const docsWithDuration = docs.filter(d => typeof d.durationMs === 'number' && d.durationMs > 0);
    const totalDuration = docsWithDuration.reduce((acc, d) => acc + (d.durationMs || 0), 0);
    const avgDuration = docsWithDuration.length > 0 ? Math.round(totalDuration / docsWithDuration.length) : 0;
    const finishedCount = completed + failed;
    const successRate = finishedCount > 0 ? Math.round((completed / finishedCount) * 100) : 100;

    this.metrics = {
      totalDocs: total,
      completedDocs: completed,
      failedDocs: failed,
      processingDocs: processing,
      avgDurationMs: avgDuration,
      totalDurationMs: totalDuration,
      successRate
    };
  }

  viewMessage(messageId?: number): void {
    if (messageId) {
      this.router.navigate(['/messages', messageId]);
    }
  }

  stopPolling(): void {
    if (this.pollInterval) {
      clearInterval(this.pollInterval);
      this.pollInterval = null;
    }
  }

  ngOnDestroy(): void {
    this.stopPolling();
  }
}
