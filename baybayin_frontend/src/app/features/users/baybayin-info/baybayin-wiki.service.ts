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

export interface SemanticSearchResult {
  article_id: number;
  title: string;
  content: string;
  similarity: number;
  tags: string[];
  summary?: string;
}

export interface RelatedArticle {
  id: number;
  title: string;
  summary: string;
  similarity: number;
  tags: string[];
}

@Injectable({ providedIn: 'root' })
export class BaybayinWikiService {
  private apiUrl = 'http://localhost:8000/api/wiki/articles/?search=Baybayin';
  private baseUrl = 'http://localhost:8000/api/codex';

  constructor(private http: HttpClient) {}

  getBaybayinArticles(): Observable<WikiArticle[]> {
    return this.http.get<{ results?: WikiArticle[] } | WikiArticle[]>(this.apiUrl).pipe(
      map((res: { results?: WikiArticle[] } | WikiArticle[]) => Array.isArray(res) ? res : res.results || [])
    );
  }

  /**
   * Perform semantic search across Codex articles
   * @param query Natural language search query
   * @param topK Number of results to return (default 5)
   */
  semanticSearch(query: string, topK: number = 5): Observable<SemanticSearchResult[]> {
    return this.http.post<SemanticSearchResult[]>(`${this.baseUrl}/articles/semantic_search/`, {
      query,
      top_k: topK
    });
  }

  /**
   * Get related articles based on an article ID
   * @param articleId ID of the reference article
   * @param topK Number of related articles to return (default 3)
   */
  getRelatedArticles(articleId: number, topK: number = 3): Observable<RelatedArticle[]> {
    return this.http.get<RelatedArticle[]>(
      `${this.baseUrl}/articles/${articleId}/related_articles/?top_k=${topK}`
    );
  }

  /**
   * Get all available article tags for filtering
   */
  getArticleTags(): Observable<string[]> {
    return this.http.get<WikiArticle[]>(`${this.baseUrl}/articles/`).pipe(
      map(articles => {
        const allTags = new Set<string>();
        articles.forEach(article => {
          if (article.tags && Array.isArray(article.tags)) {
            article.tags.forEach(tag => allTags.add(tag));
          }
        });
        return Array.from(allTags).sort();
      })
    );
  }

  /**
   * Filter articles by tag
   */
  getArticlesByTag(tag: string): Observable<WikiArticle[]> {
    return this.http.get<WikiArticle[]>(`${this.baseUrl}/articles/?tags=${tag}`);
  }
}
