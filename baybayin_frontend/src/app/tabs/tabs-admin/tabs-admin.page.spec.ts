import { ComponentFixture, TestBed } from '@angular/core/testing';
import { TabsAdminPage } from './tabs-admin.page';

describe('TabsAdminPage', () => {
  let component: TabsAdminPage;
  let fixture: ComponentFixture<TabsAdminPage>;

  beforeEach(() => {
    fixture = TestBed.createComponent(TabsAdminPage);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
