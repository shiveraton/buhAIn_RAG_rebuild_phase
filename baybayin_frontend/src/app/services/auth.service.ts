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
import { environment } from '../../environments/environment';

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
      this.currentUserSubject.next(user);
    });
  }

  // Sign up with email and password
  async signUp(email: string, password: string, displayName?: string) {
    try {
      const result = await createUserWithEmailAndPassword(this.auth, email, password);
      
      // Create user profile in database
      if (result.user) {
        await this.createUserProfile(result.user.uid, {
          email: email,
          displayName: displayName || email.split('@')[0],
          totalScore: 0,
          gamesPlayed: 0,
          createdAt: new Date().toISOString()
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
      return await signInWithEmailAndPassword(this.auth, email, password);
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

  // Check and award daily login bonus
  async checkDailyLoginBonus(uid: string): Promise<boolean> {
    const userRef = ref(this.db, `users/${uid}`);
    const userSnapshot = await get(userRef);
    
    if (userSnapshot.exists()) {
      const userData = userSnapshot.val();
      const today = new Date().toISOString().split('T')[0]; // YYYY-MM-DD format for better consistency
      const lastLoginDate = userData.lastLoginDate;
      
      // Check if user already logged in today
      if (lastLoginDate !== today) {
        // Award daily bonus
        const dailyBonus = 2;
        const yesterday = new Date();
        yesterday.setDate(yesterday.getDate() - 1);
        const yesterdayStr = yesterday.toISOString().split('T')[0];
        
        const updatedData = {
          totalScore: (userData.totalScore || 0) + dailyBonus,
          lastLoginDate: today,
          loginStreak: lastLoginDate === yesterdayStr 
            ? (userData.loginStreak || 0) + 1 : 1 // Increment streak or reset to 1
        };
        
        await update(userRef, updatedData);
        return true; // Daily bonus awarded
      }
    }
    
    return false; // No bonus (already logged in today)
  }
}
