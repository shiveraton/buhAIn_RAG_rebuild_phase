import { Injectable } from '@angular/core';
import { environment } from 'src/environments/environment';
import { Observable, from, EMPTY, throwError } from 'rxjs';
import { HttpClient } from '@angular/common/http';
import { concatMap, catchError, first, timeout } from 'rxjs/operators';

interface TransliterateResponse {
  input_text: string,
  transliteration_direction: string,
  normalized_text: string,
  length: number,
  transliterated_text: string,
  warnings: [],
  // Cross-language specific fields (optional)
  baybayin_text?: string,
  translated_text?: string,
  steps?: string[],
  error?: string
}

@Injectable({
  providedIn: 'root'
})
export class TransliterationService {
  private transliterationApiUrl: string = environment.django.apiUrl;

  constructor(private http: HttpClient) { }

  transliterateText(input: string, direction: string = 'to_baybayin', source_language?: string): Observable<TransliterateResponse> {
    const body: any = {
      text: input,
      transliteration_direction: direction
    };
    if (source_language) {
      body['source_language'] = source_language;
    }

    const candidates: string[] = [
      this.transliterationApiUrl,              // configured host (may be remote)
      'http://127.0.0.1:8000/api',             // local fallback
      'http://localhost:8000/api'             // alternate local fallback
    ].filter(Boolean).map(u => u.replace(/\/$/, ''));

    const timeoutMs = 4000; // per-attempt timeout (milliseconds)

    const attempt$ = from(candidates).pipe(
      concatMap(base => {
        const url = `${base}/transliterate/text/`;
        console.log('[TransliterationService] Attempting', url, body);
        return this.http.post<TransliterateResponse>(url, body).pipe(
          timeout(timeoutMs),
          catchError(err => {
            console.warn('[TransliterationService] attempt failed for', url, err && err.message ? err.message : err);
            return EMPTY;
          })
        );
      }),
      first(),
      catchError(() => throwError(() => new Error('All transliteration endpoints failed')))
    );

    return attempt$;
  }

  transliterateImage(inputImage: File,direction: string = "to_baybayin", role="user"): Observable<TransliterateResponse> {
    const formData = new FormData();
    formData.append('inputImage', inputImage);
    formData.append('direction', direction);
    formData.append('role', role);

    const url = `${this.transliterationApiUrl}/transliterate/image/`; // make sure endpoint matches Django API
    console.log(url)
    return this.http.post<TransliterateResponse>(url, formData).pipe(
      timeout(8000), 
      catchError(err => {
        console.error('[TransliterationService] Image transliteration failed:', err);
        return throwError(() => new Error('Image transliteration failed.'));
      })
    );
  }
}
