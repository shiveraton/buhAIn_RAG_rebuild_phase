import { NgModule } from '@angular/core';
import { Routes, RouterModule } from '@angular/router';

import { GameCenterPage } from './game-center.page';

const routes: Routes = [
  {
    path: '',
    component: GameCenterPage
  }
];

@NgModule({
  imports: [RouterModule.forChild(routes)],
  exports: [RouterModule],
})
export class GameCenterPageRoutingModule {}
