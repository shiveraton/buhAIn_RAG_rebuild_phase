import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { map } from 'rxjs/operators';

export interface WikiArticle {
  id: number;
  title: string;
  summary: string;
  content: string;
  tags: string[];
  // Add other fields as needed
}

@Injectable({ providedIn: 'root' })
export class BaybayinWikiService {
  private apiUrl = 'http://localhost:8000/api/wiki/articles/?search=Baybayin';

  constructor(private http: HttpClient) {}

  getBaybayinArticles(): Observable<WikiArticle[]> {
    return this.http.get<{ results?: WikiArticle[] } | WikiArticle[]>(this.apiUrl).pipe(
      map((res: { results?: WikiArticle[] } | WikiArticle[]) => Array.isArray(res) ? res : res.results || [])
    );
  }
}
