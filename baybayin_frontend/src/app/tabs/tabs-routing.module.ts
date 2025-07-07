import { NgModule } from '@angular/core';
import { Routes, RouterModule } from '@angular/router';
import { TabsPage } from './tabs.page';

const routes: Routes = [
  {
    path: '',
    component: TabsPage,
    children: [
      {
        path: 'transliteration',
        loadChildren: () => import('../transliteration/transliteration.module').then(m => m.TransliterationPageModule)
      },
      {
        path: 'leaderboard',
        loadChildren: () => import('../leaderboard/leaderboard.module').then(m => m.LeaderboardPageModule)
      },
      {
        path: 'baybayin-info',
        loadChildren: () => import('../baybayin-info/baybayin-info.module').then(m => m.BaybayinInfoPageModule)
      },
      {
        path: 'quests',
        loadChildren: () => import('../quests/quests.module').then(m => m.QuestsPageModule)
      },
      {
        path: 'profile',
        loadChildren: () => import('../profile/profile.module').then(m => m.ProfilePageModule)
      },
      {
        path: '',
        redirectTo: '/tabs/transliteration',
        pathMatch: 'full'
      }
    ]
  }
];

@NgModule({
  imports: [RouterModule.forChild(routes)],
  exports: [RouterModule],
})
export class TabsPageRoutingModule {}
