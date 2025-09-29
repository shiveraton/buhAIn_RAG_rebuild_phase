import { Component, OnInit, OnDestroy } from '@angular/core';
import { AuthService } from '../../../core/services/auth.service';
import { ScoreService } from '../../../core/services/score.service';
import { QuestUpdateService } from '../../../core/services/quest-update.service';
import { ToastController } from '@ionic/angular';
import { Subscription } from 'rxjs';

@Component({
  selector: 'app-quests',
  templateUrl: './quests.page.html',
  styleUrls: ['./quests.page.scss'],
  standalone: false,
})
export class QuestsPage implements OnInit, OnDestroy {
  currentUser: any = null;
  userProfile: any = null;
  isLoading = false;
  private authSubscription?: Subscription;
  private questUpdateSubscription?: Subscription;
  
  dailyQuests = [
    {
      id: 'daily_login',
      title: 'Log in today',
      description: 'Open the app and claim your daily bonus',
      points: 2,
      completed: false,
      progress: 0,
      target: 1,
      claimed: false
    },
    {
      id: 'transliterate_3',
      title: 'Transliterate 3 words using text feature',
      description: 'Use the text transliteration feature 3 times',
      points: 15,
      completed: false,
      progress: 0,
      target: 3,
      claimed: false
    }
  ];

  weeklyQuests = [
    {
      id: 'login_streak_7',
      title: 'Login streak of 7 days',
      description: 'Log in for 7 consecutive days',
      points: 50,
      completed: false,
      progress: 0,
      target: 7,
      claimed: false
    },
    {
      id: 'transliterate_20',
      title: 'Transliterate 20 words',
      description: 'Use the transliteration feature 20 times this week',
      points: 75,
      completed: false,
      progress: 0,
      target: 20,
      claimed: false
    },
    {
      id: 'earn_100_points',
      title: 'Earn 100 points',
      description: 'Accumulate 100 points this week',
      points: 40,
      completed: false,
      progress: 0,
      target: 100,
      claimed: false
    }
  ];

  constructor(
    private authService: AuthService,
    private scoreService: ScoreService,
    private toastController: ToastController,
    private questUpdateService: QuestUpdateService
  ) { }

  async ngOnInit() {
    // Subscribe to authentication state changes instead of getting current user immediately
    this.authSubscription = this.authService.currentUser$.subscribe(async (user) => {
      this.currentUser = user;
      if (user) {
        // Reset quest states for new user
        this.resetQuestStates();
        await this.loadUserProfile();
      } else {
        // Clear everything when user logs out
        this.userProfile = null;
        this.resetQuestStates();
        this.isLoading = false;
      }
    });

    // Subscribe to quest updates for real-time updates
    this.questUpdateSubscription = this.questUpdateService.questUpdate$.subscribe((questType) => {
      console.log('Received quest update:', questType);
      if (this.currentUser && this.userProfile) {
        this.loadUserProfile();
      }
    });
  }

  ngOnDestroy() {
    if (this.authSubscription) {
      this.authSubscription.unsubscribe();
    }
    if (this.questUpdateSubscription) {
      this.questUpdateSubscription.unsubscribe();
    }
  }

  ionViewWillEnter() {
    // Refresh quest progress every time user enters this page
    if (this.currentUser) {
      this.loadUserProfile();
    }
  }

  async loadUserProfile() {
    if (this.currentUser) {
      this.isLoading = true;
      const startTime = Date.now();
      
      try {
        this.userProfile = await this.authService.getUserProfile(this.currentUser.uid);
        await this.updateQuestProgress(); // Update quest progress after loading profile
        
        // Ensure minimum loading time of 3.5 seconds
        const elapsedTime = Date.now() - startTime;
        const remainingTime = Math.max(0, 3500 - elapsedTime);
        
        if (remainingTime > 0) {
          await new Promise(resolve => setTimeout(resolve, remainingTime));
        }
      } catch (error) {
        console.error('Error loading user profile:', error);
      } finally {
        this.isLoading = false;
      }
    }
  }

