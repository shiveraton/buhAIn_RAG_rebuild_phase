import { Injectable } from '@angular/core';
import { CanActivate, Router } from '@angular/router';
import { AuthService } from '../services/auth.service';
import { Observable, from } from 'rxjs';
import { switchMap, take } from 'rxjs/operators';
import { ToastController } from '@ionic/angular';

@Injectable({
  providedIn: 'root'
})
export class AdminGuard implements CanActivate {

  constructor(
    private authService: AuthService,
    private router: Router,
    private toastController: ToastController
  ) {}

  canActivate(): Observable<boolean> {
    console.log('AdminGuard: canActivate called');
    
    // Get current Firebase user synchronously
    const currentUser = this.authService.getCurrentUser();
    console.log('AdminGuard: Current Firebase user:', currentUser);
    
    if (!currentUser) {
      console.log('AdminGuard: No user logged in, redirecting to login');
      // Only redirect to login if truly no user
      this.router.navigate(['/login']);
      return from([false]);
    }

    const isAdminUser = this.authService.isAdmin(currentUser);
    console.log('AdminGuard: Is admin user?', isAdminUser);

    if (!isAdminUser) {
      console.log('AdminGuard: Regular user trying to access admin routes - showing warning and staying put');
      // Regular user trying to access admin routes - show warning but DON'T navigate
      this.showAccessDeniedToast();
      return from([false]); // Block access but don't redirect
    }

    console.log('AdminGuard: Admin user, allowing access');
    return from([true]);
  }

  private async showAccessDeniedToast() {
    const toast = await this.toastController.create({
      message: '🚫 Access denied. Only administrators can access this area.',
      duration: 3000,
      position: 'top',
      color: 'danger',
      buttons: [{
        text: 'OK',
        role: 'cancel'
      }]
    });
    await toast.present();
  }
}
