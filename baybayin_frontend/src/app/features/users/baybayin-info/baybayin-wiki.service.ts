import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { map } from 'rxjs/operators';

export interface WikiArticle {
  id: number;
  title: string;
  slug: string;
  category_name?: string;
  category_color?: string;
  summary: string;
  content?: string; // Only available in detail view
  featured_image?: string;
  tags: string[];
  reading_time?: number;
  difficulty_level?: string;
  is_featured?: boolean;
  created_at?: string;
  updated_at?: string;
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
  private baseUrl = 'http://localhost:8000/api/codex';
  private apiUrl = 'http://localhost:8000/api/codex/articles/';

  constructor(private http: HttpClient) {}

  getBaybayinArticles(): Observable<WikiArticle[]> {
    return this.http.get<WikiArticle[]>(this.apiUrl).pipe(
      map((res: any) => {
        // Handle both array response and object with results
        if (Array.isArray(res)) {
          return res;
        } else if (res.results && Array.isArray(res.results)) {
          return res.results;
        } else if (res.value && Array.isArray(res.value)) {
          return res.value;
        }
        return [];
      })
    );
  }

  /**
   * Perform semantic search across Codex articles
   * @param query Natural language search query
   * @param topK Number of results to return (default 5)
   */
  semanticSearch(query: string, topK: number = 5): Observable<SemanticSearchResult[]> {
    return this.http.post<any>(`${this.baseUrl}/articles/semantic_search/`, {
      query,
      top_k: topK
    }).pipe(
      map((response: any) => {
        // API returns {success, query, results: {articles: [], facts: [], combined: []}}
        if (response.success && response.results) {
          // Use combined results which includes both articles and facts
          const combined = response.results.combined || response.results.articles || [];
          
          // Transform to SemanticSearchResult format
          return combined.map((item: any) => ({
            article_id: item.id,
            title: item.title,
            content: item.content_preview || item.summary || '',
            similarity: item.similarity_score,
            tags: item.tags || [],
            summary: item.summary
          }));
        }
        return [];
      })
    );
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
