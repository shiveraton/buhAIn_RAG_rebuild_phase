import { ComponentFixture, TestBed } from '@angular/core/testing';
import { TabsUserPage } from './tabs-user.page';

describe('TabsUserPage', () => {
  let component: TabsUserPage;
  let fixture: ComponentFixture<TabsUserPage>;

  beforeEach(() => {
    fixture = TestBed.createComponent(TabsUserPage);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
