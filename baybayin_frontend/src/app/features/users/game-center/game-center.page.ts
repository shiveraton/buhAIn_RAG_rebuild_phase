import { Component, OnInit, OnDestroy } from '@angular/core';
import { IonicModule } from '@ionic/angular';
import { CommonModule } from '@angular/common';
import { Subscription } from 'rxjs';
import { TriviaService, TriviaQuestion, GameState, SubmitAnswerResponse } from '../../../core/services/trivia.service';
import { AuthenticationService } from 'src/app/core/services/authentication.service';

@Component({
  selector: 'app-game-center',
  templateUrl: './game-center.page.html',
  styleUrls: ['./game-center.page.scss'],
  standalone: true,
  imports: [IonicModule, CommonModule]
})
export class GameCenterPage implements OnInit, OnDestroy {
  // Game state management
  currentScreen: 'menu' | 'game' | 'results' | 'level-completed' | 'level-failed' = 'menu';
  currentQuestion: TriviaQuestion | null = null;
  gameState: GameState | null = null;
  
  // Trivia game state
  score = 0;
  questionNumber = 1;
  totalQuestions = 999; // Remove arbitrary limit - let backend determine completion
  selectedAnswer = '';
  showResult = false;
  lastResult: 'correct' | 'incorrect' | null = null;
  correctAnswer = '';
  earnedPoints = 0;
  
  // Loading states
  loadingQuestion = false;
  submittingAnswer = false;
  
  private subscriptions = new Subscription();

  constructor(private triviaService: TriviaService,) {}

  ngOnInit() {
    // Always load game state for both guest and authenticated users
    this.loadGameState();

    // Subscribe to game state changes
    this.subscriptions.add(
      this.triviaService.gameState$.subscribe(gameState => {
        this.gameState = gameState;
      })
    );
  }

  ngOnDestroy() {
    this.subscriptions.unsubscribe();
  }

  loadGameState() {
    this.triviaService.getGameState().subscribe({
      next: (gameState) => {
        this.triviaService.updateGameState(gameState);
      },
      error: (error) => {
        console.error('Error loading game state:', error);
      }
    });
  }

  startTrivia() {
    this.currentScreen = 'game';
    this.questionNumber = 1;
    this.score = 0; // Reset session score, not XP
    this.loadNewQuestion();
  }

  loadNewQuestion() {
    this.loadingQuestion = true;
    this.selectedAnswer = '';
    this.showResult = false;
    this.lastResult = null;

    this.triviaService.getQuestion().subscribe({
      next: (response) => {
        this.currentQuestion = response.trivia;
        this.triviaService.updateGameState(response.game_state);
        this.loadingQuestion = false;
      },
      error: (error) => {
        console.error('Error loading question:', error);
        this.loadingQuestion = false;
      }
    });
  }

  selectAnswer(answer: string) {
    if (this.submittingAnswer || this.showResult) return;
    this.selectedAnswer = answer;
  }

  submitAnswer() {
    if (!this.selectedAnswer || this.submittingAnswer) return;

    this.submittingAnswer = true;
    this.triviaService.submitAnswer(this.selectedAnswer).subscribe({
      next: (response: SubmitAnswerResponse) => {
        this.handleAnswerResult(response);
        this.submittingAnswer = false;
      },
      error: (error) => {
        console.error('Error submitting answer:', error);
        this.submittingAnswer = false;
      }
    });
  }

  private handleAnswerResult(response: SubmitAnswerResponse) {
    this.lastResult = response.result;
    this.correctAnswer = response.correct_answer;
    this.earnedPoints = response.points;
    this.showResult = true;
    
    // Track session score (separate from persistent XP)
    this.score += response.points;
    
    // Update game state with new XP and moves from backend
    this.triviaService.updateGameState(response.game_state);
    
    // Check for level completion or failure - backend determines this
    if (response.game_state.level_completed) {
      // Level completed - show advancement message after delay
      setTimeout(() => this.showLevelCompleted(), 2000);
    } else if (response.game_state.level_failed) {
      // Level failed - show failure message after delay
      setTimeout(() => this.showLevelFailed(), 2000);
    } else {
      // Continue to next question after a delay
      setTimeout(() => {
        this.questionNumber++;
        this.loadNewQuestion();
      }, 2000);
    }
  }

  nextQuestion() {
    // This method is no longer used - level progression is handled by backend
    this.loadNewQuestion();
  }

  showResults() {
    this.currentScreen = 'results';
  }

  showLevelCompleted() {
    // Show level advancement celebration
    this.currentScreen = 'level-completed';
  }

  showLevelFailed() {
    // Show level failure/retry screen
    this.currentScreen = 'level-failed';
  }

  playAgain() {
    this.startTrivia();
  }

  goToMainMenu() {
    this.currentScreen = 'menu';
    this.currentQuestion = null;
  }

  resetLevel() {
    this.triviaService.resetLevel().subscribe({
      next: (response) => {
        this.triviaService.updateGameState(response.game_state);
        // Reset session tracking
        this.score = 0;
        this.questionNumber = 1;
        this.goToMainMenu();
      },
      error: (error) => {
        console.error('Error resetting level:', error);
      }
    });
  }
    // XP progress bar (0–100%)
  get xpPercent(): number {
    if (!this.gameState) return 0;
    const xp = this.gameState.current_xp ?? 0;
    const goal = this.gameState.xp_to_next_level ?? 1;
    return Math.min(100, Math.max(0, (xp / goal) * 100));
  }

  // Button classes for answer highlighting
  getAnswerButtonClasses(option: string): string {
    if (!this.showResult && this.selectedAnswer !== option) {
      return '';
    }

    if (this.showResult) {
      if (option === this.correctAnswer) return 'bg-green-500 text-white';
      if (option === this.selectedAnswer && option !== this.correctAnswer)
        return 'bg-red-500 text-white';
      return '';
    }

    return this.selectedAnswer === option
      ? 'bg-blue-200'
      : '';
  }
}
