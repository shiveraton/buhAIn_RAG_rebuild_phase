import { Component, OnInit, OnDestroy } from '@angular/core';
import { AuthService } from '../../../core/services/auth.service';
import { Subscription } from 'rxjs';
import { ThemeService } from '../../../core/services/theme.service';

@Component({
  selector: 'app-leaderboard',
  templateUrl: 'leaderboard.page.html',
  styleUrls: ['leaderboard.page.scss'],
  standalone: false,
})
export class LeaderboardPage implements OnInit, OnDestroy {
  leaderboard: any[] = [];
  fullLeaderboard: any[] = []; // Store full leaderboard data
  currentUser: any = null;
  isLoading = false;
  hasPermissionError = false;
  isOffline = false;
  currentTheme = 'light';
  
  // Pagination properties
  currentPage = 1;
  itemsPerPage = 10;
  totalPages = 1;
  
  private authSubscription?: Subscription;
  private themeSubscription?: Subscription;

  constructor(
    private authService: AuthService,
    private themeService: ThemeService
  ) {}

  async ngOnInit() {
    // Check initial online status
    this.isOffline = !navigator.onLine;
    
    // Listen for online/offline events
    window.addEventListener('online', () => {
      this.isOffline = false;
      if (this.currentUser) {
        this.loadLeaderboard();
      }
    });
    
    window.addEventListener('offline', () => {
      this.isOffline = true;
    });

    // Subscribe to authentication state changes
    this.authSubscription = this.authService.currentUser$.subscribe(async (user) => {
      this.currentUser = user;
      await this.loadLeaderboard();
    });

    // Subscribe to theme changes
    this.themeSubscription = this.themeService.theme$.subscribe(theme => {
      this.currentTheme = theme;
    });
    
    // Initialize theme
    this.currentTheme = this.themeService.getCurrentTheme();
  }

  ngOnDestroy() {
    if (this.authSubscription) {
      this.authSubscription.unsubscribe();
    }
    if (this.themeSubscription) {
      this.themeSubscription.unsubscribe();
    }
  }

  ionViewWillEnter() {
    // Refresh leaderboard every time user enters this page
    this.loadLeaderboard();
  }

  async loadLeaderboard() {
    // Only load leaderboard if user is authenticated
    if (!this.currentUser) {
      this.leaderboard = [];
      this.fullLeaderboard = [];
      this.totalPages = 0;
      this.currentPage = 1;
      this.isLoading = false;
      return;
    }

    this.isLoading = true;
    this.hasPermissionError = false;
    const startTime = Date.now();

    // Check if online before attempting to load
    if (!navigator.onLine) {
      console.log('Offline - skipping leaderboard load');
      this.isLoading = false;
      return;
    }

    try {
      // Set a timeout for the request
      const timeoutPromise = new Promise((_, reject) => 
        setTimeout(() => reject(new Error('Request timeout')), 10000)
      );
      
      const leaderboardPromise = this.authService.getLeaderboard();
      
      this.fullLeaderboard = await Promise.race([leaderboardPromise, timeoutPromise]) as any[];
      this.hasPermissionError = false; // Reset permission error flag on successful load
      
      // Calculate pagination
      this.totalPages = Math.ceil(this.fullLeaderboard.length / this.itemsPerPage);
      this.updatePaginatedLeaderboard();

      // Ensure minimum loading time of 3.5 seconds
      const elapsedTime = Date.now() - startTime;
      const remainingTime = Math.max(0, 3500 - elapsedTime);
      
      if (remainingTime > 0) {
        await new Promise(resolve => setTimeout(resolve, remainingTime));
      }
    } catch (error) {
      console.error('Error loading leaderboard:', error);
      this.leaderboard = [];
      this.fullLeaderboard = [];
      this.totalPages = 0;
      this.hasPermissionError = true; // Set permission error flag on error
      
      // Show user-friendly error message
      if (error instanceof Error) {
        if (error.message.includes('Permission denied')) {
          console.warn('Firebase Database rules need to be configured. Check FIREBASE_SETUP.md for instructions.');
        } else if (error.message.includes('timeout') || !navigator.onLine) {
          console.warn('Network timeout or offline - leaderboard unavailable');
        }
      }
    } finally {
      this.isLoading = false;
    }
  }

