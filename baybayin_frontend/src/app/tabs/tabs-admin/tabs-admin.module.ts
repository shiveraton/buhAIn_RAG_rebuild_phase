import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';

import { IonicModule } from '@ionic/angular';

import { TabsAdminPageRoutingModule } from './tabs-admin-routing.module';

import { TabsAdminPage } from './tabs-admin.page';
import { AdminSideBarComponent } from 'src/app/components/admin/admin-side-bar/admin-side-bar.component';
@NgModule({
  imports: [
    CommonModule,
    FormsModule,
    IonicModule,
    TabsAdminPageRoutingModule
  ],
  declarations: [TabsAdminPage, AdminSideBarComponent]
})
export class TabsAdminPageModule {}
