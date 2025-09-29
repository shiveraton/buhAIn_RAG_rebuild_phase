import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';

import { IonicModule } from '@ionic/angular';

import { GameCenterPageRoutingModule } from './game-center-routing.module';

import { GameCenterPage } from './game-center.page';

@NgModule({
  imports: [
    CommonModule,
    FormsModule,
    IonicModule,
    GameCenterPageRoutingModule,
    GameCenterPage
  ]
})
export class GameCenterPageModule {}
