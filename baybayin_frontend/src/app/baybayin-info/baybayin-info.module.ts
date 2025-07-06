import { IonicModule } from '@ionic/angular';
import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { BaybayinInfoPage } from './baybayin-info.page';
import { ExploreContainerComponentModule } from '../explore-container/explore-container.module';
import { BaybayinInfoPageRoutingModule } from './baybayin-info-routing.module';

@NgModule({
  imports: [
    IonicModule,
    CommonModule,
    FormsModule,
    ExploreContainerComponentModule,
    BaybayinInfoPageRoutingModule
  ],
  declarations: [BaybayinInfoPage]
})
export class BaybayinInfoPageModule {}
