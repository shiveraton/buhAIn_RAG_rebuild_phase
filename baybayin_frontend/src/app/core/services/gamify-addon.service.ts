import { Injectable } from '@angular/core';
import { FirebaseService } from './firebase.service';
import { doc, getDoc, updateDoc, collection, query, orderBy, getDocs } from 'firebase/firestore';

@Injectable({
  providedIn: 'root'
})
export class GamifyAddonService {
  private db = this.firebaseService.db;

  constructor(private firebaseService: FirebaseService) {}

  async updateUserActivity(uid: string) {
    const userDocRef = doc(this.db, 'users', uid);
    const userSnap = await getDoc(userDocRef);
    if (!userSnap.exists()) return;

    const data = userSnap.data();
    const lastActive = new Date(data['last_active_date']);
    let currentStreak = data['current_streak'] || 0;

    const today = new Date();
    today.setHours(0, 0, 0, 0);
    const yesterday = new Date(today);
    yesterday.setDate(today.getDate() - 1);

    if (lastActive >= yesterday && lastActive < today) {
      currentStreak += 1;
    } else if (lastActive < yesterday) {
      currentStreak = 0;
    }

    await updateDoc(userDocRef, {
      last_active_date: new Date(),
      current_streak: currentStreak
    });
  }

  async getLeaderboard() {
    const leaderboardRef = collection(this.db, 'leaderboard');
    const q = query(leaderboardRef, orderBy('total_xp', 'desc'));
    const snapshot = await getDocs(q);
    return snapshot.docs.map(doc => ({ ...(doc.data() as any) }));
  }
}
