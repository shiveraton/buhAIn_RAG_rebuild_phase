import { NgModule } from '@angular/core';
import { Routes, RouterModule } from '@angular/router';

import { ImageTransSystemPage } from './image-trans-system.page';

const routes: Routes = [
  {
    path: '',
    component: ImageTransSystemPage
  }
];

@NgModule({
  imports: [RouterModule.forChild(routes)],
  exports: [RouterModule],
})
export class ImageTransSystemPageRoutingModule {}
