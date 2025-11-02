import { NgModule } from '@angular/core';
import { PreloadAllModules, RouterModule, Routes } from '@angular/router';

const routes: Routes = [
  {
    path: '',
    redirectTo: 'login',
    pathMatch: 'full'
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
  {
    path: 'logout',
    loadChildren: () => import('./features/auth/logout/logout.module').then( m => m.LogoutPageModule)
  },
];
@NgModule({
  imports: [
    RouterModule.forRoot(routes, { preloadingStrategy: PreloadAllModules })
  ],
  exports: [RouterModule]
})
export class AppRoutingModule {}
