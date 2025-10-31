import { Injectable } from '@angular/core';
import { initializeApp, getApps, getApp, FirebaseApp } from 'firebase/app';
import { getAuth, Auth } from 'firebase/auth';
import { getFirestore, Firestore } from 'firebase/firestore';
import { environment } from 'src/environments/environment';

@Injectable({
  providedIn: 'root',
})
export class FirebaseService {
  public app: FirebaseApp;
  public auth: Auth;
  public db: Firestore;

  constructor() {
    this.app = !getApps().length ? initializeApp(environment.firebaseConfig) : getApp();
    this.auth = getAuth(this.app);
    this.db = getFirestore(this.app);
  }
}
