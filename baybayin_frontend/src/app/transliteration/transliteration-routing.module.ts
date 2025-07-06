import { NgModule } from '@angular/core';
import { RouterModule, Routes } from '@angular/router';
import { TransliterationPage } from './transliteration.page';

const routes: Routes = [
  {
    path: '',
    component: TransliterationPage,
  }
];

@NgModule({
  imports: [RouterModule.forChild(routes)],
  exports: [RouterModule]
})
export class TransliterationPageRoutingModule {}
