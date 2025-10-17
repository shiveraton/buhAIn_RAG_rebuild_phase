import { IonicModule } from '@ionic/angular';
import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { TransliterationPage } from './transliteration.page';
import { ExploreContainerComponentModule } from '../explore-container/explore-container.module';
import { TransliterationPageRoutingModule } from './transliteration-routing.module';

@NgModule({
  imports: [
    IonicModule,
    CommonModule,
    FormsModule,
    ExploreContainerComponentModule,
    TransliterationPageRoutingModule
  ],
  declarations: [TransliterationPage]
})
export class TransliterationPageModule {}
