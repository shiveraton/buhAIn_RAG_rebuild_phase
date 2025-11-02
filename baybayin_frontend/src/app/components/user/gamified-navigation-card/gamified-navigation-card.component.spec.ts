import { ComponentFixture, TestBed, waitForAsync } from '@angular/core/testing';
import { IonicModule } from '@ionic/angular';

import { GamifiedNavigationCardComponent } from './gamified-navigation-card.component';

describe('GamifiedNavigationCardComponent', () => {
  let component: GamifiedNavigationCardComponent;
  let fixture: ComponentFixture<GamifiedNavigationCardComponent>;

  beforeEach(waitForAsync(() => {
    TestBed.configureTestingModule({
      declarations: [ GamifiedNavigationCardComponent ],
      imports: [IonicModule.forRoot()]
    }).compileComponents();

    fixture = TestBed.createComponent(GamifiedNavigationCardComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  }));

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
