import { ComponentFixture, TestBed } from '@angular/core/testing';
import { TransliterationPage } from './transliteration.page';

describe('TransliterationPage', () => {
  let component: TransliterationPage;
  let fixture: ComponentFixture<TransliterationPage>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      declarations: [TransliterationPage]
    }).compileComponents();

    fixture = TestBed.createComponent(TransliterationPage);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
