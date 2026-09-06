import { Component, OnInit, ViewChild, AfterViewInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Router, RouterModule } from '@angular/router';
import { MatTableModule, MatTableDataSource } from '@angular/material/table';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatSelectModule } from '@angular/material/select';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatChipsModule } from '@angular/material/chips';
import { MatCardModule } from '@angular/material/card';
import { MatProgressBarModule } from '@angular/material/progress-bar';
import { MatSnackBar, MatSnackBarModule } from '@angular/material/snack-bar';
import { MatPaginator, MatPaginatorModule } from '@angular/material/paginator';
import { MatSort, MatSortModule } from '@angular/material/sort';
import { MatTooltipModule } from '@angular/material/tooltip';

import { MessageService } from '../../core/services/message.service';
import { MessageListItem } from '../../core/models/message.model';

@Component({
  selector: 'app-queue',
  standalone: true,
  imports: [
    CommonModule,
    FormsModule,
    RouterModule,
    MatTableModule,
    MatButtonModule,
    MatIconModule,
    MatSelectModule,
    MatFormFieldModule,
    MatInputModule,
    MatChipsModule,
    MatCardModule,
    MatProgressBarModule,
    MatSnackBarModule,
    MatPaginatorModule,
    MatSortModule,
    MatTooltipModule
  ],
  templateUrl: './queue.component.html',
  styleUrls: ['./queue.component.scss']
})
export class QueueComponent implements OnInit, AfterViewInit {
  messages: MessageListItem[] = [];
  dataSource = new MatTableDataSource<MessageListItem>([]);
  displayedColumns: string[] = ['urgency', 'id', 'status', 'sla', 'categories', 'sender', 'subject', 'attachments', 'receivedDate'];
  loading = false;
  ingesting = false;

  selectedStatus = '';
  selectedCategory = '';
  selectedSourceType = 'EMAIL';
  searchQuery = '';
  activeUrgencyFilter: string | null = null;
  showResetConfirm = false;
  resetting = false;

  @ViewChild(MatPaginator) paginator!: MatPaginator;
  @ViewChild(MatSort) sort!: MatSort;

  constructor(
    private messageService: MessageService,
    private router: Router,
    private snackBar: MatSnackBar
  ) {}

  ngOnInit(): void {
    this.loadMessages();
  }

  ngAfterViewInit(): void {
    this.dataSource.paginator = this.paginator;
    this.dataSource.sort = this.sort;
    this.setupFilterPredicate();
  }

  setupFilterPredicate(): void {
    this.dataSource.filterPredicate = (item: MessageListItem, filter: string): boolean => {
      const q = filter.trim().toLowerCase();
      const matchesSearch = !q ||
        Boolean(item.sender && item.sender.toLowerCase().includes(q)) ||
        Boolean(item.subject && item.subject.toLowerCase().includes(q)) ||
        Boolean(item.topSummary && item.topSummary.toLowerCase().includes(q)) ||
        Boolean(item.productSnippet && item.productSnippet.toLowerCase().includes(q));

      const matchesUrgency = !this.activeUrgencyFilter || item.urgencyLevel === this.activeUrgencyFilter;

      return Boolean(matchesSearch && matchesUrgency);
    };
  }

  loadMessages(): void {
    this.loading = true;
    this.messageService.getMessages({
      status: this.selectedStatus,
      category: this.selectedCategory,
      sourceType: this.selectedSourceType || undefined
    }).subscribe({
      next: (res) => {
        this.messages = res.items.map(m => this.enrichMessageWithClinicalContext(m));
        this.applyFilters();
        this.loading = false;
      },
      error: (err) => {
        this.loading = false;
        this.snackBar.open('Error loading messages from backend', 'Close', { duration: 4000 });
      }
    });
  }

  enrichMessageWithClinicalContext(m: MessageListItem): MessageListItem {
    const isSafety = m.classifications?.some(c => c.category === 'SAFETY_REPORT');
    const isQC = m.classifications?.some(c => c.category === 'QUALITY_COMPLAINT');
    const isInfo = m.classifications?.some(c => c.category === 'INFO_REQUEST');

    const textToScan = `${m.subject || ''} ${m.topSummary || ''}`.toLowerCase();

    // Determine Urgency
    if (isSafety) {
      if (textToScan.includes('hospital') || textToScan.includes('fatal') || textToScan.includes('anaphyl') || textToScan.includes('death') || textToScan.includes('severe') || textToScan.includes('emergency')) {
        m.urgencyLevel = 'CRITICAL';
      } else {
        m.urgencyLevel = 'WARNING';
      }
    } else if (isQC) {
      m.urgencyLevel = 'WARNING';
    } else if (isInfo) {
      m.urgencyLevel = 'INFO';
    } else {
      m.urgencyLevel = 'ROUTINE';
    }

    // Calculate Regulatory SLA (15 days for Safety, 30 days for QC)
    if (isSafety || isQC) {
      const windowDays = isSafety ? (m.urgencyLevel === 'CRITICAL' ? 7 : 15) : 30;
      const recDate = m.receivedDate ? new Date(m.receivedDate).getTime() : Date.now();
      const elapsedMs = Date.now() - recDate;
      const totalWindowMs = windowDays * 24 * 60 * 60 * 1000;
      const remainingMs = totalWindowMs - elapsedMs;

      if (remainingMs <= 0) {
        m.slaRemainingText = 'EXPIRED';
        m.slaExpired = true;
      } else {
        const remDays = Math.floor(remainingMs / (24 * 60 * 60 * 1000));
        const remHours = Math.floor((remainingMs % (24 * 60 * 60 * 1000)) / (60 * 60 * 1000));
        m.slaRemainingText = `${remDays}d ${remHours}h`;
        m.slaExpired = false;
      }
    }

    // Extract Product mention snippet if present
    const products = ['Nortavex', 'Calmerol', 'Zolapamine', 'Verolan', 'CardioFlow'];
    for (const prod of products) {
      if (textToScan.includes(prod.toLowerCase())) {
        m.productSnippet = prod;
        break;
      }
    }

    return m;
  }

