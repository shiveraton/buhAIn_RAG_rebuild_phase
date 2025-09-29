import { Component, OnInit } from '@angular/core';
import { Router } from '@angular/router';
import { AlertController, ToastController } from '@ionic/angular';
import { AuthService } from '../../../core/services/auth.service';

@Component({
  selector: 'app-dashboard',
  templateUrl: './dashboard.page.html',
  styleUrls: ['./dashboard.page.scss'],
  standalone: false,
})
export class DashboardPage implements OnInit {
  stats = {
    totalUsers: 0,
    totalTransliterations: 0,
    averageScore: 0,
    activeUsers: 0
  };

  recentActivity: any[] = [];
  topUsers: any[] = [];

  constructor(
    private authService: AuthService,
    private router: Router,
    private alertController: AlertController,
    private toastController: ToastController
  ) {}

  ngOnInit() {
    this.loadDashboardData();
  }

  loadDashboardData() {
    // Mock data - replace with actual API calls
    this.stats = {
      totalUsers: 1247,
      totalTransliterations: 5689,
      averageScore: 85.4,
      activeUsers: 234
    };

    this.recentActivity = [
      { user: 'John Doe', action: 'Completed Quest', time: '2 minutes ago' },
      { user: 'Jane Smith', action: 'New Registration', time: '5 minutes ago' },
      { user: 'Bob Johnson', action: 'Transliteration', time: '8 minutes ago' }
    ];

    this.topUsers = [
      { name: 'Alice Wonder', score: 2450, rank: 1 },
      { name: 'Charlie Brown', score: 2340, rank: 2 },
      { name: 'Diana Prince', score: 2180, rank: 3 }
    ];
  }

  refreshData() {
    this.loadDashboardData();
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
