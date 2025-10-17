import { NgModule } from '@angular/core';
import { Routes, RouterModule } from '@angular/router';
import { TabsPage } from './tabs.page';
<<<<<<< HEAD
import { UserGuard } from '../core/guards/user.guard';
import { AdminGuard } from '../core/guards/admin.guard';
=======
>>>>>>> main

const routes: Routes = [
  {
    path: '',
    component: TabsPage,
    children: [
<<<<<<< HEAD
      // Admin Routes
      {
        path: 'analytics',
        loadChildren: () => import('../features/admin/analytics/analytics.module').then(m => m.AnalyticsPageModule),
        canActivate: [AdminGuard]
      },
      {
        path: 'dashboard',
        loadChildren: () => import('../features/admin/dashboard/dashboard.module').then(m => m.DashboardPageModule),
        canActivate: [AdminGuard]
      },
      
      // User Routes
      {
        path: 'transliteration',
        loadChildren: () => import('../features/users/transliteration/transliteration.module').then(m => m.TransliterationPageModule)
        // Removed canActivate guard to allow both admin and user access
      },
      {
        path: 'leaderboard',
        loadChildren: () => import('../features/users/leaderboard/leaderboard.module').then(m => m.LeaderboardPageModule),
        canActivate: [UserGuard]
      },
      {
        path: 'baybayin-info',
        loadChildren: () => import('../features/users/baybayin-info/baybayin-info.module').then(m => m.BaybayinInfoPageModule),
        canActivate: [UserGuard]
      },
      {
        path: 'quests',
        loadChildren: () => import('../features/users/quests/quests.module').then(m => m.QuestsPageModule),
        canActivate: [UserGuard]
      },
      {
        path: 'game-center',
        loadChildren: () => import('../features/users/game-center/game-center.module').then(m => m.GameCenterPageModule)
      },
      {
        path: 'profile',
        loadChildren: () => import('../features/users/profile/profile.module').then(m => m.ProfilePageModule),
        canActivate: [UserGuard]
=======
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
>>>>>>> main
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
