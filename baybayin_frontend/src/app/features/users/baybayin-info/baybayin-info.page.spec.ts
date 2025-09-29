import { ComponentFixture, TestBed } from '@angular/core/testing';
import { BaybayinInfoPage } from './baybayin-info.page';

describe('BaybayinInfoPage', () => {
  let component: BaybayinInfoPage;
  let fixture: ComponentFixture<BaybayinInfoPage>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      declarations: [BaybayinInfoPage]
    }).compileComponents();

    fixture = TestBed.createComponent(BaybayinInfoPage);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
