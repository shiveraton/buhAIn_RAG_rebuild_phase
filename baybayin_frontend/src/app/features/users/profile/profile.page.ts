import { Component, OnInit, OnDestroy } from '@angular/core';
import { Router } from '@angular/router';
import { AlertController, ToastController } from '@ionic/angular';
import { AuthenticationService } from 'src/app/core/services/authentication.service';
import { Subscription } from 'rxjs';
import { User } from 'firebase/auth';

@Component({
  selector: 'app-profile',
  templateUrl: './profile.page.html',
  styleUrls: ['./profile.page.scss'],
  standalone: false
})
export class ProfilePage implements OnInit, OnDestroy {
  currentUser: User | null = null;
  userProfile: any;
  isLoading = true;
  private authSubscription?: Subscription;

  constructor(
    private authenticationService: AuthenticationService,
    private router: Router,
    private alertController: AlertController,
    private toastController: ToastController
  ) { }

  ngOnInit() {
    this.authSubscription = this.authenticationService.currentUser$.subscribe(async (user) => {
      this.currentUser = user;
      if (user) {
        this.userProfile = await this.authenticationService.getUserProfile(user.uid);
      }
      this.isLoading = false;
    });
  }

  ngOnDestroy() {
    if (this.authSubscription) {
      this.authSubscription.unsubscribe();
    }
  }

  async logout() {
    console.log("na click")
    const alert = await this.alertController.create({
      header: 'Confirm Logout',
      message: 'Are you sure you want to logout?',
      buttons: [
        { text: 'Cancel', role: 'cancel' },
        {
          text: 'Logout',
          handler: async () => {
            try {
              this.router.navigate(['/login']);
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
