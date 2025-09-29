import { Injectable } from '@angular/core';
import { Preferences } from '@capacitor/preferences';
import { BehaviorSubject } from 'rxjs';

@Injectable({
  providedIn: 'root'
})
export class ThemeService {
  private currentTheme: string = 'light';
  private themeKey = 'theme_preference';
  public theme$ = new BehaviorSubject<string>('light');

  constructor() {
    // Load saved theme or use system preference
    this.initializeTheme();
  }

  async initializeTheme() {
    try {
      const { value: savedTheme } = await Preferences.get({ key: this.themeKey });
      
      if (savedTheme) {
        // Only accept 'light' or 'dark' theme values
        if (savedTheme === 'light' || savedTheme === 'dark') {
          this.currentTheme = savedTheme;
          console.log('Loading saved theme from preferences:', savedTheme);
        } else {
          // If we find an old 'auto' value, convert to light theme
          this.currentTheme = 'light';
          console.log('Found invalid theme value, defaulting to light');
          await Preferences.set({ key: this.themeKey, value: this.currentTheme });
        }
      } else {
        // Check system preference for default
        const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
        this.currentTheme = prefersDark ? 'dark' : 'light';
        console.log('No saved theme, using system preference:', this.currentTheme);
        // Save the default theme
        await Preferences.set({ key: this.themeKey, value: this.currentTheme });
      }
      
      // Force immediate theme application
      this.applyTheme(this.currentTheme);
      this.theme$.next(this.currentTheme);
    } catch (error) {
      console.error('Error initializing theme:', error);
      // Fallback to light theme
      this.applyTheme('light');
      this.theme$.next('light');
    }
    
    // Double check theme application after a short delay to ensure it's applied
    setTimeout(() => {
      if (!document.body.classList.contains('light-theme') && 
          !document.body.classList.contains('dark-theme')) {
        console.log('Theme not applied correctly, reapplying...');
        this.applyTheme(this.currentTheme);
      }
    }, 100);
  }

  getCurrentTheme(): string {
    return this.currentTheme;
  }

  async setTheme(theme: string): Promise<void> {
    try {
      this.currentTheme = theme;
      await Preferences.set({ key: this.themeKey, value: theme });
      this.applyTheme(theme);
      this.theme$.next(theme);
    } catch (error) {
      console.error('Error setting theme preference:', error);
    }
  }

  private applyTheme(theme: string) {
    // For immediate application and to ensure DOM is ready
    this.forceThemeApplication(theme);
    
    // Double-check after a short delay to make sure it was applied
    setTimeout(() => {
      const hasThemeClass = document.body.classList.contains('light-theme') || 
                            document.body.classList.contains('dark-theme');
      
      if (!hasThemeClass) {
        console.warn('Theme not applied correctly, re-applying...');
        this.forceThemeApplication(theme);
      }
    }, 100);
  }
  
  private forceThemeApplication(theme: string) {
    try {
      const body = document.body;
      console.log('Applying theme:', theme);
      
      // Remove existing theme classes
      body.classList.remove('light-theme', 'dark-theme');
      
      // Only apply light or dark theme (auto theme removed)
      if (theme !== 'light' && theme !== 'dark') {
        // If invalid theme value, default to light
        theme = 'light';
      }
      
      // Add specific theme class
      body.classList.add(`${theme}-theme`);
      
      // Update meta theme-color for mobile browsers
      const metaThemeColor = document.querySelector('meta[name="theme-color"]');
      if (metaThemeColor) {
        if (theme === 'dark') {
          metaThemeColor.setAttribute('content', '#1a1a1a');
        } else {
          metaThemeColor.setAttribute('content', '#3880ff');
        }
      }
      
      // Force a style recalculation - this ensures the styles are applied immediately
      const originalDisplay = body.style.display;
      body.style.display = 'none';
      body.offsetHeight; // Trigger a reflow
      body.style.display = originalDisplay;
      
      console.log('Theme applied. Current body classes:', body.className);
      
      // Force a repaint - helps with some tricky mobile browsers
      requestAnimationFrame(() => {
        document.documentElement.style.transition = 'background-color 0.0001s';
        setTimeout(() => {
          document.documentElement.style.transition = '';
        }, 20);
      });
    } catch (error) {
      console.error('Error applying theme:', error);
    }
  }

  async toggleTheme(): Promise<void> {
    const newTheme = this.currentTheme === 'light' ? 'dark' : 'light';
    await this.setTheme(newTheme);
  }

  isDarkMode(): boolean {
    return this.currentTheme === 'dark';
  }
  
  // No need to listen for system theme changes since auto mode is removed
  setupSystemThemeListener() {
    // This method is kept for backward compatibility but doesn't do anything now
    console.log('Auto theme mode disabled');
  }
}
