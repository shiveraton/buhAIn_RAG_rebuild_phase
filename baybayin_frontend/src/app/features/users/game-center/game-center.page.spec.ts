import { ComponentFixture, TestBed } from '@angular/core/testing';
import { GameCenterPage } from './game-center.page';

describe('GameCenterPage', () => {
  let component: GameCenterPage;
  let fixture: ComponentFixture<GameCenterPage>;

  beforeEach(() => {
    fixture = TestBed.createComponent(GameCenterPage);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
