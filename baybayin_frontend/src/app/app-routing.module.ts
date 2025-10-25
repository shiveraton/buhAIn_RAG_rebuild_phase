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
    path: 'tabs-user',
    loadChildren: () => import('./tabs/tabs-user/tabs-user.module').then( m => m.TabsUserPageModule)
  },
  {
    path: 'tabs-admin',
    loadChildren: () => import('./tabs/tabs-admin/tabs-admin.module').then( m => m.TabsAdminPageModule)
  },
  {
    path: 'signup',
    loadChildren: () => import('./features/auth/signup/signup.module').then( m => m.SignupPageModule)
  },
  {
    path: 'login',
    loadChildren: () => import('./features/auth/login/login.module').then( m => m.LoginPageModule)
  },
];
@NgModule({
  imports: [
    RouterModule.forRoot(routes, { preloadingStrategy: PreloadAllModules })
  ],
  exports: [RouterModule]
})
export class AppRoutingModule {}
