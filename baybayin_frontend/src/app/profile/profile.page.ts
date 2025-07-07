import { Component, OnInit, OnDestroy } from '@angular/core';
import { Router } from '@angular/router';
import { AlertController, ToastController } from '@ionic/angular';
import { AuthService } from '../services/auth.service';
import { ScoreService } from '../services/score.service';
import { Subscription } from 'rxjs';
import { User } from 'firebase/auth';

@Component({
  selector: 'app-profile',
  templateUrl: './profile.page.html',
  styleUrls: ['./profile.page.scss'],
  standalone: false,
})
export class ProfilePage implements OnInit, OnDestroy {
  currentUser: User | null = null;
  userProfile: any = null;
  private authSubscription?: Subscription;

  constructor(
    private authService: AuthService,
    private scoreService: ScoreService,
    private router: Router,
    private alertController: AlertController,
    private toastController: ToastController
  ) { }

  ngOnInit() {
    // Subscribe to authentication state changes
    this.authSubscription = this.authService.currentUser$.subscribe(async (user) => {
      this.currentUser = user;
      if (user) {
        try {
          // Check for daily login bonus first
          const bonusAwarded = await this.scoreService.awardDailyBonus();
          
          // Then load/refresh user profile to show updated score
          this.userProfile = await this.authService.getUserProfile(user.uid);
          
        } catch (error) {
          console.error('Error fetching user profile:', error);
        }
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

  goToLogin() {
    this.router.navigate(['/login']);
  }

  goToSignup() {
    this.router.navigate(['/signup']);
  }

  async logout() {
    const alert = await this.alertController.create({
      header: 'Confirm Logout',
      message: 'Are you sure you want to logout?',
      buttons: [
        {
          text: 'Cancel',
          role: 'cancel'
        },
        {
          text: 'Logout',
          handler: async () => {
            try {
              await this.authService.signOut();
              this.showToast('Logged out successfully', 'success');
            } catch (error) {
              this.showToast('Error logging out', 'danger');
            }
          }
        }
      ]
    });

    await alert.present();
  }

  async claimDailyBonus() {
    await this.scoreService.awardDailyBonus();
    // Refresh user profile to show updated score
    if (this.currentUser) {
      try {
        this.userProfile = await this.authService.getUserProfile(this.currentUser.uid);
      } catch (error) {
        console.error('Error refreshing user profile:', error);
      }
    }
  }

  async refreshProfile() {
    if (this.currentUser) {
      try {
        this.userProfile = await this.authService.getUserProfile(this.currentUser.uid);
        this.showToast('Profile refreshed!', 'success');
      } catch (error) {
        console.error('Error refreshing user profile:', error);
        this.showToast('Error refreshing profile', 'danger');
      }
    }
  }

  private async showToast(message: string, color: string) {
    const toast = await this.toastController.create({
      message,
      duration: 2000,
      color,
      position: 'top'
    });
    await toast.present();
  }
}
