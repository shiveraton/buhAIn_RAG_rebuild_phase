import { Component, OnInit, OnDestroy } from '@angular/core';
import { Camera, CameraResultType, CameraSource } from '@capacitor/camera';
import { Router, ActivatedRoute } from '@angular/router';
import { ToastController } from '@ionic/angular';

import { TransliterationService } from '../../../core/services/transliteration/transliteration.service';
import { ScoreService } from '../../../core/services/score.service';
import { AuthService } from '../../../core/services/auth.service';
import { QuestUpdateService } from '../../../core/services/quest-update.service';
import { ThemeService } from '../../../core/services/theme.service';
import { Subscription } from 'rxjs';

@Component({
  selector: 'app-transliteration',
  templateUrl: 'transliteration.page.html',
  styleUrls: ['transliteration.page.scss'],
  standalone: false,
})
export class TransliterationPage implements OnInit, OnDestroy {
  // Track which ambiguous syllables have been confirmed
  confirmedAmbiguous: boolean[] = [];

  // Helper to get the display output for ambiguous syllables
  getAmbiguousDisplay(): string {
    return this.ambiguousSyllables
      .map((s, i) => {
        if (s.options.length > 1 && !this.confirmedAmbiguous[i]) {
          return '';
        }
        return s.selected;
      })
      .join('');
  }

  // Called when user clicks a vowel button to confirm
  confirmAmbiguous(i: number, opt: string) {
    const s = this.ambiguousSyllables[i];
    // If this syllable has a consonant base, store full syllable (base + vowel)
    s.selected = s.base && s.base.length > 0 ? s.base + opt : opt;
    this.confirmedAmbiguous[i] = true;
    // Don't show any output in real-time, wait for transliterate button
    this.result = '';
  }
  // Getter for template: checks if any ambiguous syllables exist
  get hasAmbiguousSyllables(): boolean {
    return this.ambiguousSyllables.some(s => s.options.length > 1);
  }
  // Returns the resolved Latin output based on user choices
  getAmbiguousResult(): string {
    return this.ambiguousSyllables.map(s => s.selected).join('');
  }

  // Updates the result when user changes a vowel selection
  updateAmbiguousResult() {
    this.result = this.getAmbiguousResult();
  }
  // Stores syllables and ambiguity for Baybayin-to-Latin UI prompt
  ambiguousSyllables: Array<{
    latin: string;
    options: string[];
    selected: string;
    base?: string; // consonant base (e.g., 'k') or empty for standalone vowels
  }> = [];

  // Unified character array for new keyboard UI
  baybayinCharacters = [
    { baybayin: 'ᜀ', latin: 'a', type: 'vowel' },
    { baybayin: 'ᜁ', latin: 'i/e', type: 'vowel' },
    { baybayin: 'ᜂ', latin: 'u/o', type: 'vowel' },
    { baybayin: 'ᜃ', latin: 'ka', type: 'consonant' },
    { baybayin: 'ᜄ', latin: 'ga', type: 'consonant' },
    { baybayin: 'ᜅ', latin: 'nga', type: 'consonant' },
    { baybayin: 'ᜆ', latin: 'ta', type: 'consonant' },
    { baybayin: 'ᜇ', latin: 'da', type: 'consonant' },
    { baybayin: 'ᜈ', latin: 'na', type: 'consonant' },
    { baybayin: 'ᜉ', latin: 'pa', type: 'consonant' },
    { baybayin: 'ᜊ', latin: 'ba', type: 'consonant' },
    { baybayin: 'ᜋ', latin: 'ma', type: 'consonant' },
    { baybayin: 'ᜌ', latin: 'ya', type: 'consonant' },
    { baybayin: 'ᜍ', latin: 'ra', type: 'consonant' },
    { baybayin: 'ᜎ', latin: 'la', type: 'consonant' },
    { baybayin: 'ᜏ', latin: 'wa', type: 'consonant' },
    { baybayin: 'ᜐ', latin: 'sa', type: 'consonant' },
    { baybayin: 'ᜑ', latin: 'ha', type: 'consonant' },
    { baybayin: 'ᜓ', latin: 'kudlit (u/o)', type: 'special' },
    { baybayin: 'ᜒ', latin: 'kudlit (i/e)', type: 'special' },
    { baybayin: '᜔', latin: 'virama', type: 'special' }
  ];
  deleteCharacter() {
    // Remove last character from inputText
    if (this.inputText.length > 0) {
      this.inputText = this.inputText.slice(0, -1);
      // Trigger input change to update syllables and reset confirmed state
      this.onInputChange();
    }
  }
  transliterationDirection: 'latin-to-baybayin' | 'baybayin-to-latin' = 'latin-to-baybayin';
  isLatinToBaybayin: boolean = true;
  inputMethod: 'text' | 'camera' | 'upload' = 'text';
  inputText = '';
  result: string | null = null;
  cameraImage: string | null = null;
  uploadedImageSrc: string | null = null;
  expectedText: string = '';
  currentUser: any = null;
  currentTheme = 'light';
  isDarkTheme: boolean = false;
  showTextInput: boolean = false;
  showUploadPreview: boolean = false;
  // UI toggle: request cross-language EN->TL->Baybayin pipeline
  transliterateFromEnglish: boolean = false;
  private authSubscription?: Subscription;
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

