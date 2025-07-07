import { Component, OnInit } from '@angular/core';
import { Router } from '@angular/router';
import { AuthService } from '../services/auth.service';
import { IonicModule } from '@ionic/angular';
import { CommonModule } from '@angular/common';

@Component({
  selector: 'app-splash',
  templateUrl: './splash.component.html',
  styleUrls: ['./splash.component.scss'],
  standalone: true,
  imports: [IonicModule, CommonModule]
})
export class SplashComponent implements OnInit {

  constructor(
    private router: Router,
    private authService: AuthService
  ) { }

  ngOnInit() {
    // Show splash screen for 3 seconds, then go to main app (tabs)
    setTimeout(() => {
      this.router.navigate(['/tabs']);
    }, 3000);
  }

  private checkAuthAndNavigate() {
    // Check if user is already authenticated
    this.authService.currentUser$.subscribe(user => {
      if (user) {
        // User is logged in, go to main app
        this.router.navigate(['/tabs']);
      } else {
        // User not logged in, go to login page
        this.router.navigate(['/login']);
      }
    });
  }
}
