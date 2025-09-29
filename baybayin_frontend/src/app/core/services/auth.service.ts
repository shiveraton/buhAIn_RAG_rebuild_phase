import { Injectable } from '@angular/core';
import { initializeApp } from 'firebase/app';
import { 
  getAuth, 
  signInWithEmailAndPassword, 
  createUserWithEmailAndPassword, 
  signOut, 
  onAuthStateChanged, 
  User 
} from 'firebase/auth';
import { 
  getDatabase, 
  ref, 
  set, 
  get, 
  push, 
  update 
} from 'firebase/database';
import { BehaviorSubject } from 'rxjs';
import { environment } from '../../../environments/environment';

@Injectable({
  providedIn: 'root'
})
export class AuthService {
  private app = initializeApp(environment.firebase);
  private auth = getAuth(this.app);
  private db = getDatabase(this.app);
  
  private currentUserSubject = new BehaviorSubject<User | null>(null);
  public currentUser$ = this.currentUserSubject.asObservable();

  constructor() {
    // Listen for authentication state changes
    onAuthStateChanged(this.auth, (user) => {
      console.log('Auth state changed:', user ? `User: ${user.email}` : 'No user');
      this.currentUserSubject.next(user);
      
      // Track login date when user signs in (but don't award bonus automatically)
      if (user) {
        // Add a small delay to ensure auth is fully established
        setTimeout(() => {
          // Check if user is admin and handle appropriately
          if (this.isAdmin(user)) {
            console.log('Admin user detected, ensuring admin profile...');
            this.ensureAdminProfile(user.uid, user.email!).catch(error => {
              console.error('Error ensuring admin profile:', error);
              // Don't re-throw error to prevent logout
            });
          } else {
            console.log('Regular user detected, tracking login date...');
            this.trackLoginDate(user.uid).catch(error => {
              console.error('Error tracking login date:', error);
              // Don't re-throw error to prevent logout
            });
          }
        }, 500);
      }
    });
  }

  // Sign up with email and password
  async signUp(email: string, password: string, displayName?: string) {
    try {
      const result = await createUserWithEmailAndPassword(this.auth, email, password);
      
      // Create user profile in database
      if (result.user) {
        const today = new Date().toISOString().split('T')[0];
        await this.createUserProfile(result.user.uid, {
          email: email,
          displayName: displayName || email.split('@')[0],
          totalScore: 0,
          gamesPlayed: 0,
          createdAt: new Date().toISOString(),
          lastLoginDate: today,
          lastDailyBonusDate: '', // Initialize as empty to prevent automatic claiming
          loginStreak: 1,
          dailyTransliterations: 0,
          weeklyTransliterations: 0,
          lastTransliterationDate: '',
          lastTransliterationWeek: ''
        });
      }
      
      return result;
    } catch (error) {
      throw error;
    }
  }

  // Sign in with email and password
  async signIn(email: string, password: string) {
    try {
      // Regular user login through Firebase
      const result = await signInWithEmailAndPassword(this.auth, email, password);
      
      // Check if this user is an admin
      let isAdmin = false;
      if (result.user && email === 'admin@gmail.com') {
        isAdmin = true;
      }
      
      // Ensure user profile exists for non-admin users
      if (result.user && !isAdmin) {
        const profile = await this.getUserProfile(result.user.uid);
        if (!profile) {
          const today = new Date().toISOString().split('T')[0];
          await this.createUserProfile(result.user.uid, {
            email: email,
            displayName: result.user.displayName || email.split('@')[0],
            totalScore: 0,
            gamesPlayed: 0,
            createdAt: new Date().toISOString(),
            lastLoginDate: today,
            lastDailyBonusDate: '',
            loginStreak: 1,
            dailyTransliterations: 0,
            weeklyTransliterations: 0,
            lastTransliterationDate: '',
            lastTransliterationWeek: ''
          });
        }
      }
      
      return result;
    } catch (error) {
      throw error;
    }
  }

