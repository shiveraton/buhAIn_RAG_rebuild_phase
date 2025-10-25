import { Component, OnInit } from '@angular/core';
import { Router } from '@angular/router';
import { AlertController, LoadingController, ToastController } from '@ionic/angular';
import { AuthService } from '../../../core/services/auth.service';

@Component({
  selector: 'app-login',
  templateUrl: './login.page.html',
  styleUrls: ['./login.page.scss'],
  standalone: false,
})
export class LoginPage implements OnInit {
  email: string = '';
  password: string = '';

  constructor(
    private authService: AuthService,
    private router: Router,
    private alertController: AlertController,
    private loadingController: LoadingController,
    private toastController: ToastController
  ) { }

  ngOnInit() {}

  async login() {
    if (!this.email || !this.password) {
      this.showToast('Please fill in all fields', 'warning');
      return;
    }

    const loading = await this.loadingController.create({
      message: 'Signing in...',
    });
    await loading.present();

    try {
      const result = await this.authService.signIn(this.email, this.password);

      // Ensure loading is dismissed
      await loading.dismiss();

      const currentUser = result.user;
      if (currentUser?.uid) {
        const isAdmin = await this.authService.checkUserAdmin(currentUser.uid);
        if (isAdmin) {
          // Admin login
          this.showToast('Admin login successful!', 'success');
          this.router.navigate(['/tabs-admin']);
        } else {
          // Regular user login
          this.showToast('Login successful!', 'success');
          this.router.navigate(['/splash'], { queryParams: { action: 'login' } });
        }
      } else {
        this.showToast('Login failed: user not found.', 'danger');
      }
    } catch (error: any) {
      await loading.dismiss();
      this.showToast(this.getErrorMessage(error.code), 'danger');
    }
  }

  goToSignup() {
    this.router.navigate(['/signup']);
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

  private getErrorMessage(errorCode: string): string {
    switch (errorCode) {
      case 'auth/user-not-found':
        return 'No user found with this email address.';
      case 'auth/wrong-password':
        return 'Incorrect password.';
      case 'auth/invalid-email':
        return 'Invalid email address.';
      case 'auth/user-disabled':
        return 'This account has been disabled.';
      default:
        return 'An error occurred during login. Please try again.';
    }
  }
}
