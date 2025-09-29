import { Injectable } from '@angular/core';
import { HttpClient, HttpHeaders } from '@angular/common/http';
import { Observable, BehaviorSubject } from 'rxjs';
import { tap } from 'rxjs/operators';
import { environment } from '../../../../environments/environment';

export interface TriviaQuestion {
  question: string;
  options: string[];
}

export interface GameState {
  level: number;
  current_xp: number;
  target_xp: number;
  moves_remaining: number;
  consecutive_correct: number;
  mastery_level: number;
  accuracy_rate: number;
  top_weaknesses: string[];
  level_completed?: boolean;
  level_failed?: boolean;
}

export interface TriviaResponse {
  trivia: TriviaQuestion;
  game_state: GameState;
  question_token?: string;  // Add optional token
}

export interface SubmitAnswerRequest {
  user_answer: string;
  question_token?: string;  // Add optional token
}

export interface SubmitAnswerResponse {
  result: 'correct' | 'incorrect';
  correct_answer: string;
  points: number;
  game_state: GameState;
}

@Injectable({
  providedIn: 'root'
})
export class TriviaService {
  private baseUrl = `${environment.django.apiUrl}/trivia`;
  private gameStateSubject = new BehaviorSubject<GameState | null>(null);
  public gameState$ = this.gameStateSubject.asObservable();
  
  private currentQuestionToken: string | null = null;  // Store token

  constructor(private http: HttpClient) {}

  private getHeaders(): HttpHeaders {
    const token = localStorage.getItem('auth_token');
    const headers: any = {
      'Content-Type': 'application/json'
    };
    
    // Only add Authorization header if token exists
    if (token) {
      headers['Authorization'] = `Token ${token}`;
    }
    
    return new HttpHeaders(headers);
  }

  /**
   * Get a new trivia question
   */
  getQuestion(): Observable<TriviaResponse> {
    return this.http.get<TriviaResponse>(`${this.baseUrl}/question/`, {
      headers: this.getHeaders(),
      withCredentials: true
    }).pipe(
      tap((response: TriviaResponse) => {
        // Store token for later use
        if (response.question_token) {
          this.currentQuestionToken = response.question_token;
        }
      })
    );
  }

  /**
   * Submit an answer to the current question
   */
  submitAnswer(answer: string): Observable<SubmitAnswerResponse> {
    const body: SubmitAnswerRequest = { 
      user_answer: answer,
      question_token: this.currentQuestionToken || undefined
    };
    return this.http.post<SubmitAnswerResponse>(`${this.baseUrl}/submit-answer/`, body, {
      headers: this.getHeaders(),
      withCredentials: true
    }).pipe(
      tap(() => {
        // Clear token after use
        this.currentQuestionToken = null;
      })
    );
  }

  /**
   * Get current game state without a new question
   */
  getGameState(): Observable<GameState> {
    return this.http.get<GameState>(`${this.baseUrl}/game-state/`, {
      headers: this.getHeaders(),
      withCredentials: true
    });
  }

  /**
   * Reset current level progress
   */
  resetLevel(): Observable<{message: string, game_state: GameState}> {
    return this.http.post<{message: string, game_state: GameState}>(`${this.baseUrl}/reset-level/`, {}, {
      headers: this.getHeaders(),
      withCredentials: true
    });
  }

  /**
   * Update the local game state and notify subscribers
   */
  updateGameState(gameState: GameState): void {
    this.gameStateSubject.next(gameState);
  }

  /**
   * Clear the current game state
   */
  clearGameState(): void {
    this.gameStateSubject.next(null);
  }
}
