import { Component, OnInit, OnDestroy } from '@angular/core';
import { Camera, CameraResultType, CameraSource } from '@capacitor/camera';
import { Router, ActivatedRoute } from '@angular/router';
import { ToastController } from '@ionic/angular';

import { TransliterationService } from '../../../core/services/transliteration.service';
import { QuestUpdateService } from '../../../core/services/quest-update.service';
import { Subscription } from 'rxjs';

@Component({
  selector: 'app-transliteration',
  templateUrl: 'transliteration.page.html',
  styleUrls: ['transliteration.page.scss'],
  standalone: false,
})
export class TransliterationPage implements OnInit, OnDestroy {
  confirmedAmbiguous: boolean[] = [];
  previewUrl: string | ArrayBuffer | null = null;
  selectedFile!: File;
  uploadResponse: string | null = null;
  isLoading = false;
  predictedText: string = '';
  inputText = '';
  result: string | null = null;
  cameraImage: string | null = null;
  uploadedImageSrc: string | null = null;
  expectedText: string = '';
  showTextInput: boolean = false;
  showUploadPreview: boolean = false;
  transliterateFromEnglish: boolean = false;

  private themeSubscription?: Subscription;

  // Baybayin character arrays
  baybayinVowels = [
    { baybayin: 'ᜀ', latin: 'a' },
    { baybayin: 'ᜁ', latin: 'i/e' },
    { baybayin: 'ᜂ', latin: 'u/o' }
  ];

  baybayinConsonants = [
    { baybayin: 'ᜃ', latin: 'ka' },
    { baybayin: 'ᜄ', latin: 'ga' },
    { baybayin: 'ᜅ', latin: 'nga' },
    { baybayin: 'ᜆ', latin: 'ta' },
    { baybayin: 'ᜇ', latin: 'da' },
    { baybayin: 'ᜈ', latin: 'na' },
    { baybayin: 'ᜉ', latin: 'pa' },
    { baybayin: 'ᜊ', latin: 'ba' },
    { baybayin: 'ᜋ', latin: 'ma' },
    { baybayin: 'ᜌ', latin: 'ya' },
    { baybayin: 'ᜍ', latin: 'ra' },
    { baybayin: 'ᜎ', latin: 'la' },
    { baybayin: 'ᜏ', latin: 'wa' },
    { baybayin: 'ᜐ', latin: 'sa' },
    { baybayin: 'ᜑ', latin: 'ha' }
  ];

  baybayinSpecial = [
    { baybayin: 'ᜓ', latin: 'kudlit (u/o)' },
    { baybayin: 'ᜒ', latin: 'kudlit (i/e)' },
    { baybayin: '᜔', latin: 'virama' }
  ];

  spellCheckedText: string | null = null;
  spellingMetadata: any = null;
  isAdminMode: boolean = false;

  transliterationDirection: 'latin-to-baybayin' | 'baybayin-to-latin' = 'latin-to-baybayin';
  inputMethod: 'text' | 'camera' | 'upload' = 'text';

  ambiguousSyllables: Array<{
    latin: string;
    options: string[];
    selected: string;
    base?: string;
  }> = [];

  constructor(
    private transliterateService: TransliterationService,
    private router: Router,
    private route: ActivatedRoute,
  ) {}

  ngOnInit() {
    this.route.queryParams.subscribe(params => {
      this.isAdminMode = params['adminMode'] === 'true';
    });
  }

  ngOnDestroy() {
    if (this.themeSubscription) {
      this.themeSubscription.unsubscribe();
    }
  }

  backToDashboard() {
    this.router.navigate(['/dashboard']);
  }

  setInputMethod(method: 'text' | 'camera' | 'upload') {
    this.inputMethod = method;
    this.inputText = '';
    this.result = null;
    this.cameraImage = null;
    this.uploadedImageSrc = null;
  }

  swapDirection() {
    this.transliterationDirection =
      this.transliterationDirection === 'latin-to-baybayin'
        ? 'baybayin-to-latin'
        : 'latin-to-baybayin';
    this.inputText = '';
    this.result = null;
  }

  async onCamera() {
    this.clearAllInputs();
    try {
      const image = await Camera.getPhoto({
        quality: 80,
        allowEditing: false,
        resultType: CameraResultType.DataUrl,
        source: CameraSource.Camera,
      });
      this.cameraImage = image.dataUrl || null;
      this.result = 'ARA DAE.';
    } catch {
      this.result = 'Camera cancelled or failed.';
    }
  }

  onUpload() {
    this.clearAllInputs();
    const uploadInput = document.querySelector<HTMLInputElement>('#uploadInput');
    uploadInput?.click();
  }

  async handleUpload(event: any) {
    const file = event.target.files[0];
    if (file) {
      const reader = new FileReader();
      reader.onload = (e: any) => {
        this.uploadedImageSrc = e.target.result;
        this.showUploadPreview = true;
      };
      reader.readAsDataURL(file);
    }
    this.result = 'Uploaded image sent to James and Jhed.';
  }

  onText() {
    this.clearAllInputs();
    this.showTextInput = !this.showTextInput;
  }

  clearAllInputs() {
    this.showTextInput = false;
    this.showUploadPreview = false;
    this.cameraImage = null;
    this.uploadedImageSrc = null;
    this.inputText = '';
    this.result = null;
  }

  clearText() {
    this.inputText = '';
  }

  async submitText() {
    if (!this.inputText) {
      this.result = 'Please enter some text.';
      return;
    }

    this.spellCheckedText = null;
    this.spellingMetadata = null;

    if (this.transliterationDirection === 'latin-to-baybayin') {
      if (this.transliterateService && this.transliterateService.transliterateText) {
        const direction = this.transliterateFromEnglish ? 'cross_en_to_baybayin' : 'to_baybayin';
        const source_lang = this.transliterateFromEnglish ? 'en' : undefined;
        this.transliterateService.transliterateText(this.inputText, direction, source_lang).subscribe({
           next: (response) => {
             this.spellCheckedText = (response as any)?.spell_checked_text || null;
             this.spellingMetadata = (response as any)?.spelling_metadata || null;

             if (response?.baybayin_text) {
               this.result = response.baybayin_text;
               this.expectedText = this.spellCheckedText || response.translated_text || response.normalized_text || '';
             } else if (response?.transliterated_text) {
               this.result = response.transliterated_text;
               this.expectedText = this.spellCheckedText || response.normalized_text || '';
             } else {
               this.result = '';
             }
           },
           error: () => {
             this.result = '';
           }
        });
      } else {
        this.result = '';
      }
    } 
  }
}
