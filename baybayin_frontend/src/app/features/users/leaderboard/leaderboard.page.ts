import { Component, OnInit, OnDestroy } from '@angular/core';
import { GamifyAddonService } from 'src/app/core/services/gamify-addon.service';
import { AuthenticationService } from 'src/app/core/services/authentication.service';
import { Subscription } from 'rxjs';

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

  // Pagination properties
  currentPage = 1;
  itemsPerPage = 10;
  totalPages = 1;

  private authSubscription?: Subscription;

  constructor(private gamifyAddon: GamifyAddonService, private authenticationService: AuthenticationService) {}

  async ngOnInit() {
    // Check initial online status
    this.isOffline = !navigator.onLine;

    window.addEventListener('online', () => {
      this.isOffline = false;
      if (this.currentUser) this.loadLeaderboard();
    });

    window.addEventListener('offline', () => {
      this.isOffline = true;
    });

    this.authSubscription = this.authenticationService.currentUser$.subscribe((user) => {
      this.currentUser = user;
      this.loadLeaderboard();
    });
  }

  ngOnDestroy() {
    if (this.authSubscription) {
      this.authSubscription.unsubscribe();
    }
  }

  ionViewWillEnter() {
    this.loadLeaderboard();
  }

  async loadLeaderboard() {
    if (!this.currentUser || this.isOffline) {
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

    try {
      // Set timeout for leaderboard request
      const timeoutPromise = new Promise((_, reject) =>
        setTimeout(() => reject(new Error('Request timeout')), 10000)
      );

      const leaderboardPromise = this.gamifyAddon.getLeaderboard();
      this.fullLeaderboard = await Promise.race([leaderboardPromise, timeoutPromise]) as any[];

      // Calculate pagination
      this.totalPages = Math.ceil(this.fullLeaderboard.length / this.itemsPerPage);
      this.updatePaginatedLeaderboard();

      // Ensure minimum loading time
      const elapsedTime = Date.now() - startTime;
      const remainingTime = Math.max(0, 3500 - elapsedTime);
      if (remainingTime > 0) await new Promise(resolve => setTimeout(resolve, remainingTime));

    } catch (error) {
      console.error('Error loading leaderboard:', error);
      this.leaderboard = [];
      this.fullLeaderboard = [];
      this.totalPages = 0;
      this.hasPermissionError = true;
    } finally {
      this.isLoading = false;
    }
  }

  async refreshLeaderboard(event: any) {
    try {
      if (!this.currentUser) return;
      this.isLoading = true;
      const startTime = Date.now();

      this.fullLeaderboard = await this.gamifyAddon.getLeaderboard();
      this.totalPages = Math.ceil(this.fullLeaderboard.length / this.itemsPerPage);
      this.updatePaginatedLeaderboard();

      const elapsedTime = Date.now() - startTime;
      const remainingTime = Math.max(0, 3500 - elapsedTime);
      if (remainingTime > 0) await new Promise(resolve => setTimeout(resolve, remainingTime));
    } catch (error) {
      console.error('Error refreshing leaderboard:', error);
    } finally {
      this.isLoading = false;
      event.target.complete();
    }
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
    return Array.from({ length: this.totalPages }, (_, i) => i + 1);
  }

  getRankIcon(index: number): string {
    switch (index) {
      case 0: return 'trophy';
      case 1: return 'medal';
      case 2: return 'ribbon';
      default: return 'star-outline';
    }
  }

  getRankColor(index: number): string {
    switch (index) {
      case 0: return 'warning';
      case 1: return 'medium';
      case 2: return 'tertiary';
      default: return 'primary';
    }
  }

  isCurrentUser(uid: string): boolean {
    return this.currentUser && this.currentUser.uid === uid;
  }

  getGlobalRank(localIndex: number): number {
    return (this.currentPage - 1) * this.itemsPerPage + localIndex + 1;
  }

  getCurrentUserRank(): { rank: number; data: any } | null {
    if (!this.currentUser || this.fullLeaderboard.length === 0) return null;
    const userIndex = this.fullLeaderboard.findIndex(p => p.uid === this.currentUser.uid);
    if (userIndex === -1) return null;
    return { rank: userIndex + 1, data: this.fullLeaderboard[userIndex] };
  }

  isCurrentUserOnCurrentPage(): boolean {
    if (!this.currentUser) return false;
    return this.leaderboard.some(p => p.uid === this.currentUser.uid);
  }

  getOrdinalSuffix(rank: number): string {
    const j = rank % 10;
    const k = rank % 100;
    if (j === 1 && k !== 11) return 'st';
    if (j === 2 && k !== 12) return 'nd';
    if (j === 3 && k !== 13) return 'rd';
    return 'th';
  }
}
