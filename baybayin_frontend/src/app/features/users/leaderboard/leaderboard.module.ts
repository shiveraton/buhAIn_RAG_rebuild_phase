import { IonicModule } from '@ionic/angular';
import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { LeaderboardPage } from './leaderboard.page';
import { LeaderboardPageRoutingModule } from './leaderboard-routing.module';

@NgModule({
  imports: [
    IonicModule,
    CommonModule,
    FormsModule,
    LeaderboardPageRoutingModule
  ],
  declarations: [LeaderboardPage]
})
export class LeaderboardPageModule {}
