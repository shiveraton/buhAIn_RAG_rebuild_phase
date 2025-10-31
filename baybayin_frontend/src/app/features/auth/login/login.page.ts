import { Component, OnInit } from '@angular/core';
import { Router } from '@angular/router';
import { AlertController, LoadingController, ToastController } from '@ionic/angular';
import { AuthenticationService } from 'src/app/core/services/authentication.service';

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
    private authenticationService: AuthenticationService,
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
      const currentUser = await this.authenticationService.login(this.email, this.password);
      await loading.dismiss();
      if (currentUser?.uid) {
        const role = await this.authenticationService.getRole(currentUser.uid);
        if (role == 'admin') {
          this.showToast('Admin login successful!', 'success');
          this.router.navigate(['/tabs-admin']);
        } else {
          this.showToast('Login successful!', 'success');
          this.router.navigate(['/tabs-user']);
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
