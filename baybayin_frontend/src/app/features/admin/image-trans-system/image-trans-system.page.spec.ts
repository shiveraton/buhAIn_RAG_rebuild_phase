import { ComponentFixture, TestBed } from '@angular/core/testing';
import { ImageTransSystemPage } from './image-trans-system.page';

describe('ImageTransSystemPage', () => {
  let component: ImageTransSystemPage;
  let fixture: ComponentFixture<ImageTransSystemPage>;

  beforeEach(() => {
    fixture = TestBed.createComponent(ImageTransSystemPage);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