  // Sign out
  async signOut() {
    try {
      await signOut(this.auth);
    } catch (error) {
      throw error;
    }
  }

  // Get current user
  getCurrentUser(): User | null {
    return this.auth.currentUser;
  }

  // Create user profile in database
  private async createUserProfile(uid: string, userData: any) {
    const userRef = ref(this.db, `users/${uid}`);
    await set(userRef, userData);
  }

  // Update or create user profile in database
  async updateUserProfile(uid: string, userData: any) {
    const userRef = ref(this.db, `users/${uid}`);
    await set(userRef, userData);
  }

  // Get user profile from database
  async getUserProfile(uid: string) {
    const userRef = ref(this.db, `users/${uid}`);
    const snapshot = await get(userRef);
    return snapshot.exists() ? snapshot.val() : null;
  }

  // Update user score
  async updateUserScore(uid: string, newScore: number) {
    const userRef = ref(this.db, `users/${uid}`);
    const userSnapshot = await get(userRef);
    
    if (userSnapshot.exists()) {
      const userData = userSnapshot.val();
      const updatedData = {
        totalScore: (userData.totalScore || 0) + newScore,
        gamesPlayed: (userData.gamesPlayed || 0) + 1,
        lastPlayed: new Date().toISOString()
      };
      
      await update(userRef, updatedData);
      return updatedData;
    }
    
    throw new Error('User profile not found');
  }

  // Track transliteration usage for quest progress
  async trackTransliterationUsage(uid: string) {
    const userRef = ref(this.db, `users/${uid}`);
    const userSnapshot = await get(userRef);
    
    if (userSnapshot.exists()) {
      const userData = userSnapshot.val();
      const today = new Date().toISOString().split('T')[0]; // YYYY-MM-DD format
      const currentWeek = this.getWeekKey(new Date());
      
      // Initialize tracking fields if they don't exist
      const updatedData: any = {
        lastTransliterationDate: today,
        lastTransliterationWeek: currentWeek
      };

      // Update daily transliterations (reset if new day)
      if (userData.lastTransliterationDate !== today) {
        updatedData.dailyTransliterations = 1;
      } else {
        updatedData.dailyTransliterations = (userData.dailyTransliterations || 0) + 1;
      }

      // Update weekly transliterations (reset if new week)
      if (userData.lastTransliterationWeek !== currentWeek) {
        updatedData.weeklyTransliterations = 1;
      } else {
        updatedData.weeklyTransliterations = (userData.weeklyTransliterations || 0) + 1;
      }
      
      await update(userRef, updatedData);
      return updatedData;
    }
    
    throw new Error('User profile not found');
  }

  // Helper method to get week key (year-week format)
  private getWeekKey(date: Date): string {
    const year = date.getFullYear();
    const week = this.getWeekNumber(date);
    return `${year}-W${week.toString().padStart(2, '0')}`;
  }

  // Helper method to get week number
  private getWeekNumber(date: Date): number {
    const firstDayOfYear = new Date(date.getFullYear(), 0, 1);
    const pastDaysOfYear = (date.getTime() - firstDayOfYear.getTime()) / 86400000;
    return Math.ceil((pastDaysOfYear + firstDayOfYear.getDay() + 1) / 7);
  }

