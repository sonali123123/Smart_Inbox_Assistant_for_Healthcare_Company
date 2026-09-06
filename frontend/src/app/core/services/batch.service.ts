import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { BatchStatusResponse } from '../models/message.model';

@Injectable({
  providedIn: 'root'
})
export class BatchService {
  private readonly apiUrl = 'http://localhost:8080/api';

  constructor(private http: HttpClient) {}

  runBatch(sourceDir?: string): Observable<{ batchId: string }> {
    return this.http.post<{ batchId: string }>(`${this.apiUrl}/batch/run`, { sourceDir });
  }

  getBatchStatus(batchId: string): Observable<BatchStatusResponse> {
    return this.http.get<BatchStatusResponse>(`${this.apiUrl}/batch/${batchId}/status`);
  }
}
