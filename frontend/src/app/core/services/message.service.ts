import { Injectable } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';
import { MessageDetail, MessageListItem } from '../models/message.model';

@Injectable({
  providedIn: 'root'
})
export class MessageService {
  private readonly apiUrl = 'http://localhost:8080/api';

  constructor(private http: HttpClient) {}

  getMessages(filters?: { status?: string; category?: string; sourceType?: string }): Observable<{ items: MessageListItem[]; total: number }> {
    let params = new HttpParams();
    if (filters?.status) params = params.set('status', filters.status);
    if (filters?.category) params = params.set('category', filters.category);
    if (filters?.sourceType) params = params.set('sourceType', filters.sourceType);

    return this.http.get<{ items: MessageListItem[]; total: number }>(`${this.apiUrl}/messages`, { params });
  }

  getMessage(id: number): Observable<MessageDetail> {
    return this.http.get<MessageDetail>(`${this.apiUrl}/messages/${id}`);
  }

  triggerIngest(): Observable<{ status: string; messagesIngested: number; message: string }> {
    return this.http.post<{ status: string; messagesIngested: number; message: string }>(`${this.apiUrl}/mail/ingest`, {});
  }

  getAttachmentFileUrl(attachmentId: number): string {
    return `${this.apiUrl}/attachments/${attachmentId}/file`;
  }

  resetDemoData(): Observable<{ status: string; message: string }> {
    return this.http.post<{ status: string; message: string }>(`${this.apiUrl}/messages/reset`, {});
  }
}
