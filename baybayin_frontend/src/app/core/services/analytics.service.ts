import { Injectable } from '@angular/core';
import { initializeApp } from 'firebase/app';
import { 
  getDatabase, 
  ref, 
  get, 
  query, 
  orderByChild, 
  limitToLast,
  startAt,
  endAt
} from 'firebase/database';
import { environment } from '../../../environments/environment';

@Injectable({
  providedIn: 'root'
})
export class AnalyticsService {
  private app = initializeApp(environment.firebase);
  private db = getDatabase(this.app);

  constructor() { }

  // Get real transliteration statistics
  async getTransliterationStats() {
    try {
      const usersRef = ref(this.db, 'users'); // Only regular users, not admins
      const snapshot = await get(usersRef);
      
      let totalTransliterations = 0;
      let textTransliterations = 0;
      let imageTransliterations = 0;
      let cameraTransliterations = 0;

      if (snapshot.exists()) {
        const users = snapshot.val();
        Object.values(users).forEach((user: any) => {
          // Skip admin users (they shouldn't be in users path anyway)
          if (user.isAdmin) return;
          
          // Sum up daily and weekly transliterations from all users
          totalTransliterations += (user.dailyTransliterations || 0) + (user.weeklyTransliterations || 0);
        });
        
        // Calculate breakdown estimates after getting total
        textTransliterations = Math.floor(totalTransliterations * 0.6); // 60% text
        imageTransliterations = Math.floor(totalTransliterations * 0.3); // 30% image
        cameraTransliterations = Math.floor(totalTransliterations * 0.1); // 10% camera
      }

      return {
        totalTransliterations,
        textTransliterations,
        imageTransliterations,
        cameraTransliterations
      };
    } catch (error) {
      console.error('Error getting transliteration stats:', error);
      // Return mock data if Firebase fails
      return {
        totalTransliterations: 0,
        textTransliterations: 0,
        imageTransliterations: 0,
        cameraTransliterations: 0
      };
    }
  }

  // Get user engagement statistics
  async getUserEngagement() {
    try {
      const usersRef = ref(this.db, 'users'); // Only regular users, not admins
      const snapshot = await get(usersRef);
      
      let totalUsers = 0;
      let dailyActiveUsers = 0;
      let weeklyActiveUsers = 0;
      let monthlyActiveUsers = 0;
      let totalGamesPlayed = 0;

      const today = new Date().toISOString().split('T')[0];
      const oneWeekAgo = new Date();
      oneWeekAgo.setDate(oneWeekAgo.getDate() - 7);
      const oneMonthAgo = new Date();
      oneMonthAgo.setDate(oneMonthAgo.getDate() - 30);

      if (snapshot.exists()) {
        const users = snapshot.val();
        totalUsers = Object.keys(users).length; // Count only regular users

        Object.values(users).forEach((user: any) => {
          // Skip admin users (they shouldn't be in users path anyway)
          if (user.isAdmin) return;
          
          totalGamesPlayed += user.gamesPlayed || 0;

          // Check daily active users (logged in today)
          if (user.lastLoginDate === today) {
            dailyActiveUsers++;
          }

          // Check weekly active users (logged in within last 7 days)
          if (user.lastLoginDate && new Date(user.lastLoginDate) >= oneWeekAgo) {
            weeklyActiveUsers++;
          }

          // Check monthly active users (logged in within last 30 days)
          if (user.lastLoginDate && new Date(user.lastLoginDate) >= oneMonthAgo) {
            monthlyActiveUsers++;
          }
        });
      }

      // Calculate average session time (estimated based on games played)
      const avgSessionTime = totalGamesPlayed > 0 ? 
        `${Math.floor((totalGamesPlayed * 2.5))} min` : '0 min'; // Estimate 2.5 min per game

      return {
        dailyActiveUsers,
        weeklyActiveUsers,
        monthlyActiveUsers,
        averageSessionTime: avgSessionTime,
        totalUsers
      };
    } catch (error) {
      console.error('Error getting user engagement:', error);
      return {
        dailyActiveUsers: 0,
        weeklyActiveUsers: 0,
        monthlyActiveUsers: 0,
        averageSessionTime: '0 min',
        totalUsers: 0
      };
    }
  }

  // Get popular features based on real usage
  async getPopularFeatures() {
    try {
      const usersRef = ref(this.db, 'users'); // Only regular users, not admins
      const snapshot = await get(usersRef);
      
      let textUsage = 0;
      let gamesPlayed = 0;
      let questsEngagement = 0;

      if (snapshot.exists()) {
        const users = snapshot.val();
        Object.values(users).forEach((user: any) => {
          // Skip admin users (they shouldn't be in users path anyway)
          if (user.isAdmin) return;
          
          textUsage += user.dailyTransliterations || 0;
          gamesPlayed += user.gamesPlayed || 0;
          
          // Check if user has quest data (engagement indicator)
          if (user.weeklyTransliterations > 0 || user.dailyTransliterations > 0) {
            questsEngagement++;
          }
        });
      }

      // Calculate percentages based on total usage
      const totalUsage = textUsage + gamesPlayed + questsEngagement;
      
      return [
        { 
          name: 'Text Transliteration', 
          usage: totalUsage > 0 ? Math.round((textUsage / totalUsage) * 100) : 0
        },
        { 
          name: 'Games', 
          usage: totalUsage > 0 ? Math.round((gamesPlayed / totalUsage) * 100) : 0
        },
        { 
          name: 'Quests', 
          usage: totalUsage > 0 ? Math.round((questsEngagement / totalUsage) * 100) : 0
        },
        { 
          name: 'Image/Camera Upload', 
          usage: 15 // Placeholder since we don't track this yet
        }
      ].sort((a, b) => b.usage - a.usage); // Sort by usage descending
    } catch (error) {
      console.error('Error getting popular features:', error);
      return [
        { name: 'Text Transliteration', usage: 0 },
        { name: 'Games', usage: 0 },
        { name: 'Quests', usage: 0 },
        { name: 'Image/Camera Upload', usage: 0 }
      ];
    }
  }

  // Get comprehensive analytics data
  async getAnalyticsData() {
    try {
      const [transliterationStats, userEngagement, popularFeatures] = await Promise.all([
        this.getTransliterationStats(),
        this.getUserEngagement(),
        this.getPopularFeatures()
      ]);

      return {
        transliterationStats,
        userEngagement,
        popularFeatures
      };
    } catch (error) {
      console.error('Error getting analytics data:', error);
      throw error;
    }
  }
}
