import { NgModule } from '@angular/core';
import { RouterModule, Routes } from '@angular/router';
import { BaybayinInfoPage } from './baybayin-info.page';

const routes: Routes = [
  {
    path: '',
    component: BaybayinInfoPage,
  }
];

@NgModule({
  imports: [RouterModule.forChild(routes)],
  exports: [RouterModule]
})
export class BaybayinInfoPageRoutingModule {}
