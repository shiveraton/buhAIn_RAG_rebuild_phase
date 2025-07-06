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
  warnings: []
}
@Injectable({
  providedIn: 'root'
})
export class TransliterationService {
  private transliterationApiUrl: string = environment.django.apiUrl;

  constructor(private http: HttpClient) { }

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
  }
}
