import { NgModule } from '@angular/core';
import { Routes, RouterModule } from '@angular/router';
import { TabsAdminPage } from './tabs-admin.page';
import { AdminGuard } from 'src/app/core/guards/admin.guard';
const routes: Routes = [
  {
    path: '',
    component: TabsAdminPage,
    // canActivate: [AdminGuard],
    children: [
      {
        path: '',
        redirectTo: 'dashboard',
        pathMatch: 'full',
      },
      {
        path: 'dashboard',
        loadChildren: () => import('../../features/admin/dashboard/dashboard.module').then(m => m.DashboardPageModule),
      },
      {
        path: 'image-transliteration-system',
        loadChildren: () => import('../../features/admin/image-trans-system/image-trans-system.module').then(m => m.ImageTransSystemPageModule)
      }
    ]
  }
];

@NgModule({
  imports: [RouterModule.forChild(routes)],
  exports: [RouterModule],
})
export class TabsAdminPageRoutingModule {}
