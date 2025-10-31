import { Injectable } from '@angular/core';
import { CanActivate, Router } from '@angular/router';
import { Observable, from } from 'rxjs';
import { ToastController } from '@ionic/angular';
import { AuthenticationService } from '../services/authentication.service';
@Injectable({
  providedIn: 'root'
})
export class UserGuard implements CanActivate {

  constructor(
    private authenticationService: AuthenticationService,
    private router: Router,
    private toastController: ToastController
  ) {}

  async canActivate(): Promise<boolean> {
    console.log('UserGuard: canActivate called');
    
    const currentUser = this.authenticationService.getCurrentUser();
    console.log('UserGuard: Current Firebase user:', currentUser);
    
    if (!currentUser?.uid) {
      console.warn('UserGuard: No user logged in, blocking access');
      return false;
    }

    const role = await this.authenticationService.getRole(currentUser.uid);
    if (role === 'admin') {
      console.log('UserGuard: Admin detected, redirecting to admin tabs');
      this.showAdminRedirectToast();
      this.router.navigate(['/tabs-admin']);
      return false
    }
    return true
  }

  private async showAdminRedirectToast() {
    const toast = await this.toastController.create({
      message: '⚠️ Admin users cannot access user features. Redirecting to admin dashboard...',
      duration: 3000,
      position: 'top',
      color: 'warning',
      buttons: [{
        text: 'OK',
        role: 'cancel'
      }]
    });
    await toast.present();
  }
}
