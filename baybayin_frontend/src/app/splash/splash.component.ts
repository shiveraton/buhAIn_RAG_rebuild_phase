import { Component, OnInit, OnDestroy } from '@angular/core';
import { Router, ActivatedRoute } from '@angular/router';
import { AuthService } from '../core/services/auth.service';
import { IonicModule } from '@ionic/angular';
import { CommonModule } from '@angular/common';

@Component({
  selector: 'app-splash',
  templateUrl: './splash.component.html',
  styleUrls: ['./splash.component.scss'],
  standalone: true,
  imports: [IonicModule, CommonModule]
})
export class SplashComponent implements OnInit, OnDestroy {
  loadingMessage = 'Loading...';
  splashTitle = 'Baybayin Learning App';
  splashSubtitle = 'Master the Ancient Filipino Script';
  private navigationTimer: any;
  private hasNavigated = false;

  constructor(
    private router: Router,
    private route: ActivatedRoute,
    private authService: AuthService
  ) {}

  ngOnInit() {
    console.log('Splash component initialized');

    // Adjust splash text based on query param (optional)
    this.route.queryParams.subscribe(params => {
      if (params['action'] === 'login') {
        this.loadingMessage = 'Logging in...';
        this.splashTitle = 'Welcome Back!';
        this.splashSubtitle = 'Continuing your Baybayin journey';
      } else if (params['action'] === 'signup') {
        this.loadingMessage = 'Setting up your account...';
        this.splashTitle = 'Welcome!';
        this.splashSubtitle = 'Starting your Baybayin learning adventure';
      } else {
        this.loadingMessage = 'Loading...';
        this.splashTitle = 'Baybayin Learning App';
        this.splashSubtitle = 'Master the Ancient Filipino Script';
      }
    });

    // Wait for 2 seconds to simulate splash duration
    this.navigationTimer = setTimeout(async () => {
      if (this.hasNavigated) return; // prevent double nav

      const currentUser = this.authService.getCurrentUser();
      console.log('Current user:', currentUser);

      if (currentUser?.uid) {
        try {
          // check if this UID belongs to an admin
          const isAdmin = await this.authService.checkUserAdmin(currentUser.uid);
          if (isAdmin) {
            console.log('Redirecting to admin tabs...');
            this.router.navigate(['/tabs-admin']);
          } else {
            console.log('Redirecting to user tabs...');
            this.router.navigate(['/tabs-user']);
          }
        } catch (error) {
          console.error('Error checking user role:', error);
          this.router.navigate(['/tabs-user']);
        }
      } else {
        console.log('No user found, redirecting to user tabs...');
        this.router.navigate(['/tabs-user']);
      }

      this.hasNavigated = true;
    }, 2000);
  }

  ngOnDestroy() {
    if (this.navigationTimer) {
      clearTimeout(this.navigationTimer);
    }
  }
}
