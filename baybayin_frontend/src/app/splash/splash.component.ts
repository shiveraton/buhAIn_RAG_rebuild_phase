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
  ) { }

  ngOnInit() {
    console.log('Splash component initialized');
    
    // Check for query parameters to determine the context
    this.route.queryParams.subscribe(params => {
      console.log('Query params:', params);
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

    // Simple, reliable navigation - always works
    this.navigationTimer = setTimeout(() => {
      console.log('Navigation timer triggered - going to tabs');
      this.router.navigate(['/tabs']);
    }, 2000); // Reduced to 2 seconds for faster UX
  }

  ngOnDestroy() {
    // Clean up timer
    if (this.navigationTimer) {
      clearTimeout(this.navigationTimer);
    }
  }
}
