import { Component, OnInit, OnDestroy } from '@angular/core';
import { Camera, CameraResultType, CameraSource } from '@capacitor/camera';
import { Router } from '@angular/router';
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

  /**
   * Transliterates Latin text to Baybayin, handling syllables, kudlit, and virama.
   * Example: "himas" → ᜑᜒᜋᜐ᜔
   */
  private transliterateLatinToBaybayin(text: string): string {
    // Baybayin character map
    const consonantMap: { [key: string]: string } = {
      'k': 'ᜃ', 'g': 'ᜄ', 'ng': 'ᜅ', 't': 'ᜆ', 'd': 'ᜇ', 'n': 'ᜈ',
      'p': 'ᜉ', 'b': 'ᜊ', 'm': 'ᜋ', 'y': 'ᜌ', 'r': 'ᜍ', 'l': 'ᜎ',
      'w': 'ᜏ', 's': 'ᜐ', 'h': 'ᜑ'
    };
    const vowelMap: { [key: string]: string } = {
      'a': 'ᜀ', 'i': 'ᜁ', 'e': 'ᜁ', 'o': 'ᜂ', 'u': 'ᜂ'
    };
    const kudlitI = 'ᜒ';
    const kudlitU = 'ᜓ';
    const virama = '᜔';

    // Syllable regex: (C)V(C)?
    const syllableRegex = /ng|[bcdfghklmnprstwy]?([aeiou])([bcdfghklmnprstwy]?)/gi;
    let result = '';
    let lastIndex = 0;
    let match;

    // Lowercase and remove non-letters
    text = text.toLowerCase().replace(/[^a-z]/g, '');

    while ((match = syllableRegex.exec(text)) !== null) {
      let [syllable, vowel, finalConsonant] = match;
      let start = match.index;
      // Handle initial consonant (including ng)
      let initialConsonant = '';
      if (syllable.startsWith('ng')) {
        initialConsonant = 'ng';
      } else if (consonantMap[syllable[0]]) {
        initialConsonant = syllable[0];
      }

      // Main consonant + kudlit
      if (initialConsonant) {
        result += consonantMap[initialConsonant];
        if (vowel === 'a') {
          // No kudlit for 'a'
        } else if (vowel === 'i' || vowel === 'e') {
          result += kudlitI;
        } else if (vowel === 'o' || vowel === 'u') {
          result += kudlitU;
        }
      } else {
        // Standalone vowel
        result += vowelMap[vowel];
      }

      // Final consonant (closed syllable, add virama)
      if (finalConsonant && consonantMap[finalConsonant]) {
        result += consonantMap[finalConsonant] + virama;
      }

      lastIndex = syllableRegex.lastIndex;
    }

    // Handle trailing consonant (not matched by regex)
    if (lastIndex < text.length) {
      let trailing = text.slice(lastIndex);
      if (consonantMap[trailing]) {
        result += consonantMap[trailing] + virama;
      }
    }

    return result;
  }
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

  constructor(
    private transliterateService: TransliterationService,
    private scoreService: ScoreService,
    private authService: AuthService,
    private router: Router,
    private toastController: ToastController,
    private questUpdateService: QuestUpdateService,
    private themeService: ThemeService
  ) {}

  ngOnInit() {
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
    if (this.transliterationDirection === 'baybayin-to-latin') {
      this.translateBaybayinToLatin(this.inputText);
      // Clear result, don't show any output until transliterate button is clicked
      this.result = '';
    } else {
      this.result = null;
    }
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
    // Real-time update for baybayin-to-latin mode
    if (this.transliterationDirection === 'baybayin-to-latin') {
      this.translateBaybayinToLatin(this.inputText);
      // Clear result, don't show any output until transliterate button is clicked
      this.result = '';
    }
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

    if (this.transliterationDirection === 'latin-to-baybayin') {
      // Try backend first, fallback to local if error or no backend
      if (this.transliterateService && this.transliterateService.transliterateText) {
        let usedLocal = false;
        const direction = this.transliterateFromEnglish ? 'cross_en_to_baybayin' : 'to_baybayin';
        const source_lang = this.transliterateFromEnglish ? 'en' : undefined;
        this.transliterateService.transliterateText(this.inputText, direction, source_lang).subscribe({
           next: async (response) => {
             // reset any previous UI hints
             this.spellCheckedText = null;
             this.spellingMetadata = null;

             // If backend returned cross-language fields, prefer 'baybayin_text' and show translated_text context
             if (response) {
               // Capture spell-check fields when present (both cross and standard flows)
               if ((response as any).spell_checked_text) {
                 this.spellCheckedText = (response as any).spell_checked_text;
               }
               if ((response as any).spelling_metadata) {
                 this.spellingMetadata = (response as any).spelling_metadata;
               }

               if (response.baybayin_text) {
                 // Show the baybayin script and include a short note with translated text in latin
                 this.result = response.baybayin_text;
                 // Prefer the spell-checked Tagalog phrase for the left pane if available
                 this.expectedText = this.spellCheckedText || response.translated_text || response.normalized_text || '';
               } else if (response.transliterated_text) {
                 this.result = response.transliterated_text;
                 // For standard transliteration, show spell-checked input (if provided) as a suggestion
                 this.expectedText = this.spellCheckedText || response.normalized_text || '';
               } else {
                 this.result = this.transliterateLatinToBaybayin(this.inputText);
                 usedLocal = true;
               }
             } else {
               this.result = this.transliterateLatinToBaybayin(this.inputText);
               usedLocal = true;
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
            // Fallback to local
            this.result = this.transliterateLatinToBaybayin(this.inputText);
            this.showSuccessToast();
          }
        });
      } else {
        // No backend, use local
        this.result = this.transliterateLatinToBaybayin(this.inputText);
        this.showSuccessToast();
      }
    } else {
      // Baybayin to Latin translation
      // Try backend first for spelling checker integration, fallback to local if error or no backend
      if (this.transliterateService && this.transliterateService.transliterateText) {
        this.transliterateService.transliterateText(this.inputText, 'to_latin').subscribe({
          next: async (response) => {
            // reset any previous UI hints
            this.spellCheckedText = null;
            this.spellingMetadata = null;

            if (response) {
              // Capture spell-check fields when present
              if ((response as any).spell_checked_text) {
                this.spellCheckedText = (response as any).spell_checked_text;
              }
              if ((response as any).spelling_metadata) {
                this.spellingMetadata = (response as any).spelling_metadata;
              }
              
              if (response.transliterated_text) {
                this.result = response.transliterated_text;
              } else {
                // Fallback to local translation
                this.result = this.handleLocalBaybayinToLatin();
              }
            } else {
              this.result = this.handleLocalBaybayinToLatin();
            }

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
            // Fallback to local
            this.result = this.handleLocalBaybayinToLatin();
            this.showSuccessToast();
          }
        });
      } else {
        // No backend, use local
        this.result = this.handleLocalBaybayinToLatin();
        this.showSuccessToast();
      }
    }
  }

  private handleLocalBaybayinToLatin(): string {
    // Handle local Baybayin to Latin translation with ambiguous syllable logic
    const hasAmbiguous = this.ambiguousSyllables.some(s => s.options.length > 1);
    if (hasAmbiguous && this.ambiguousSyllables.length > 0) {
      return this.getAmbiguousResult();
    } else {
      return this.translateBaybayinToLatin(this.inputText);
    }
  }

  private translateBaybayinToLatin(baybayinText: string): string {
    // Baybayin-to-Latin transliteration with ambiguity tracking for UI prompt
    // Preserve previous ambiguous syllable selections where possible so that
    // confirming a choice doesn't cause the prompt to reappear for later
    // incremental updates with identical syllable options.
    const prevAmbiguous = this.ambiguousSyllables ? this.ambiguousSyllables.slice() : [];
    const prevConfirmed = this.confirmedAmbiguous ? this.confirmedAmbiguous.slice() : [];
    this.ambiguousSyllables = [];
    let result = '';
    const kudlitI = 'ᜒ';
    const kudlitU = 'ᜓ';
    const virama = '᜔';
    const consonantMap: { [key: string]: string } = {
      'ᜃ': 'k', 'ᜄ': 'g', 'ᜅ': 'ng', 'ᜆ': 't', 'ᜇ': 'd', 'ᜈ': 'n',
      'ᜉ': 'p', 'ᜊ': 'b', 'ᜋ': 'm', 'ᜌ': 'y', 'ᜍ': 'r', 'ᜎ': 'l',
      'ᜏ': 'w', 'ᜐ': 's', 'ᜑ': 'h'
    };
    const vowelMap: { [key: string]: string } = {
      'ᜀ': 'a', 'ᜁ': 'i/e', 'ᜂ': 'u/o'
    };
    let i = 0;
    while (i < baybayinText.length) {
      const char = baybayinText[i];
      // Vowel
      if (vowelMap[char]) {
        const options = vowelMap[char] === 'i/e' ? ['i', 'e'] : vowelMap[char] === 'u/o' ? ['u', 'o'] : ['a'];
        // Standalone vowel: selected is just the vowel letter
        this.ambiguousSyllables.push({ latin: vowelMap[char], options, selected: options[0], base: '' });
        result += options[0];
        i++;
        continue;
      }
      // Consonant
      if (consonantMap[char]) {
        let latin = consonantMap[char];
        let vowel = 'a';
        let options = ['a'];
        if (i + 1 < baybayinText.length) {
          const next = baybayinText[i + 1];
          if (next === kudlitI) {
            vowel = 'i/e';
            options = ['i', 'e'];
            i++;
          } else if (next === kudlitU) {
            vowel = 'u/o';
            options = ['u', 'o'];
            i++;
          } else if (next === virama) {
            vowel = '';
            options = [''];
            i++;
          }
        }
        // For consonant syllables, store the consonant base and set selected to the
        // full default syllable (base + default vowel) so results include consonants.
        this.ambiguousSyllables.push({ latin: latin + vowel, options, selected: latin + options[0], base: latin });
        result += latin + options[0];
        i++;
        continue;
      }
      // If not found, skip or output as is
      i++;
    }
    // Initialize confirmedAmbiguous array to match newly built ambiguousSyllables
    const len = this.ambiguousSyllables.length;
    this.confirmedAmbiguous = new Array(len).fill(false);
    // Restore previous confirmed selections when options match at same position
    const arraysEqual = (a: string[], b: string[]) => {
      if (!a || !b || a.length !== b.length) return false;
      for (let k = 0; k < a.length; k++) if (a[k] !== b[k]) return false;
      return true;
    };
    for (let j = 0; j < len; j++) {
      const prev = prevAmbiguous[j];
      if (prev && arraysEqual(prev.options, this.ambiguousSyllables[j].options)) {
        // If previously confirmed, carry over the selected value and confirmation
        let chosen = prev.selected || this.ambiguousSyllables[j].selected;
        const curBase = this.ambiguousSyllables[j].base || '';
        // If current entry has a consonant base but previous selected was only a vowel,
        // prepend the base so the selected value includes the consonant.
        if (curBase && !chosen.startsWith(curBase)) {
          // If previous selected is empty string (virama case) keep as empty
          if (chosen !== '') {
            chosen = curBase + chosen;
          } else {
            chosen = curBase; // consonant with no vowel
          }
        }
        this.ambiguousSyllables[j].selected = chosen;
        if (prevConfirmed[j]) {
          this.confirmedAmbiguous[j] = true;
        }
      }
    }

    return result || 'Translation completed';
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
