<<<<<<< HEAD
import { Component, OnInit, OnDestroy, Renderer2 } from '@angular/core';
import { ThemeService } from './core/services/theme.service';
import { AuthService } from './core/services/auth.service';
import { Platform } from '@ionic/angular';
import { Subscription } from 'rxjs';
import { StatusBar, Style } from '@capacitor/status-bar';
=======
import { Component } from '@angular/core';
>>>>>>> main

@Component({
  selector: 'app-root',
  templateUrl: 'app.component.html',
  styleUrls: ['app.component.scss'],
  standalone: false,
})
<<<<<<< HEAD
export class AppComponent implements OnInit, OnDestroy {

  private themeSubscription: Subscription | undefined;

  // Dynamically switch between dark and light mode
  switchTheme(isDark: boolean) {
    if (isDark) {
      this.renderer.addClass(document.body, 'dark-theme');
      this.renderer.removeClass(document.body, 'light-theme');
    } else {
      this.renderer.addClass(document.body, 'light-theme');
      this.renderer.removeClass(document.body, 'dark-theme');
    }
  }

  // Add method to set light theme
  setLightTheme() {
    this.themeService.setTheme('light');
  }

  constructor(
    private themeService: ThemeService,
    private authService: AuthService,
    private platform: Platform,
    private renderer: Renderer2
  ) {}

  async ngOnInit() {
    try {
      // Wait for the platform to be ready
      await this.platform.ready();
      
      // Add transition class to body for smooth theme changes
      this.renderer.addClass(document.body, 'theme-transition');
      
      // Check for admin session on app startup
      this.authService.checkAdminSession();
      
      // Initialize theme on app startup
      await this.themeService.initializeTheme();
      
      // Setup system theme listener for auto theme mode
      this.themeService.setupSystemThemeListener();
      
      // Subscribe to theme changes
      this.themeSubscription = this.themeService.theme$.subscribe(theme => {
        console.log('Theme changed to:', theme);
        
        // Update status bar style for native platforms
        if (this.platform.is('hybrid')) {
          try {
            if (theme === 'dark' || (theme === 'auto' && window.matchMedia('(prefers-color-scheme: dark)').matches)) {
              StatusBar.setStyle({ style: Style.Dark });
            } else {
              StatusBar.setStyle({ style: Style.Light });
            }
          } catch (error) {
            console.error('Error setting status bar style:', error);
          }
        }

        // Dynamically update theme class on body
        this.switchTheme(theme === 'dark' || (theme === 'auto' && window.matchMedia('(prefers-color-scheme: dark)').matches));
      });
    } catch (error) {
      console.error('Error initializing app:', error);
    }
  }
  
  ngOnDestroy() {
    // Clean up subscription when component is destroyed
    if (this.themeSubscription) {
      this.themeSubscription.unsubscribe();
    }
  }
=======
export class AppComponent {
  constructor() {}
>>>>>>> main
}