  // Track quest claims to prevent duplicate rewards
  async claimQuest(uid: string, questId: string, isWeekly: boolean = false): Promise<boolean> {
    const userRef = ref(this.db, `users/${uid}`);
    const userSnapshot = await get(userRef);
    
    if (userSnapshot.exists()) {
      const userData = userSnapshot.val();
      const today = new Date().toISOString().split('T')[0];
      const currentWeek = this.getWeekKey(new Date());
      
      if (isWeekly) {
        // Check weekly quest claims
        const weeklyClaimsKey = `weeklyQuestClaims_${currentWeek}`;
        const weeklyClaims = userData[weeklyClaimsKey] || [];
        
        if (weeklyClaims.includes(questId)) {
          return false; // Already claimed this week
        }
        
        // Add to weekly claims
        const updatedWeeklyClaims = [...weeklyClaims, questId];
        await update(userRef, {
          [weeklyClaimsKey]: updatedWeeklyClaims
        });
        
      } else {
        // Check daily quest claims
        const dailyClaimsKey = `dailyQuestClaims_${today}`;
        const dailyClaims = userData[dailyClaimsKey] || [];
        
        if (dailyClaims.includes(questId)) {
          return false; // Already claimed today
        }
        
        // Add to daily claims
        const updatedDailyClaims = [...dailyClaims, questId];
        await update(userRef, {
          [dailyClaimsKey]: updatedDailyClaims
        });
      }
      
      return true; // Successfully claimed
    }
    
    throw new Error('User profile not found');
  }

  // Check if quest is already claimed
  async isQuestClaimed(uid: string, questId: string, isWeekly: boolean = false): Promise<boolean> {
    const userRef = ref(this.db, `users/${uid}`);
    const userSnapshot = await get(userRef);
    
    if (userSnapshot.exists()) {
      const userData = userSnapshot.val();
      const today = new Date().toISOString().split('T')[0];
      const currentWeek = this.getWeekKey(new Date());
      
      if (isWeekly) {
        const weeklyClaimsKey = `weeklyQuestClaims_${currentWeek}`;
        const weeklyClaims = userData[weeklyClaimsKey] || [];
        return weeklyClaims.includes(questId);
      } else {
        const dailyClaimsKey = `dailyQuestClaims_${today}`;
        const dailyClaims = userData[dailyClaimsKey] || [];
        return dailyClaims.includes(questId);
      }
    }
    
    return false;
  }

  // Get leaderboard data
  async getLeaderboard() {
    try {
      console.log('Attempting to load leaderboard...');
      const usersRef = ref(this.db, 'users');
      const snapshot = await get(usersRef);
      
      if (snapshot.exists()) {
        const users = snapshot.val();
        console.log('Raw users data from Firebase:', users);
        
        const leaderboard = Object.keys(users).map(uid => ({
          uid,
          ...users[uid]
        })).sort((a, b) => (b.totalScore || 0) - (a.totalScore || 0));
        
        console.log('Processed leaderboard:', leaderboard);
        return leaderboard;
      } else {
        console.log('No users data found in Firebase');
        return [];
      }
    } catch (error: any) {
      console.error('Firebase leaderboard access error:', error);
      
      // For development: return mock data or current user only
      const currentUser = this.getCurrentUser();
      if (currentUser) {
        try {
          console.log('Attempting fallback: loading current user profile only');
          const userProfile = await this.getUserProfile(currentUser.uid);
          const fallbackData = userProfile ? [{ uid: currentUser.uid, ...userProfile }] : [];
          console.log('Fallback leaderboard data:', fallbackData);
          return fallbackData;
        } catch (profileError) {
          console.error('Error fetching user profile for leaderboard:', profileError);
          return [];
        }
      }
      
      throw error; // Re-throw if we can't provide fallback data
    }
  }

  // Check if user is authenticated
  isAuthenticated(): boolean {
    return this.auth.currentUser !== null;
  }

  // Check if user is admin
  isAdmin(user: any): boolean {
    const result = user && (user.email === 'admin@gmail.com' || user.isAdmin === true);
    console.log('isAdmin check:', user?.email, '→', result);
    return result;
  }

  // Enhanced logout to handle admin session
  async logout() {
    try {
      // Check if current user is admin
      const currentUser = this.currentUserSubject.value;
      const isAdminUser = this.isAdmin(currentUser);
      
      // Sign out from Firebase
      await signOut(this.auth);
      this.currentUserSubject.next(null);
      
      // Return admin status to help with routing
      return { wasAdmin: isAdminUser };
    } catch (error) {
      console.error('Logout error:', error);
      throw error;
    }
  }

