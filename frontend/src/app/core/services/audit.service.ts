import { Injectable } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';
import { AuditLogEntry } from '../models/message.model';

@Injectable({
  providedIn: 'root'
})
export class AuditService {
  private readonly apiUrl = 'http://localhost:8080/api';

  constructor(private http: HttpClient) {}

  getAuditLog(entityType?: string, entityId?: number): Observable<AuditLogEntry[]> {
    let params = new HttpParams();
    if (entityType) params = params.set('entityType', entityType);
    if (entityId) params = params.set('entityId', entityId.toString());

    return this.http.get<AuditLogEntry[]>(`${this.apiUrl}/audit`, { params });
  }
}
