import { Component, OnInit, OnDestroy } from '@angular/core';
import { AuthService } from '../services/auth.service';
import { LoadingController, RefresherEventDetail } from '@ionic/angular';
import { Subscription } from 'rxjs';

@Component({
  selector: 'app-leaderboard',
  templateUrl: 'leaderboard.page.html',
  styleUrls: ['leaderboard.page.scss'],
  standalone: false,
})
export class LeaderboardPage implements OnInit, OnDestroy {
  leaderboard: any[] = [];
  currentUser: any = null;
  isLoading = false;
  hasPermissionError = false;
  private authSubscription?: Subscription;

  constructor(
    private authService: AuthService,
    private loadingController: LoadingController
  ) {}

  async ngOnInit() {
    // Subscribe to authentication state changes
    this.authSubscription = this.authService.currentUser$.subscribe(async (user) => {
      this.currentUser = user;
      await this.loadLeaderboard();
    });
  }

  ngOnDestroy() {
    if (this.authSubscription) {
      this.authSubscription.unsubscribe();
    }
  }

  ionViewWillEnter() {
    // Refresh leaderboard every time user enters this page
    this.loadLeaderboard();
  }

  async loadLeaderboard() {
    // Only load leaderboard if user is authenticated
    if (!this.currentUser) {
      this.leaderboard = [];
      return;
    }

    this.isLoading = true;
    const loading = await this.loadingController.create({
      message: 'Loading leaderboard...',
    });
    await loading.present();

    try {
      this.leaderboard = await this.authService.getLeaderboard();
      this.hasPermissionError = false; // Reset permission error flag on successful load
    } catch (error) {
      console.error('Error loading leaderboard:', error);
      this.leaderboard = [];
      this.hasPermissionError = true; // Set permission error flag on error
      
      // Show user-friendly error message
      if (error instanceof Error && error.message.includes('Permission denied')) {
        // Firebase permission error - show helpful message
        console.warn('Firebase Database rules need to be configured. Check FIREBASE_SETUP.md for instructions.');
      }
    } finally {
      this.isLoading = false;
      await loading.dismiss();
    }
  }

  async refreshLeaderboard(event: any) {
    try {
      // Only refresh if user is authenticated
      if (this.currentUser) {
        this.leaderboard = await this.authService.getLeaderboard();
      }
    } catch (error) {
      console.error('Error refreshing leaderboard:', error);
    } finally {
      event.target.complete();
    }
  }

  getRankIcon(index: number): string {
    switch (index) {
      case 0: return 'trophy';
      case 1: return 'medal';
      case 2: return 'ribbon';
      default: return 'star-outline';
    }
  }

  getRankColor(index: number): string {
    switch (index) {
      case 0: return 'warning'; // Gold
      case 1: return 'medium'; // Silver
      case 2: return 'tertiary'; // Bronze
      default: return 'primary';
    }
  }

  isCurrentUser(uid: string): boolean {
    return this.currentUser && this.currentUser.uid === uid;
  }
}
