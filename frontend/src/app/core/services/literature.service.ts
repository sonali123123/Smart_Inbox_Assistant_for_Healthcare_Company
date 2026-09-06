import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { MessageListItem } from '../models/message.model';

@Injectable({
  providedIn: 'root'
})
export class LiteratureService {
  private readonly apiUrl = 'http://localhost:8080/api';

  constructor(private http: HttpClient) {}

  uploadBatch(files: File[]): Observable<{ batchId: string }> {
    const formData = new FormData();
    files.forEach(f => formData.append('files', f));
    return this.http.post<{ batchId: string }>(`${this.apiUrl}/literature/batch`, formData);
  }

  getBatchCases(batchId: string): Observable<{ batchId: string; totalCases: number; cases: MessageListItem[] }> {
    return this.http.get<{ batchId: string; totalCases: number; cases: MessageListItem[] }>(
      `${this.apiUrl}/literature/batch/${batchId}`
    );
  }
}
