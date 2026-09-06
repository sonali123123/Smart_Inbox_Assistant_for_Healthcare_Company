import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { Classification, ExtractedField } from '../models/message.model';

@Injectable({
  providedIn: 'root'
})
export class ReviewService {
  private readonly apiUrl = 'http://localhost:8080/api';

  constructor(private http: HttpClient) {}

  reviewClassification(
    messageId: number,
    classificationId: number,
    action: 'ACCEPT' | 'OVERRIDE',
    newCategory?: string,
    reviewerName: string = 'Reviewer'
  ): Observable<Classification> {
    const payload = { action, newCategory, reviewerName };
    return this.http.put<Classification>(
      `${this.apiUrl}/messages/${messageId}/classifications/${classificationId}/review`,
      payload
    );
  }

  editField(
    messageId: number,
    fieldId: number,
    newValue: string,
    reviewerName: string = 'Reviewer',
    reason?: string
  ): Observable<ExtractedField> {
    const payload = { action: 'EDIT', newValue, reviewerName, reason };
    return this.http.put<ExtractedField>(
      `${this.apiUrl}/messages/${messageId}/fields/${fieldId}`,
      payload
    );
  }
}