  async refreshLeaderboard(event: any) {
    try {
      // Only refresh if user is authenticated
      if (this.currentUser) {
        this.isLoading = true;
        const startTime = Date.now();
        
        this.fullLeaderboard = await this.authService.getLeaderboard();
        this.totalPages = Math.ceil(this.fullLeaderboard.length / this.itemsPerPage);
        this.updatePaginatedLeaderboard();

        // Ensure minimum loading time of 3.5 seconds
        const elapsedTime = Date.now() - startTime;
        const remainingTime = Math.max(0, 3500 - elapsedTime);
        
        if (remainingTime > 0) {
          await new Promise(resolve => setTimeout(resolve, remainingTime));
        }
      }
    } catch (error) {
      console.error('Error refreshing leaderboard:', error);
    } finally {
      this.isLoading = false;
      event.target.complete();
    }
  }

  getRankIcon(index: number): string {
    switch (index) {
      case 0: return 'trophy';      // 1st place - Gold trophy
      case 1: return 'medal';       // 2nd place - Silver medal  
      case 2: return 'ribbon';      // 3rd place - Bronze ribbon
      default: return 'star-outline'; // 4th place and below - Star outline
    }
  }

  getRankColor(index: number): string {
    switch (index) {
      case 0: return 'warning';   // Gold
      case 1: return 'medium';    // Silver
      case 2: return 'tertiary';  // Bronze
      default: return 'primary';  // Default blue for 4th place and below
    }
  }

  isCurrentUser(uid: string): boolean {
    return this.currentUser && this.currentUser.uid === uid;
  }

  // Pagination methods
  updatePaginatedLeaderboard() {
    const startIndex = (this.currentPage - 1) * this.itemsPerPage;
    const endIndex = startIndex + this.itemsPerPage;
    this.leaderboard = this.fullLeaderboard.slice(startIndex, endIndex);
  }

  nextPage() {
    if (this.currentPage < this.totalPages) {
      this.currentPage++;
      this.updatePaginatedLeaderboard();
    }
  }

  previousPage() {
    if (this.currentPage > 1) {
      this.currentPage--;
      this.updatePaginatedLeaderboard();
    }
  }

  goToPage(page: number) {
    if (page >= 1 && page <= this.totalPages) {
      this.currentPage = page;
      this.updatePaginatedLeaderboard();
    }
  }

  getPageNumbers(): number[] {
    const pages = [];
    for (let i = 1; i <= this.totalPages; i++) {
      pages.push(i);
    }
    return pages;
  }

  // Get global rank for a player (considering pagination)
  getGlobalRank(localIndex: number): number {
    return (this.currentPage - 1) * this.itemsPerPage + localIndex + 1;
  }

  // Get current user's global rank and data
  getCurrentUserRank(): { rank: number; data: any } | null {
    if (!this.currentUser || this.fullLeaderboard.length === 0) {
      return null;
    }
    
    const userIndex = this.fullLeaderboard.findIndex(player => player.uid === this.currentUser.uid);
    if (userIndex === -1) {
      return null;
    }
    
    return {
      rank: userIndex + 1,
      data: this.fullLeaderboard[userIndex]
    };
  }

  // Check if current user is visible on current page
  isCurrentUserOnCurrentPage(): boolean {
    if (!this.currentUser) return false;
    return this.leaderboard.some(player => player.uid === this.currentUser.uid);
  }

  // Get ordinal suffix for rank numbers (1st, 2nd, 3rd, etc.)
  getOrdinalSuffix(rank: number): string {
    const j = rank % 10;
    const k = rank % 100;
    
    if (j === 1 && k !== 11) {
      return 'st';
    }
    if (j === 2 && k !== 12) {
      return 'nd';
    }
    if (j === 3 && k !== 13) {
      return 'rd';
    }
    return 'th';
  }
}
