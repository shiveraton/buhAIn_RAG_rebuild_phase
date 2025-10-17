import { Injectable } from '@angular/core';
import { environment } from 'src/environments/environment';
import { Observable } from 'rxjs';
import { HttpClient } from '@angular/common/http';
interface TransliterateResponse{
  input_text: string,
  transliteration_direction: string,
  normalized_text: string,
  length: number,
  transliterated_text: string,
<<<<<<< HEAD
  warnings: [],
  // Cross-language fields (optional)
  baybayin_text?: string,
  translated_text?: string,
  steps?: string[],
  error?: string
=======
  warnings: []
>>>>>>> main
}
@Injectable({
  providedIn: 'root'
})
export class TransliterationService {
  private transliterationApiUrl: string = environment.django.apiUrl;

  constructor(private http: HttpClient) { }

<<<<<<< HEAD
  /**
   * Call backend transliteration endpoint. Supports cross-language calls by
   * passing direction = 'cross_en_to_baybayin' and source_language = 'en'.
   */
  transliterateText(input: string, direction: string = 'to_baybayin', source_language?: string): Observable<TransliterateResponse>{
    const transliterateTextUrl= this.transliterationApiUrl + "/transliterate/text/";
    const body: any = {
      text: input,
      transliteration_direction: direction
    };
    if (source_language) {
      body['source_language'] = source_language;
    }
    return this.http.post<TransliterateResponse>(transliterateTextUrl, body);
=======
  transliterateText(input: string): Observable<TransliterateResponse>{
    const transliterateTextUrl= this.transliterationApiUrl + "/transliterate/text/"
    console.log(transliterateTextUrl)
    const body = {
      text: input,
      transliteration_direction: "to_baybayin"
    }
    const result = this.http.post<TransliterateResponse>(transliterateTextUrl, body);
    console.log(result)
    return result
>>>>>>> main
  }
}