  // Check and restore admin session on app startup (no longer needed)
  checkAdminSession() {
    // This method is no longer needed since we use real Firebase auth
    // Admin sessions are handled by Firebase automatically
  }

  // Check and award daily login bonus
  async checkDailyLoginBonus(uid: string): Promise<boolean> {
    const userRef = ref(this.db, `users/${uid}`);
    const userSnapshot = await get(userRef);
    
    if (userSnapshot.exists()) {
      const userData = userSnapshot.val();
      const today = new Date().toISOString().split('T')[0];
      const lastDailyBonusDate = userData.lastDailyBonusDate;
      const lastLoginDate = userData.lastLoginDate;
      
      // Check if user logged in today AND hasn't claimed bonus today
      if (lastLoginDate === today && lastDailyBonusDate !== today) {
        // Award daily bonus
        const dailyBonus = 2;
        
        const updatedData = {
          totalScore: (userData.totalScore || 0) + dailyBonus,
          lastDailyBonusDate: today // Only update bonus date, not login date
        };
        
        await update(userRef, updatedData);
        return true; // Daily bonus awarded
      }
    }
    
    return false; // No bonus (not logged in today or already claimed)
  }

  // Track user login date without awarding bonus
  async trackLoginDate(uid: string): Promise<void> {
    const userRef = ref(this.db, `users/${uid}`);
    const userSnapshot = await get(userRef);
    
    if (userSnapshot.exists()) {
      const userData = userSnapshot.val();
      const today = new Date().toISOString().split('T')[0];
      const lastLoginDate = userData.lastLoginDate;
      
      // Skip if this is a new account (created today) or already logged in today
      const createdToday = userData.createdAt && 
        userData.createdAt.split('T')[0] === today;
      
      if (!createdToday && lastLoginDate !== today) {
        const yesterday = new Date();
        yesterday.setDate(yesterday.getDate() - 1);
        const yesterdayStr = yesterday.toISOString().split('T')[0];
        
        const updatedData = {
          lastLoginDate: today,
          loginStreak: lastLoginDate === yesterdayStr 
            ? (userData.loginStreak || 0) + 1 : 1 // Increment streak or reset to 1
        };
        
        await update(userRef, updatedData);
      }
    }
  }

  // Ensure admin profile exists in database (separate from users)
  async ensureAdminProfile(uid: string, email: string) {
    try {
      console.log('Ensuring admin profile for:', email);
      const adminRef = ref(this.db, `admins/${uid}`);
      
      // Try to get existing profile first
      const existingProfile = await get(adminRef);
      
      if (!existingProfile.exists()) {
        console.log('Creating new admin profile...');
        // Create admin profile in separate admins path
        const adminProfile = {
          email: email,
          displayName: 'Admin',
          isAdmin: true,
          createdAt: new Date().toISOString(),
          lastLoginDate: new Date().toISOString().split('T')[0]
        };
        
        await set(adminRef, adminProfile);
        console.log('Admin profile created successfully in admins path');
      } else {
        console.log('Admin profile exists, updating last login...');
        // Update last login date for existing admin
        const today = new Date().toISOString().split('T')[0];
        const adminData = existingProfile.val();
        
        if (adminData.lastLoginDate !== today) {
          await update(adminRef, {
            lastLoginDate: today
          });
          console.log('Admin last login date updated');
        }
      }
    } catch (error) {
      console.error('Error ensuring admin profile:', error);
      console.log('This error will not prevent login to avoid logout issues');
      // Don't throw error as this shouldn't prevent login
      // The admin can still function without the database profile
    }
  }

  // Get admin profile (separate from getUserProfile)
  async getAdminProfile(uid: string) {
    const adminRef = ref(this.db, `admins/${uid}`);
    const snapshot = await get(adminRef);
    return snapshot.exists() ? snapshot.val() : null;
  }
}
