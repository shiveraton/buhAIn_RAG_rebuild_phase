import { Component, OnInit, OnDestroy } from '@angular/core';
import { Router } from '@angular/router';
import { AuthService } from '../core/services/auth.service';
import { Subscription } from 'rxjs';

@Component({
  selector: 'app-tabs',
  templateUrl: 'tabs.page.html',
  styleUrls: ['tabs.page.scss'],
  standalone: false,
})
export class TabsPage implements OnInit, OnDestroy {
  isAdmin = false;
  isAuthenticated = false; // <-- new flag to control tab visibility for logged-in users
  private authSubscription?: Subscription;

  constructor(
    private authService: AuthService,
    private router: Router
  ) {}

  ngOnInit() {
    // Subscribe to auth state changes to detect admin vs user and auth status
    this.authSubscription = this.authService.currentUser$.subscribe(user => {
      const wasAdmin = this.isAdmin;
      const wasAuth = this.isAuthenticated;

      this.isAuthenticated = !!user;
      this.isAdmin = this.authService.isAdmin(user);
      
      console.log('TabsPage: User updated - isAuthenticated:', this.isAuthenticated, 'isAdmin:', this.isAdmin);
      
      // If user type or auth changed, redirect to appropriate default tab
      if (wasAdmin !== this.isAdmin || wasAuth !== this.isAuthenticated) {
        this.redirectToDefaultTab();
      }
    });
  }

  ngOnDestroy() {
    if (this.authSubscription) {
      this.authSubscription.unsubscribe();
    }
  }

  private redirectToDefaultTab() {
    const currentPath = this.router.url;
    
    // Redirect if we're on base tabs path OR if user type doesn't match current route
    if (currentPath === '/tabs' || currentPath === '/tabs/' || 
        (this.isAdmin && currentPath.includes('/tabs/transliteration')) ||
        (!this.isAdmin && (currentPath.includes('/tabs/analytics') || currentPath.includes('/tabs/dashboard')))) {
      
      if (this.isAdmin) {
        console.log('TabsPage: Redirecting admin to analytics');
        this.router.navigate(['/tabs/analytics']);
      } else {
        console.log('TabsPage: Redirecting user to transliteration');
        this.router.navigate(['/tabs/transliteration']);
      }
    }
  }

  async logout() {
    try {
      await this.authService.logout();
      this.router.navigate(['/login']);
    } catch (error) {
      console.error('Error logging out:', error);
    }
  }
}
