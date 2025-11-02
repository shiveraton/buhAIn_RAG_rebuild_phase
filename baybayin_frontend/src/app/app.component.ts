import { Component, OnInit } from '@angular/core';
import { Platform } from '@ionic/angular';

@Component({
  selector: 'app-root',
  templateUrl: 'app.component.html',
  styleUrls: ['app.component.scss'],
  standalone: false,
})
export class AppComponent implements OnInit {

  constructor(private platform: Platform) {}

  async ngOnInit() {
    try {
      await this.platform.ready();
    } catch (error) {
      console.error('Error initializing app:', error);
    }
  }
}
