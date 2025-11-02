import { Component, OnInit } from '@angular/core';
import { Router } from '@angular/router';
import { AlertController, LoadingController, ToastController } from '@ionic/angular';
import { AuthenticationService } from 'src/app/core/services/authentication.service';
import { RegisterService } from 'src/app/core/services/register.service';

@Component({
  selector: 'app-signup',
  templateUrl: './signup.page.html',
  styleUrls: ['./signup.page.scss'],
  standalone: false,
})
export class SignupPage implements OnInit {
  email: string = '';
  password: string = '';
  confirmPassword: string = '';
  username: string = '';

  constructor(
    private registerSerivce: RegisterService,
    private router: Router,
    private authenticationService: AuthenticationService,
    private loadingController: LoadingController,
    private toastController: ToastController
  ) { }

  ngOnInit() {
  }

  async signup() {
    if (!this.email || !this.password || !this.confirmPassword || !this.username) {
      this.showToast('Please fill in all fields', 'warning');
      return;
    }

    if (this.password !== this.confirmPassword) {
      this.showToast('Passwords do not match', 'warning');
      return;
    }

    if (this.password.length < 6) {
      this.showToast('Password must be at least 6 characters long', 'warning');
      return;
    }

    const loading = await this.loadingController.create({
      message: 'Creating account...',
    });
    await loading.present();

    try {
      await this.registerSerivce.register(this.email, this.password, this.username);
      await loading.dismiss();
      this.showToast('Account created successfully!', 'success');

      const user = await this.authenticationService.login(this.email, this.password);
      if (user?.uid) {
        const role = await this.authenticationService.getRole(user.uid);
        if (role === 'admin') {
          this.router.navigate(['/tabs-admin']);
        } else {
          this.router.navigate(['/tabs-user']);
        }
      }
    } catch (error: any) {
      await loading.dismiss();
      this.showToast(this.getErrorMessage(error.code), 'danger');
    }
  }

  goToLogin() {
    this.router.navigate(['/login']);
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
      case 'auth/email-already-in-use':
        return 'An account with this email already exists.';
      case 'auth/invalid-email':
        return 'Invalid email address.';
      case 'auth/weak-password':
        return 'Password is too weak. Please choose a stronger password.';
      default:
        return 'An error occurred during signup. Please try again.';
    }
  }
}