  applyFilters(): void {
    this.dataSource.data = this.messages;
    if (this.searchQuery || this.activeUrgencyFilter) {
      this.dataSource.filter = this.searchQuery || ' ';
    } else {
      this.dataSource.filter = '';
    }
    if (this.dataSource.paginator) {
      this.dataSource.paginator.firstPage();
    }
  }

  filterByUrgency(urgency: string | null): void {
    this.activeUrgencyFilter = this.activeUrgencyFilter === urgency ? null : urgency;
    this.applyFilters();
  }

  filterByPendingStatus(): void {
    this.selectedStatus = this.selectedStatus === 'PENDING_REVIEW' ? '' : 'PENDING_REVIEW';
    this.loadMessages();
  }

  filterByQC(): void {
    this.selectedCategory = this.selectedCategory === 'QUALITY_COMPLAINT' ? '' : 'QUALITY_COMPLAINT';
    this.loadMessages();
  }

  get totalCount(): number {
    return this.messages.length;
  }

  get urgentSaeCount(): number {
    return this.messages.filter(m => m.urgencyLevel === 'CRITICAL').length;
  }

  get qcCount(): number {
    return this.messages.filter(m => m.classifications?.some(c => c.category === 'QUALITY_COMPLAINT')).length;
  }

  get pendingCount(): number {
    return this.messages.filter(m => m.status === 'PENDING_REVIEW').length;
  }

  triggerIngest(): void {
    this.ingesting = true;
    this.messageService.triggerIngest().subscribe({
      next: (res) => {
        this.ingesting = false;
        this.snackBar.open(`Ingestion triggered: ${res.messagesIngested} messages queued.`, 'OK', { duration: 4000 });
        this.loadMessages();
      },
      error: (err) => {
        this.ingesting = false;
        this.snackBar.open('Ingestion error: ' + (err.error?.message || err.message), 'Close', { duration: 5000 });
      }
    });
  }

  openDetail(message: MessageListItem): void {
    this.router.navigate(['/messages', message.id]);
  }

  exportToCsv(): void {
    if (this.messages.length === 0) return;
    const headers = ['ID', 'Status', 'Urgency', 'SLA Remaining', 'Categories', 'Sender', 'Subject', 'Received Date'];
    const rows = this.messages.map(m => [
      m.id,
      m.status,
      m.urgencyLevel || 'ROUTINE',
      m.slaRemainingText || 'N/A',
      m.classifications?.map(c => c.category).join(';') || '',
      `"${(m.sender || '').replace(/"/g, '""')}"`,
      `"${(m.subject || '').replace(/"/g, '""')}"`,
      m.receivedDate || ''
    ]);

    const csvContent = 'data:text/csv;charset=utf-8,' + [headers.join(','), ...rows.map(e => e.join(','))].join('\n');
    const encodedUri = encodeURI(csvContent);
    const link = document.createElement('a');
    link.setAttribute('href', encodedUri);
    link.setAttribute('download', `PV_Triage_Queue_${new Date().toISOString().slice(0,10)}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    this.snackBar.open('Queue exported to CSV', 'OK', { duration: 3000 });
  }


  getConfidenceClass(confidence: number): string {
    if (confidence >= 0.8) return 'high';
    if (confidence >= 0.5) return 'medium';
    return 'low';
  }

  getSenderName(sender: string): string {
    if (!sender) return 'Unknown';
    let name = sender;
    if (sender.includes('<')) {
      name = sender.split('<')[0].trim();
    }
    name = name.replace(/^["']|["']$/g, '').trim();
    return name || sender;
  }

  getSenderEmail(sender: string): string {
    if (!sender) return '';
    const match = sender.match(/<([^>]+)>/);
    return match ? match[1] : '';
  }

  openResetConfirm(): void {
    this.showResetConfirm = true;
  }

  cancelReset(): void {
    this.showResetConfirm = false;
  }

  confirmReset(): void {
    this.resetting = true;
    this.messageService.resetDemoData().subscribe({
      next: () => {
        this.resetting = false;
        this.showResetConfirm = false;
        this.messages = [];
        this.dataSource.data = [];
        this.snackBar.open('Demo data reset! Queue is now clean (0 messages).', 'OK', { duration: 4000 });
        this.loadMessages();
      },
      error: (err) => {
        this.resetting = false;
        this.snackBar.open('Failed to reset data: ' + (err.error?.message || err.message), 'Close', { duration: 5000 });
      }
    });
  }
}

