import { Injectable } from '@angular/core';
import { CanActivate, Router } from '@angular/router';
import { AuthenticationService } from '../services/authentication.service';
import { Platform } from '@ionic/angular';

@Injectable({
  providedIn: 'root'
})
export class AdminGuard implements CanActivate {

  constructor(
    private authenticationService: AuthenticationService,
    private router: Router,
    private platform: Platform
  ) {}

  async canActivate(): Promise<boolean> {
    const user = this.authenticationService.getCurrentUser();
    if (!user?.uid) {
      console.warn('No user logged in, redirecting to user tabs');
      this.router.navigate(['/login']);
      return false;
    }

    const role = await this.authenticationService.getRole(user.uid);
    if (role == 'admin' && (this.platform.is('mobile') || this.platform.is('hybrid'))) {
      console.warn('Admin access blocked on mobile device');
      this.router.navigate(['/logout'])
      return false;
    }
    if (role == "admin"){
      console.log("admin")
      return true
    }
    console.log("user")
    this.router.navigate(['/tabs-user'])
    return false;
  }
}

