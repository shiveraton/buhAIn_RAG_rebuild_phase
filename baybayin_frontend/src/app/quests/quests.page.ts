import { Component, OnInit, OnDestroy } from '@angular/core';
import { AuthService } from '../services/auth.service';
import { ScoreService } from '../services/score.service';
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
  private authSubscription?: Subscription;
  
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
      title: 'Transliterate 3 words',
      description: 'Use the transliteration feature 3 times',
      points: 15,
      completed: false,
      progress: 0,
      target: 3,
      claimed: false
    },
    {
      id: 'earn_20_points',
      title: 'Earn 20 points',
      description: 'Accumulate 20 points through various activities',
      points: 10,
      completed: false,
      progress: 0,
      target: 20,
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
    private toastController: ToastController
  ) { }

  async ngOnInit() {
    // Subscribe to authentication state changes instead of getting current user immediately
    this.authSubscription = this.authService.currentUser$.subscribe(async (user) => {
      this.currentUser = user;
      if (user) {
        await this.loadUserProfile();
        this.updateQuestProgress();
      } else {
        this.userProfile = null;
      }
    });
  }

  ngOnDestroy() {
    if (this.authSubscription) {
      this.authSubscription.unsubscribe();
    }
  }

  ionViewWillEnter() {
    // Refresh quest progress every time user enters this page
    if (this.currentUser && this.userProfile) {
      this.refreshUserProfile();
    }
  }

  async loadUserProfile() {
    if (this.currentUser) {
      try {
        this.userProfile = await this.authService.getUserProfile(this.currentUser.uid);
      } catch (error) {
        console.error('Error loading user profile:', error);
      }
    }
  }

  updateQuestProgress() {
    if (!this.userProfile) return;

    // Update daily quests
    this.dailyQuests.forEach(quest => {
      switch (quest.id) {
        case 'daily_login':
          const today = new Date().toISOString().split('T')[0]; // Use same format as AuthService
          quest.completed = this.userProfile.lastLoginDate === today;
          quest.progress = quest.completed ? 1 : 0;
          break;
        case 'transliterate_3':
          // This would need to be tracked in user profile
          quest.progress = Math.min(this.userProfile.dailyTransliterations || 0, quest.target);
          quest.completed = quest.progress >= quest.target;
          break;
        case 'earn_20_points':
          // This would need daily points tracking
          quest.progress = Math.min(this.userProfile.dailyPoints || 0, quest.target);
          quest.completed = quest.progress >= quest.target;
          break;
      }
    });

    // Update weekly quests
    this.weeklyQuests.forEach(quest => {
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
    });
  }

  async claimQuest(quest: any, isWeekly: boolean = false) {
    if (!this.currentUser || !quest.completed) {
      return;
    }

    try {
      await this.scoreService.awardPoints(`Quest: ${quest.title}`, quest.points);
      
      const toast = await this.toastController.create({
        message: `🏆 Quest completed! +${quest.points} points`,
        duration: 3000,
        color: 'success',
        position: 'top'
      });
      await toast.present();

      // Mark quest as claimed (you'd save this to database)
      quest.claimed = true;
      
    } catch (error) {
      console.error('Error claiming quest:', error);
    }
  }

  // Check if user needs to refresh their profile after claiming daily bonus
  async refreshUserProfile() {
    if (this.currentUser) {
      await this.loadUserProfile();
      this.updateQuestProgress();
    }
  }

  getProgressPercentage(quest: any): number {
    return Math.min((quest.progress / quest.target) * 100, 100);
  }
}