  // New fields to hold spell-check results from backend
  spellCheckedText: string | null = null;
  spellingMetadata: any = null;
  
  // Admin mode detection
  isAdminMode: boolean = false;

  constructor(
    private transliterateService: TransliterationService,
    private scoreService: ScoreService,
    private authService: AuthService,
    private router: Router,
    private route: ActivatedRoute,
    private toastController: ToastController,
    private questUpdateService: QuestUpdateService,
    private themeService: ThemeService
  ) {}

  ngOnInit() {
    // Check for admin mode from query parameters
    this.route.queryParams.subscribe(params => {
      this.isAdminMode = params['adminMode'] === 'true';
    });

    // Subscribe to authentication state changes
    this.authSubscription = this.authService.currentUser$.subscribe((user) => {
      this.currentUser = user;
    });

    // Subscribe to theme changes
    this.themeSubscription = this.themeService.theme$.subscribe(theme => {
      this.currentTheme = theme;
      this.isDarkTheme = theme === 'dark';
    });

    // Initialize theme
    this.currentTheme = this.themeService.getCurrentTheme();
    this.isDarkTheme = this.themeService.isDarkMode();
  }

  ngOnDestroy() {
    if (this.authSubscription) {
      this.authSubscription.unsubscribe();
    }
    if (this.themeSubscription) {
      this.themeSubscription.unsubscribe();
    }
  }

  async toggleTheme() {
    await this.themeService.toggleTheme();
  }

  backToDashboard() {
    // Navigate back to admin dashboard
    this.router.navigate(['/dashboard']);
  }

  setInputMethod(method: 'text' | 'camera' | 'upload') {
    this.inputMethod = method;
    // Optionally clear input/result when switching
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

  onInputChange() {
    // Real-time update for baybayin-to-latin mode
    // All transliteration is now handled by the backend; no local processing here
    this.result = null;
  }

  async onCamera() {
    // Clear other inputs when using camera
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
      
      // Remove automatic point awarding - link to quest instead
      if (this.result && this.result !== 'Camera cancelled or failed.') {
        // No automatic points - camera usage doesn't count for text quest
      }
    } catch (err) {
      this.result = 'Camera cancelled or failed.';
    }
  }

  handleCamera(event: any) {
    // (Not used with Capacitor Camera)
  }

  onUpload() {
    // Clear other inputs when using upload
    this.clearAllInputs();
    
    // Trigger upload input
    const uploadInput = document.querySelector<HTMLInputElement>('#uploadInput');
    uploadInput?.click();
  }

  async handleUpload(event: any) {
    const file = event.target.files[0];
    if (file) {
      // Create preview of uploaded image
      const reader = new FileReader();
      reader.onload = (e: any) => {
        this.uploadedImageSrc = e.target.result;
        this.showUploadPreview = true;
      };
      reader.readAsDataURL(file);
    }
    
    // Send uploaded image to backend for transliteration
    // Placeholder: show result
    this.result = 'Uploaded image sent to James and Jhed.';
    
    // Remove automatic points for upload - only text feature counts for quest
    // Upload usage doesn't count for text quest
  }

  onText() {
    // Clear other inputs when using text
    this.clearAllInputs();
    this.showTextInput = !this.showTextInput;
  }

  clearAllInputs() {
    // Clear all input states
    this.showTextInput = false;
    this.showUploadPreview = false;
    this.cameraImage = null;
    this.uploadedImageSrc = null;
    this.inputText = '';
    this.result = null;
  }

  addCharacter(character: string) {
    // Add the selected Baybayin character to the input text
    this.inputText += character;
    // All transliteration is now handled by the backend; no local processing here
    this.result = '';
  }

  clearText() {
    // Clear the input text
    this.inputText = '';
  }

