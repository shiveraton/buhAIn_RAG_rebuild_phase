import { Component, OnInit, OnDestroy } from '@angular/core';
import { Camera, CameraResultType, CameraSource } from '@capacitor/camera';

import { TransliterationService } from '../services/transliteration/transliteration.service';
import { ScoreService } from '../services/score.service';
import { AuthService } from '../services/auth.service';
import { Subscription } from 'rxjs';

@Component({
  selector: 'app-transliteration',
  templateUrl: 'transliteration.page.html',
  styleUrls: ['transliteration.page.scss'],
  standalone: false,
})
export class TransliterationPage implements OnInit, OnDestroy {
  showTextInput = false;
  inputText = '';
  result: string | null = null;
  cameraImage: string | null = null;
  expectedText: string = ''; // For scoring purposes
  currentUser: any = null;
  private authSubscription?: Subscription;

  constructor(
    private transliterateService: TransliterationService,
    private scoreService: ScoreService,
    private authService: AuthService
  ) {}

  ngOnInit() {
    // Subscribe to authentication state changes
    this.authSubscription = this.authService.currentUser$.subscribe((user) => {
      this.currentUser = user;
    });
  }

  ngOnDestroy() {
    if (this.authSubscription) {
      this.authSubscription.unsubscribe();
    }
  }

  async onCamera() {
    try {
      const image = await Camera.getPhoto({
        quality: 80,
        allowEditing: false,
        resultType: CameraResultType.DataUrl,
        source: CameraSource.Camera,
      });
      this.cameraImage = image.dataUrl || null;
      this.result = 'ARA DAE.';
      
      // Award points for using camera transliteration
      if (this.result && this.result !== 'Camera cancelled or failed.') {
        // Simulate accuracy calculation (in real app, compare with expected result)
        const mockAccuracy = Math.floor(Math.random() * 30) + 70; // 70-100% accuracy
        await this.scoreService.awardTransliterationPoints(mockAccuracy);
      }
    } catch (err) {
      this.result = 'Camera cancelled or failed.';
    }
  }

  handleCamera(event: any) {
    // (Not used with Capacitor Camera)
  }

  onUpload() {
    // Trigger upload input
    const uploadInput = document.querySelector<HTMLInputElement>('#uploadInput');
    uploadInput?.click();
  }

  async handleUpload(event: any) {
    // Send uploaded image to backend for transliteration
    // Placeholder: show result
    this.result = 'Uploaded image sent to James and Jhed.';
    
    // Award points for successful upload
    const mockAccuracy = Math.floor(Math.random() * 30) + 70; // 70-100% accuracy
    await this.scoreService.awardTransliterationPoints(mockAccuracy);
  }

  onText() {
    this.showTextInput = !this.showTextInput;
  }

  async submitText() {
    if(!this.inputText){
      this.result = 'Please enter some text.'
      return;
    }
    
    this.transliterateService.transliterateText(this.inputText).subscribe({
      next: async (response) => {
        console.log(response);
        this.result = response.transliterated_text || 'Transliteration completed';
        
        // Award points for text transliteration
        if (response.transliterated_text) {
          // In a real app, you'd compare with expected results
          const mockAccuracy = Math.floor(Math.random() * 30) + 70; // 70-100% accuracy
          await this.scoreService.awardTransliterationPoints(mockAccuracy);
        }
      },
      error: (err) => {
        console.log(err);
        this.result = 'Error processing text. Please try again.';
      }
    });
  }
}
