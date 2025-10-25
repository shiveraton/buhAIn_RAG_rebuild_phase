import { Injectable } from '@angular/core';
import { CanActivate, Router } from '@angular/router';
import { AuthService } from '../services/auth.service';
import { Observable, from } from 'rxjs';
import { ToastController } from '@ionic/angular';

@Injectable({
  providedIn: 'root'
})
export class UserGuard implements CanActivate {

  constructor(
    private authService: AuthService,
    private router: Router,
    private toastController: ToastController
  ) {}

  canActivate(): Observable<boolean> {
    console.log('UserGuard: canActivate called');
    
    const currentUser = this.authService.getCurrentUser();
    console.log('UserGuard: Current Firebase user:', currentUser);
    
    if (!currentUser?.uid) {
      console.warn('UserGuard: No user logged in, blocking access');
      return from([false]); // Simply block access
    }

    const isAdminUser = this.authService.isAdmin(currentUser);
    console.log('UserGuard: Is admin user?', isAdminUser);

    if (isAdminUser) {
      console.log('UserGuard: Admin detected, redirecting to admin tabs');
      this.showAdminRedirectToast();
      this.router.navigate(['/tabs-admin']);
      return from([false]); // Block user route, redirect to admin
    }

    console.log('UserGuard: Regular user, allowing access');
    return from([true]);
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
