import { Component, OnInit, OnDestroy } from '@angular/core';
import { AuthenticationService } from 'src/app/core/services/authentication.service';
import { User } from 'firebase/auth';
import { Subscription } from 'rxjs';
import { Router } from '@angular/router';

@Component({
  selector: 'app-dashboard',
  templateUrl: './dashboard.page.html',
  styleUrls: ['./dashboard.page.scss'],
  standalone: false
})
export class DashboardPage implements OnInit, OnDestroy {

  xpPercentage: number = 0;
  userProfile: any = {
    username: 'buhainTest',
    level: 1,
    current_xp: 100
  };
  currentUser: User | null = null;
  private authSubscription?: Subscription;
  readonly next_level_xp = 1000;
  stars = Array.from({ length: 10 }, () => ({
    x: Math.random() * 100,
    y: Math.random() * 100
  }));

  constructor(
    private authenticationService: AuthenticationService,
    private router: Router
  ) {}

  ngOnInit() {
    this.authSubscription = this.authenticationService.currentUser$.subscribe(user => {
      this.currentUser = user;

      if (this.currentUser) {
        // Fetch user profile safely, fallback if null
        this.userProfile = this.authenticationService.getUserProfile(this.currentUser.uid) || {
          username: 'buhainTest',
          level: 1,
          current_xp: 100
        };
      }

      this.updateXpBar();
    });
  }

  ngOnDestroy() {
    if (this.authSubscription) this.authSubscription.unsubscribe();
  }

  navigateTo(page: string) {
    this.router.navigateByUrl(`/tabs-user/${page}`, { replaceUrl: true });
  }

  updateXpBar() {
    this.xpPercentage = Math.min(
      (this.userProfile.current_xp / this.next_level_xp) * 100,
      100
    );
  }

  get xpPercent(): number {
    return this.xpPercentage;
  }
}
