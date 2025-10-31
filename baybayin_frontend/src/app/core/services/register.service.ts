import { Injectable } from '@angular/core';
import { initializeApp } from 'firebase/app';
import { getAuth, createUserWithEmailAndPassword, fetchSignInMethodsForEmail, User } from 'firebase/auth';
import { environment } from 'src/environments/environment';
import { getFirestore, doc, setDoc, collection, query, where, getDocs, writeBatch} from 'firebase/firestore'

@Injectable({
  providedIn: 'root'
})
export class RegisterService {
  private auth = getAuth()
  private db = getFirestore()

  constructor() {
    initializeApp(environment.firebaseConfig)
  }

  async register(email: string, password: string, username:string): Promise<User>{

    email = email.toLowerCase();

    try{
      const methods = await fetchSignInMethodsForEmail(this.auth, email)
      if (methods.length > 0){
        throw { code: 'email-exists', message: 'Email already in use'} 
      }
      

      if (username){
        const userRef = collection(this.db, 'users')
        const usernameQuery = query(userRef, where('username', '==', username))
        const usernameQuerySnapshot = await getDocs(usernameQuery);
        if(!usernameQuerySnapshot.empty){
          throw { code: 'username-taken', message: 'Username already taken' }
        }
      }

      const userCredentials = await createUserWithEmailAndPassword(this.auth, email, password)
      const user = userCredentials.user
      const user_leaderboard_id = `leaderboard_${user.uid}`

      const batch = writeBatch(this.db)

      batch.set(doc(this.db, 'users', user.uid), {
        email: user.email,
        username: username,
        leaderboard_id: user_leaderboard_id,
        role: "user",

        level: 0,
        current_xp: 0,
        total_xp: 0, 

        current_streak: 0,
        highest_streak: 0,
        last_active_date: new Date(),
        created_at: new Date()
      })

      batch.set(doc(this.db, 'leaderboard', user_leaderboard_id), {
        username: username, 
        user_id: user.uid,
        level: 0,
        total_xp: 0
      })

      await batch.commit()

      return user
      
    }catch(error: any){
      if (!error.code) error = {code: 'unknown', message: error.message || 'Unknown error'}
      throw error
    }
  }

}
