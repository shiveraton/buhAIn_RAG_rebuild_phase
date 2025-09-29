import { IonicModule } from '@ionic/angular';
import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { TransliterationPage } from './transliteration.page';
import { TransliterationPageRoutingModule } from './transliteration-routing.module';

@NgModule({
  imports: [
    IonicModule,
    CommonModule,
    FormsModule,
    TransliterationPageRoutingModule
  ],
  declarations: [
    TransliterationPage
  ]
})
export class TransliterationPageModule {}
