import { Injectable } from '@angular/core';
import { initializeApp, getApps, getApp } from 'firebase/app';
import { getAuth, signInWithEmailAndPassword, signOut, onAuthStateChanged, User} from 'firebase/auth';
import { environment } from 'src/environments/environment';
import { getFirestore, doc, getDoc, updateDoc } from 'firebase/firestore';
import { GamifyAddonService } from './gamify-addon.service';
import { BehaviorSubject, Observable } from 'rxjs';

@Injectable({
  providedIn: 'root'
})
export class AuthenticationService {
  private app = !getApps().length ? initializeApp(environment.firebaseConfig) : getApp();
  private auth = getAuth(this.app);
  private db = getFirestore(this.app);

  private currentUserSubject = new BehaviorSubject<User | null>(null);
  public currentUser$: Observable<User | null> = this.currentUserSubject.asObservable();

  constructor(private gamifyAddonService: GamifyAddonService) {
    // Subscribe to auth state changes
    onAuthStateChanged(this.auth, (user) => {
      this.currentUserSubject.next(user);
    });
  }

  async login(email: string, password: string) {
    try {
      const userCredentials = await signInWithEmailAndPassword(this.auth, email, password);
      const user = userCredentials.user;

      await this.gamifyAddonService.updateUserActivity(user.uid);

      this.currentUserSubject.next(user);

      return user;
    } catch (error: any) {
      console.error('login-error:', error);
      throw { code: 'login-failed', message: error.message || 'Login failed' };
    }
  }

  async logout() {
    try {
      await signOut(this.auth);
      this.currentUserSubject.next(null);
    } catch (error: any) {
      console.error('Logout error:', error);
      throw { code: 'logout-failed', message: error.message || 'Logout failed' };
    }
  }

  public async getRole(uid: string) {
    const userDocRef = doc(this.db, 'users', uid);
    const userSnap = await getDoc(userDocRef);

    if (!userSnap.exists()) return;

    const data = userSnap.data();
    return data['role'];
  }

  public getCurrentUser(): User | null {
    return this.currentUserSubject.value;
  }

  async getUserProfile(uid: string) {
    const userDocRef = doc(this.db, 'users', uid);
    const snapshot = await getDoc(userDocRef);
    return snapshot.exists() ? snapshot.data() : null;
  }

  public async setUserRole(uid: string, role: string) {
    try {
      const userDocRef = doc(this.db, 'users', uid);
      await updateDoc(userDocRef, {
        role: role
      });
      console.log(`User ${uid} role updated to ${role}`);
    } catch (error) {
      console.error('Error updating user role:', error);
      throw error;
    }
  }


}
