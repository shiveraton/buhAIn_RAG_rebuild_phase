import { NgModule } from '@angular/core';
import { Routes, RouterModule } from '@angular/router';

import { TabsUserPage } from './tabs-user.page';
import { UserGuard } from 'src/app/core/guards/user.guard';
const routes: Routes = [
  {
    path: '',
    component: TabsUserPage,
    children: [
      {
        path: '',
        redirectTo: 'transliteration',
        pathMatch: 'full'
      },
      {
        path: 'transliteration',
        loadChildren: () => import('../../features/users/transliteration/transliteration.module').then(m => m.TransliterationPageModule),
      },
      {
        path: 'leaderboard',
        loadChildren: () => import('../../features/users/leaderboard/leaderboard.module').then(m => m.LeaderboardPageModule),
        canActivate: [UserGuard],
      },
      {
        path: 'baybayin-info',
        loadChildren: () => import('../../features/users/baybayin-info/baybayin-info.module').then(m => m.BaybayinInfoPageModule),
      },
      {
        path: 'quests',
        loadChildren: () => import('../../features/users/quests/quests.module').then(m => m.QuestsPageModule),
        canActivate: [UserGuard],
      },
      {
        path: 'game-center',
        loadChildren: () => import('../../features/users/game-center/game-center.module').then(m => m.GameCenterPageModule),
      },
      {
        path: 'profile',
        loadChildren: () => import('../../features/users/profile/profile.module').then(m => m.ProfilePageModule),
      },
    ]
  }
];

@NgModule({
  imports: [RouterModule.forChild(routes)],
  exports: [RouterModule],
})
export class TabsUserPageRoutingModule {}
