import { Injectable } from '@angular/core';
import { CanActivate, Router } from '@angular/router';
import { AuthService } from '../services/auth.service';
import { Observable, from, timer } from 'rxjs';
import { switchMap, take, map, catchError } from 'rxjs/operators';
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
    
    // Get current Firebase user synchronously
    const currentUser = this.authService.getCurrentUser();
    console.log('UserGuard: Current Firebase user:', currentUser);
    
    if (!currentUser) {
      //console.log('UserGuard: No user logged in, redirecting to login');
      // Only redirect to login if truly no user
     // this.router.navigate(['/login']);
     // return from([false]);
    }

    const isAdminUser = this.authService.isAdmin(currentUser);
    console.log('UserGuard: Is admin user?', isAdminUser);

    if (isAdminUser) {
      console.log('UserGuard: Admin trying to access user routes - showing warning and staying put');
      // Admin trying to access user routes - show warning but DON'T navigate
      this.showAccessDeniedToast();
      return from([false]); // Block access but don't redirect
    }

    console.log('UserGuard: Regular user, allowing access');
    return from([true]);
  }

  private async showAccessDeniedToast() {
    const toast = await this.toastController.create({
      message: '⚠️ Access denied. Admin users cannot access user features.',
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
