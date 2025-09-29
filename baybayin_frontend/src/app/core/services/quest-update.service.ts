import { Injectable } from '@angular/core';
import { Subject } from 'rxjs';

@Injectable({
  providedIn: 'root'
})
export class QuestUpdateService {
  private questUpdateSubject = new Subject<string>();
  
  // Observable that other components can subscribe to
  questUpdate$ = this.questUpdateSubject.asObservable();

  constructor() { }

  // Emit quest update events
  notifyQuestUpdate(questType: string) {
    this.questUpdateSubject.next(questType);
  }
}
