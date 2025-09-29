import { Component, OnInit } from '@angular/core';
import { Router, ActivatedRoute } from '@angular/router';
import { ThemeService } from '../../../core/services/theme.service';
import { AuthService } from '../../../core/services/auth.service';
import { AlertController, ToastController } from '@ionic/angular';
import { Preferences } from '@capacitor/preferences';

@Component({
  selector: 'app-settings',
  templateUrl: './settings.page.html',
  styleUrls: ['./settings.page.scss'],
  standalone: false,
})
export class SettingsPage implements OnInit {
  currentTheme: string = 'light';
  notificationsEnabled: boolean = true;
  soundEnabled: boolean = true;
  dailyReminders: boolean = true;
  practiceReminders: boolean = true;
  difficultyLevel: string = 'medium';
  autoSave: boolean = true;
  privateLearning: boolean = false;
  returnTo: string = '/tabs/profile'; // Default return location

  constructor(
    private router: Router,
    private route: ActivatedRoute,
    private themeService: ThemeService,
    private authService: AuthService,
    private alertController: AlertController,
    private toastController: ToastController
  ) {}

  async ngOnInit() {
    // Check for returnTo query parameter
    this.route.queryParams.subscribe(params => {
      if (params['returnTo']) {
        this.returnTo = params['returnTo'];
      }
    });

    // Load current theme from ThemeService
    this.currentTheme = this.themeService.getCurrentTheme();
    
    // Subscribe to theme changes
    this.themeService.theme$.subscribe(theme => {
      this.currentTheme = theme;
    });
    
    // Load user preferences
    await this.loadUserPreferences();
  }

  goBack() {
    this.router.navigate([this.returnTo]);
  }

  async onThemeToggleChange(event: any) {
    const isDarkMode = event.detail.checked;
    const theme = isDarkMode ? 'dark' : 'light';
    this.currentTheme = theme;
    await this.themeService.setTheme(theme);
    
    const toast = await this.toastController.create({
      message: `Theme changed to ${theme} mode`,
      duration: 2000,
      position: 'bottom',
      color: 'success'
    });
    toast.present();
  }

  async onNotificationToggle(event: any) {
    this.notificationsEnabled = event.detail.checked;
    // Save preference logic here
    await this.savePreference('notifications', this.notificationsEnabled);
  }

  async onSoundToggle(event: any) {
    this.soundEnabled = event.detail.checked;
    await this.savePreference('sound', this.soundEnabled);
  }

  async onDailyRemindersToggle(event: any) {
    this.dailyReminders = event.detail.checked;
    await this.savePreference('dailyReminders', this.dailyReminders);
  }

  async onPracticeRemindersToggle(event: any) {
    this.practiceReminders = event.detail.checked;
    await this.savePreference('practiceReminders', this.practiceReminders);
  }

  async onDifficultyChange(event: any) {
    this.difficultyLevel = event.detail.value;
    await this.savePreference('difficultyLevel', this.difficultyLevel);
  }

  async onAutoSaveToggle(event: any) {
    this.autoSave = event.detail.checked;
    await this.savePreference('autoSave', this.autoSave);
  }

  async onPrivateLearningToggle(event: any) {
    this.privateLearning = event.detail.checked;
    await this.savePreference('privateLearning', this.privateLearning);
  }

  async resetProgress() {
    const alert = await this.alertController.create({
      header: 'Reset Progress',
      message: 'Are you sure you want to reset all your learning progress? This action cannot be undone.',
      buttons: [
        {
          text: 'Cancel',
          role: 'cancel'
        },
        {
          text: 'Reset',
          role: 'destructive',
          handler: async () => {
            // Implement reset logic here
            const toast = await this.toastController.create({
              message: 'Progress reset successfully',
              duration: 2000,
              position: 'bottom',
              color: 'warning'
            });
            toast.present();
          }
        }
      ]
    });
    await alert.present();
  }

  async exportData() {
    const toast = await this.toastController.create({
      message: 'Exporting your data...',
      duration: 2000,
      position: 'bottom',
      color: 'primary'
    });
    toast.present();
    
    // Implement data export logic here
  }

  async deleteAccount() {
    const alert = await this.alertController.create({
      header: 'Delete Account',
      message: 'Are you sure you want to permanently delete your account? This action cannot be undone and all your data will be lost.',
      buttons: [
        {
          text: 'Cancel',
          role: 'cancel'
        },
        {
          text: 'Delete',
          role: 'destructive',
          handler: async () => {
            try {
              // Implement account deletion logic here
              // For now, we'll just sign out the user
              await this.authService.logout();
              this.router.navigate(['/login']);
            } catch (error) {
              console.error('Error deleting account:', error);
              const toast = await this.toastController.create({
                message: 'Error deleting account. Please try again.',
                duration: 3000,
                position: 'bottom',
                color: 'danger'
              });
              toast.present();
            }
          }
        }
      ]
    });
    await alert.present();
  }

  async quickSetTheme(theme: string) {
    if (theme === this.currentTheme) return;
    
    this.currentTheme = theme;
    await this.themeService.setTheme(theme);
    
    // Provide haptic feedback if available
    try {
      if ((navigator as any).vibrate) {
        (navigator as any).vibrate(50);
      }
    } catch (error) {
      console.error('Vibration API error:', error);
    }
    
    const toast = await this.toastController.create({
      message: `Theme changed to ${theme} mode`,
      duration: 1500,
      position: 'bottom',
      color: 'success'
    });
    toast.present();
  }

  private async loadUserPreferences() {
    try {
      // Get user preferences using Capacitor Preferences
      const { value: prefsString } = await Preferences.get({ key: 'userPreferences' });
      
      if (prefsString) {
        const prefs = JSON.parse(prefsString);
        this.notificationsEnabled = prefs.notifications ?? true;
        this.soundEnabled = prefs.sound ?? true;
        this.dailyReminders = prefs.dailyReminders ?? true;
        this.practiceReminders = prefs.practiceReminders ?? true;
        this.difficultyLevel = prefs.difficultyLevel ?? 'medium';
        this.autoSave = prefs.autoSave ?? true;
        this.privateLearning = prefs.privateLearning ?? false;
      }
    } catch (error) {
      console.error('Error loading preferences:', error);
      // If there's an error, use defaults
    }
  }

  private async savePreference(key: string, value: any) {
    try {
      // Get current preferences
      const { value: prefsString } = await Preferences.get({ key: 'userPreferences' });
      const prefs = prefsString ? JSON.parse(prefsString) : {};
      
      // Update the specific preference
      prefs[key] = value;
      
      // Save back to Preferences
      await Preferences.set({
        key: 'userPreferences',
        value: JSON.stringify(prefs)
      });
      
      // Show a toast notification
      const toast = await this.toastController.create({
        message: 'Preference saved',
        duration: 1500,
        position: 'bottom',
        color: 'success'
      });
      toast.present();
    } catch (error) {
      console.error('Error saving preference:', error);
      // Show an error toast
      const errorToast = await this.toastController.create({
        message: 'Failed to save preference',
        duration: 2000,
        position: 'bottom',
        color: 'danger'
      });
      errorToast.present();
    }
  }
}
