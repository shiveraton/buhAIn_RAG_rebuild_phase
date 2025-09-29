import { Component, OnInit } from '@angular/core';
import { Router } from '@angular/router';
import { AuthService } from '../../core/services/auth.service';

@Component({
  selector: 'app-admin',
  templateUrl: './admin.page.html',
  styleUrls: ['./admin.page.scss'],
  standalone: false,
})
export class AdminPage implements OnInit {
  currentUser: any = null;

  constructor(
    private router: Router,
    private authService: AuthService
  ) {}

  ngOnInit() {
    // Check if user is admin
    this.authService.currentUser$.subscribe(user => {
      this.currentUser = user;
      if (!user || !this.isAdmin(user)) {
        this.router.navigate(['/tabs']);
      }
    });
  }

  isAdmin(user: any): boolean {
    return user && (user.email === 'admin@gmail.com' || user.isAdmin === true);
  }

  async logout() {
    try {
      await this.authService.logout();
      // Always redirect admin to login page
      this.router.navigate(['/login']);
    } catch (error) {
      console.error('Logout error:', error);
      // Even if logout fails, redirect to login
      this.router.navigate(['/login']);
    }
  }

  openSettings() {    // Navigate to settings with admin context so it returns to admin panel
    this.router.navigate(['/settings'], {
      queryParams: { returnTo: '/tabs/analytics' }
    });
  }
}
