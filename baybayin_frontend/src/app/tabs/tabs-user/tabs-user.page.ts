import { Component, OnInit } from '@angular/core';
import { BreakpointObserver, Breakpoints } from '@angular/cdk/layout';
import { Router } from '@angular/router';

@Component({
  selector: 'app-tabs-user',
  templateUrl: './tabs-user.page.html',
  styleUrls: ['./tabs-user.page.scss'],
  standalone: false,
})
export class TabsUserPage implements OnInit {
  isMobile: boolean = false;

  constructor(
    private breakpointObserver: BreakpointObserver,
    private router: Router
  ) {}

  ngOnInit() {
    // Treat mobile and tablet as the same layout
    this.breakpointObserver
      .observe([Breakpoints.Handset, Breakpoints.Tablet])
      .subscribe(result => {
        this.isMobile = result.matches;
      });
  }

  // Function to check active route for mobile tab indicator
  isActive(route: string): boolean {
    return this.router.url === route;
  }
}
