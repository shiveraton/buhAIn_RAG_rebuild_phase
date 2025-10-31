import { NgModule } from '@angular/core';
import { PreloadAllModules, RouterModule, Routes } from '@angular/router';
import { SplashComponent } from './splash/splash.component';
import { UserGuard } from './core/guards/user.guard';
import { AdminGuard } from './core/guards/admin.guard';

const routes: Routes = [
  {
    path: '',
    redirectTo: '/splash',
    pathMatch: 'full'
  },
  {
    path: 'splash',
    component: SplashComponent
  },
  {
    path: 'tabs',
    loadChildren: () => import('./tabs/tabs.module').then(m => m.TabsPageModule)
    // No guard here - both admin and users can access tabs (but see different content)
  },
  {
    path: 'admin',
    loadChildren: () => import('./features/admin/admin.module').then(m => m.AdminPageModule)
  },
  {
    path: 'quests',
    loadChildren: () => import('./features/users/quests/quests.module').then( m => m.QuestsPageModule),
    canActivate: [UserGuard]
  },
  {
    path: 'profile',
    loadChildren: () => import('./features/users/profile/profile.module').then( m => m.ProfilePageModule),
    canActivate: [UserGuard]
  },
  {
    path: 'signup',
    loadChildren: () => import('./features/auth/signup/signup.module').then( m => m.SignupPageModule)
  },
  {
    path: 'login',
    loadChildren: () => import('./features/auth/login/login.module').then( m => m.LoginPageModule)
  },
  {
    path: 'settings',
    loadChildren: () => import('./features/users/settings/settings.module').then( m => m.SettingsPageModule),
    canActivate: [UserGuard]
  },
  {
    path: 'game-center',
    loadChildren: () => import('./features/users/game-center/game-center.module').then( m => m.GameCenterPageModule)
  },
  {
    path: 'explore-container',
    loadChildren: () => import('./components/explore-container/explore-container.module').then( m => m.ExploreContainerComponentModule)
  },
];
@NgModule({
  imports: [
    RouterModule.forRoot(routes, { preloadingStrategy: PreloadAllModules })
  ],
  exports: [RouterModule]
})
export class AppRoutingModule {}
