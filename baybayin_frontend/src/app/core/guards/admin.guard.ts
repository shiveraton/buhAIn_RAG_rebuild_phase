import { Injectable } from '@angular/core';
import { CanActivate, Router } from '@angular/router';
import { AuthService } from '../services/auth.service';
import { Observable, from } from 'rxjs';
import { switchMap, take } from 'rxjs/operators';
import { Platform, ToastController } from '@ionic/angular';

@Injectable({
  providedIn: 'root'
})
export class AdminGuard implements CanActivate {

  constructor(
    private authService: AuthService,
    private router: Router,
    private toastController: ToastController,
    private platform: Platform
  ) {}

  async canActivate(): Promise<boolean> {

    const user = this.authService.getCurrentUser();
    console.log("Here")
    if (!user?.uid) {
      console.warn('No user logged in, redirecting to user tabs');
      this.router.navigate(['/tabs-user']);
      return false;
    }

    const isAdmin = await this.authService.checkUserAdmin(user.uid);

    if (isAdmin && (this.platform.is('mobile') || this.platform.is('hybrid'))) {
      console.warn('Admin access blocked on mobile device');
      this.router.navigate(['/tabs-user']);
      return false;
    }

    if (isAdmin) {
      return true; 
    }

    this.router.navigate(['/tabs-user']);
    return false;
  }
}

