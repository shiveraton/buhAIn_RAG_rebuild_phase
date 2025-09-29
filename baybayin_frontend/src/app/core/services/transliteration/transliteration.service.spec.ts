import { TestBed } from '@angular/core/testing';

import { TransliterationService } from './transliteration.service';

describe('TransliterationService', () => {
  let service: TransliterationService;

  beforeEach(() => {
    TestBed.configureTestingModule({});
    service = TestBed.inject(TransliterationService);
  });

  it('should be created', () => {
    expect(service).toBeTruthy();
  });
});
