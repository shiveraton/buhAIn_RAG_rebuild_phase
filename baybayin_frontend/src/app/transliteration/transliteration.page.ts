import { Component } from '@angular/core';
import { Camera, CameraResultType, CameraSource } from '@capacitor/camera';

import { TransliterationService } from '../services/transliteration/transliteration.service';

@Component({
  selector: 'app-transliteration',
  templateUrl: 'transliteration.page.html',
  styleUrls: ['transliteration.page.scss'],
  standalone: false,
})
export class TransliterationPage {
  showTextInput = false;
  inputText = '';
  result: string | null = null;
  cameraImage: string | null = null;


  constructor(private transliterateService: TransliterationService) {}

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

  handleUpload(event: any) {
    // Send uploaded image to backend for transliteration
    // Placeholder: show result
    this.result = 'Uploaded image sent to James and Jhed.';
  }

  onText() {
    this.showTextInput = !this.showTextInput;
  }

  submitText() {
    if(!this.inputText){
      this.result = 'Please enter some text.'
    }
    this.transliterateService.transliterateText(this.inputText).subscribe({
      next: (response) => {
        console.log(response)
      },
      error: (err) => {
        console.log(err)
      }
    })
  }
}
