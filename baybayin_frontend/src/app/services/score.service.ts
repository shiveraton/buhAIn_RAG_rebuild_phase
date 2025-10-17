import { Injectable } from '@angular/core';
import { AuthService } from './auth.service';
import { ToastController } from '@ionic/angular';

@Injectable({
  providedIn: 'root'
})
export class ScoreService {
  private dailyBonusClaimedToday = false; // Prevent multiple claims in same session

  constructor(
    private authService: AuthService,
    private toastController: ToastController
  ) { }

  // Award points for different activities
  async awardPoints(activity: string, points: number) {
    const currentUser = this.authService.getCurrentUser();
    
    if (!currentUser) {
      // For guest users, you might want to store scores locally
      this.showGuestMessage();
      return false;
    }

    try {
      await this.authService.updateUserScore(currentUser.uid, points);
      this.showScoreToast(activity, points);
      return true;
    } catch (error) {
      console.error('Error awarding points:', error);
      return false;
    }
  }

  // Predefined scoring activities
  async awardTransliterationPoints(accuracy: number) {
    // Award points based on accuracy (0-100)
    const basePoints = 10;
    const bonusPoints = Math.floor(accuracy / 10); // 1 bonus point per 10% accuracy
    const totalPoints = basePoints + bonusPoints;
    
    return await this.awardPoints('Transliteration', totalPoints);
  }

  async awardQuizPoints(correctAnswers: number, totalQuestions: number) {
    const accuracy = (correctAnswers / totalQuestions) * 100;
    const basePoints = correctAnswers * 5;
    const perfectBonus = accuracy === 100 ? 20 : 0;
    const totalPoints = basePoints + perfectBonus;
    
    return await this.awardPoints('Quiz', totalPoints);
  }

  async awardLearningPoints() {
    // Award points for completing learning modules
    return await this.awardPoints('Learning', 5);
  }

  async awardDailyBonus() {
    const currentUser = this.authService.getCurrentUser();
    
    if (!currentUser) {
      this.showGuestMessage();
      return false;
    }

    // Prevent multiple claims in same session
    if (this.dailyBonusClaimedToday) {
      const toast = await this.toastController.create({
        message: '✅ Daily bonus already claimed today!',
        duration: 2000,
        color: 'medium',
        position: 'top'
      });
      await toast.present();
      return false;
    }

    try {
      const bonusAwarded = await this.authService.checkDailyLoginBonus(currentUser.uid);
      
      if (bonusAwarded) {
        this.dailyBonusClaimedToday = true; // Set flag to prevent multiple claims
        const toast = await this.toastController.create({
          message: '🌟 Daily Login Bonus: +2 points!',
          duration: 3000,
          color: 'success',
          position: 'top',
          cssClass: 'daily-bonus-toast'
        });
        await toast.present();
        return true;
      } else {
        // Already claimed today (from database)
        this.dailyBonusClaimedToday = true; // Set flag since it was already claimed
        const toast = await this.toastController.create({
          message: '✅ Daily bonus already claimed today!',
          duration: 2000,
          color: 'medium',
          position: 'top'
        });
        await toast.present();
        return false;
      }
    } catch (error) {
      console.error('Error awarding daily bonus:', error);
      return false;
    }
  }

  private async showScoreToast(activity: string, points: number) {
    const toast = await this.toastController.create({
      message: `🎉 +${points} points for ${activity}!`,
      duration: 3000,
      color: 'success',
      position: 'top',
      cssClass: 'score-toast'
    });
    await toast.present();
  }

  private async showGuestMessage() {
    const toast = await this.toastController.create({
      message: 'Sign in to save your scores and compete on the leaderboard!',
      duration: 4000,
      color: 'warning',
      position: 'top',
      buttons: [
        {
          text: 'Sign In',
          handler: () => {
            // Navigate to profile/login
            window.location.href = '/tabs/profile';
          }
        }
      ]
    });
    await toast.present();
  }

  // Reset daily bonus flag (for new day or testing)
  resetDailyBonusFlag() {
    this.dailyBonusClaimedToday = false;
  }

  // Calculate accuracy for transliteration
  calculateTransliterationAccuracy(expected: string, actual: string): number {
    if (!expected || !actual) return 0;
    
    const expectedWords = expected.toLowerCase().trim().split(/\s+/);
    const actualWords = actual.toLowerCase().trim().split(/\s+/);
    
    let correctWords = 0;
    const maxLength = Math.max(expectedWords.length, actualWords.length);
    
    for (let i = 0; i < maxLength; i++) {
      if (expectedWords[i] && actualWords[i] && expectedWords[i] === actualWords[i]) {
        correctWords++;
      }
    }
    
    return maxLength > 0 ? (correctWords / maxLength) * 100 : 0;
  }
}