  async submitText() {
    if (!this.inputText) {
      this.result = 'Please enter some text.';
      return;
    }

    // reset spell-check UI state before each request
    this.spellCheckedText = null;
    this.spellingMetadata = null;

    if (this.transliterateService && this.transliterateService.transliterateText) {
      const direction = this.transliterationDirection === 'latin-to-baybayin'
        ? (this.transliterateFromEnglish ? 'cross_en_to_baybayin' : 'to_baybayin')
        : 'to_latin';
      const source_lang = this.transliterateFromEnglish ? 'en' : undefined;
      this.transliterateService.transliterateText(this.inputText, direction, source_lang).subscribe({
        next: async (response) => {
          // reset any previous UI hints
          this.spellCheckedText = null;
          this.spellingMetadata = null;

          if (response) {
            // Capture spell-check fields when present (both cross and standard flows)
            if ((response as any).spell_checked_text) {
              this.spellCheckedText = (response as any).spell_checked_text;
            }
            if ((response as any).spelling_metadata) {
              this.spellingMetadata = (response as any).spelling_metadata;
            }

            if (response.baybayin_text) {
              this.result = response.baybayin_text;
              this.expectedText = this.spellCheckedText || response.translated_text || response.normalized_text || '';
            } else if (response.transliterated_text) {
              this.result = response.transliterated_text;
              this.expectedText = this.spellCheckedText || response.normalized_text || '';
            } else {
              this.result = 'No transliteration result from backend.';
            }
          } else {
            this.result = 'No transliteration result from backend.';
          }
          // Track transliteration usage for quests (only for authenticated users)
          if (this.result && this.currentUser) {
            try {
              await this.authService.trackTransliterationUsage(this.currentUser.uid);
              this.questUpdateService.notifyQuestUpdate('transliterate_3');
              this.showQuestProgressToast();
            } catch (error) {
              console.error('Error tracking transliteration:', error);
              this.showSuccessToast();
            }
          } else if (this.result) {
            this.showSuccessToast();
          }
        },
        error: (err) => {
          this.result = 'Transliteration failed. Please try again.';
          this.showSuccessToast();
        }
      });
    } else {
      this.result = 'Transliteration service unavailable.';
      this.showSuccessToast();
    }
  }


  switchDirection() {
    // Deprecated: replaced by onToggleDirection
    this.transliterationDirection =
      this.transliterationDirection === 'latin-to-baybayin'
        ? 'baybayin-to-latin'
        : 'latin-to-baybayin';
    this.inputText = '';
    this.result = null;
  }

  onToggleDirection() {
    this.transliterationDirection = this.isLatinToBaybayin ? 'latin-to-baybayin' : 'baybayin-to-latin';
    this.inputText = '';
    this.result = null;
  }

  private async showQuestProgressToast() {
    const toast = await this.toastController.create({
      message: 'Text transliteration completed! Quest progress updated.',
      duration: 3000,
      color: 'success',
      position: 'bottom',
      buttons: [
        {
          text: 'View Quests',
          handler: () => {
            this.router.navigate(['/tabs/quests']);
          }
        }
      ]
    });
    toast.present();
  }

  private async showSuccessToast() {
    const toast = await this.toastController.create({
      message: 'Text transliteration completed successfully!',
      duration: 2000,
      color: 'success',
      position: 'bottom'
    });
    toast.present();
  }

  // Helper to display suggestion list from spelling metadata
  getSpellingSuggestions(): string[] {
    if (!this.spellingMetadata) return [];
    // If phrase-level suggestions exist, prefer those
    if (Array.isArray(this.spellingMetadata.suggestions) && this.spellingMetadata.suggestions.length > 0) {
      return this.spellingMetadata.suggestions;
    }
    // Fall back to per-word top suggestions concatenated into phrases
    if (Array.isArray(this.spellingMetadata.results)) {
      const parts = this.spellingMetadata.results.map((r: any) => {
        if (r.correct) return r.word;
        if (r.suggestions && r.suggestions.length > 0) return r.suggestions[0];
        return r.word;
      });
      return [parts.join(' ')];
    }
    return [];
  }

  // Check if there are spelling errors to show
  hasSpellingErrors(): boolean {
    return this.spellingMetadata && !this.spellingMetadata.is_correct;
  }

  // Render the original text with error highlighting
  renderTextWithErrors(): string {
    if (!this.spellingMetadata || !this.spellingMetadata.results) {
      return this.inputText;
    }

    let result = '';
    for (const wordResult of this.spellingMetadata.results) {
      if (!wordResult.correct) {
        result += `<span class="spelling-error">${wordResult.word}</span> `;
      } else {
        result += `${wordResult.word} `;
      }
    }
    return result.trim();
  }

  // Apply a suggestion to the input field
  applySuggestion(suggestion: string) {
    this.inputText = suggestion;
    // Clear spell-check metadata since we've applied the suggestion
    this.spellingMetadata = null;
    this.spellCheckedText = null;
    // Re-trigger transliteration with the corrected input
    this.submitText();
  }
}