  async updateQuestProgress() {
    if (!this.userProfile) return;

    // Update daily quests
    const today = new Date().toISOString().split('T')[0];
    for (const quest of this.dailyQuests) {
      // Check if quest is already claimed
      quest.claimed = await this.authService.isQuestClaimed(this.currentUser.uid, quest.id, false);

      switch (quest.id) {
        case 'daily_login': {
          const loggedInToday = this.userProfile.lastLoginDate === today;
          quest.completed = loggedInToday;
          quest.progress = loggedInToday ? 1 : 0;
          break;
        }
        case 'transliterate_3': {
          // If lastTransliterationDate is not today, progress should be 0
          const didTransliterateToday = this.userProfile.lastTransliterationDate === today;
          const translitCount = didTransliterateToday ? (this.userProfile.dailyTransliterations || 0) : 0;
          quest.progress = Math.min(translitCount, quest.target);
          quest.completed = quest.progress >= quest.target;
          break;
        }
      }
    }

    // Update weekly quests
    for (const quest of this.weeklyQuests) {
      // Check if quest is already claimed
      quest.claimed = await this.authService.isQuestClaimed(this.currentUser.uid, quest.id, true);
      
      switch (quest.id) {
        case 'login_streak_7':
          quest.progress = Math.min(this.userProfile.loginStreak || 0, quest.target);
          quest.completed = quest.progress >= quest.target;
          break;
        case 'transliterate_20':
          quest.progress = Math.min(this.userProfile.weeklyTransliterations || 0, quest.target);
          quest.completed = quest.progress >= quest.target;
          break;
        case 'earn_100_points':
          quest.progress = Math.min(this.userProfile.weeklyPoints || 0, quest.target);
          quest.completed = quest.progress >= quest.target;
          break;
      }
    }
  }

  async claimQuest(quest: any, isWeekly: boolean = false) {
    if (!this.currentUser || !quest.completed || quest.claimed) {
      return;
    }

    try {
      // Check if quest can be claimed using AuthService
      const canClaim = await this.authService.claimQuest(this.currentUser.uid, quest.id, isWeekly);
      
      if (!canClaim) {
        const toast = await this.toastController.create({
          message: `Quest already claimed ${isWeekly ? 'this week' : 'today'}!`,
          duration: 3000,
          color: 'warning',
          position: 'top'
        });
        await toast.present();
        return;
      }

      // Special handling for daily login quest - use ScoreService method
      if (quest.id === 'daily_login') {
        const bonusAwarded = await this.scoreService.awardDailyBonus();
        if (bonusAwarded) {
          quest.claimed = true;
          // Refresh profile to update quest status
          await this.refreshUserProfile();
          
          const toast = await this.toastController.create({
            message: `🌅 Daily login bonus claimed! +${quest.points} points`,
            duration: 3000,
            color: 'success',
            position: 'top'
          });
          await toast.present();
        }
        return;
      }

      // For other quests, award points normally
      await this.scoreService.awardPoints(`Quest: ${quest.title}`, quest.points);
      
      const toast = await this.toastController.create({
        message: `🏆 Quest completed! +${quest.points} points`,
        duration: 3000,
        color: 'success',
        position: 'top'
      });
      await toast.present();

      // Mark quest as claimed and refresh profile
      quest.claimed = true;
      await this.refreshUserProfile();
      
    } catch (error) {
      console.error('Error claiming quest:', error);
      
      const toast = await this.toastController.create({
        message: 'Error claiming quest. Please try again.',
        duration: 3000,
        color: 'danger',
        position: 'top'
      });
      await toast.present();
    }
  }

  // Check if user needs to refresh their profile after claiming daily bonus
  async refreshUserProfile() {
    if (this.currentUser) {
      this.isLoading = true;
      const startTime = Date.now();
      
      try {
        this.userProfile = await this.authService.getUserProfile(this.currentUser.uid);
        await this.updateQuestProgress(); // Update quest progress after loading profile
        
        // Ensure minimum loading time of 3.5 seconds
        const elapsedTime = Date.now() - startTime;
        const remainingTime = Math.max(0, 3500 - elapsedTime);
        
        if (remainingTime > 0) {
          await new Promise(resolve => setTimeout(resolve, remainingTime));
        }
      } catch (error) {
        console.error('Error loading user profile:', error);
      } finally {
        this.isLoading = false;
      }
    }
  }

  getProgressPercentage(quest: any): number {
    return Math.min((quest.progress / quest.target) * 100, 100);
  }

  // Reset quest states to default when switching users
  private resetQuestStates() {
    // Reset daily quests
    this.dailyQuests.forEach(quest => {
      quest.completed = false;
      quest.progress = 0;
      quest.claimed = false;
    });

    // Reset weekly quests
    this.weeklyQuests.forEach(quest => {
      quest.completed = false;
      quest.progress = 0;
      quest.claimed = false;
    });
  }
}
