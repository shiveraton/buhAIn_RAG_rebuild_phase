import { Component, OnInit } from '@angular/core';
import { Router } from '@angular/router';
import { AnalyticsService } from '../../../core/services/analytics.service';
import { AuthService } from '../../../core/services/auth.service';
import { LoadingController, ToastController, AlertController } from '@ionic/angular';

@Component({
  selector: 'app-analytics',
  templateUrl: './analytics.page.html',
  styleUrls: ['./analytics.page.scss'],
  standalone: false,
})
export class AnalyticsPage implements OnInit {
  analyticsData = {
    transliterationStats: {
      totalTransliterations: 0,
      textTransliterations: 0,
      imageTransliterations: 0,
      cameraTransliterations: 0
    },
    userEngagement: {
      dailyActiveUsers: 0,
      weeklyActiveUsers: 0,
      monthlyActiveUsers: 0,
      averageSessionTime: '0 min',
      totalUsers: 0
    },
    popularFeatures: [
      { name: 'Loading...', usage: 0 }
    ]
  };

  isLoading = false;

  constructor(
    private analyticsService: AnalyticsService,
    private authService: AuthService,
    private router: Router,
    private loadingController: LoadingController,
    private toastController: ToastController,
    private alertController: AlertController
  ) {}

  ngOnInit() {
    this.loadAnalytics();
  }

  async loadAnalytics() {
    this.isLoading = true;
    
    const loading = await this.loadingController.create({
      message: 'Loading analytics data...',
    });
    await loading.present();

    try {
      this.analyticsData = await this.analyticsService.getAnalyticsData();
      console.log('Real analytics data loaded:', this.analyticsData);
    } catch (error) {
      console.error('Error loading analytics:', error);
      this.showToast('Error loading analytics data', 'danger');
      
      // Keep default/mock data if loading fails
    } finally {
      this.isLoading = false;
      await loading.dismiss();
    }
  }

  async refreshAnalytics() {
    await this.loadAnalytics();
    this.showToast('Analytics refreshed!', 'success');
  }

  async logout() {
    const alert = await this.alertController.create({
      header: 'Confirm Logout',
      message: 'Are you sure you want to log out?',
      buttons: [
        {
          text: 'Cancel',
          role: 'cancel'
        },
        {
          text: 'Logout',
          role: 'confirm',
          handler: async () => {
            try {
              await this.authService.logout();
              this.router.navigate(['/login']);
            } catch (error) {
              console.error('Error logging out:', error);
              this.showToast('Error logging out. Please try again.', 'danger');
            }
          }
        }
      ]
    });

    await alert.present();
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
