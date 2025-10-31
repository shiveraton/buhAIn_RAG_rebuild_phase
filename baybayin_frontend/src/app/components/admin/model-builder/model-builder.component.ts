import { Component, OnInit } from '@angular/core';
import { ImageClassificationSystemService } from 'src/app/core/services/image-classification-system.service';

@Component({
  selector: 'app-model-builder',
  templateUrl: './model-builder.component.html',
  styleUrls: ['./model-builder.component.scss'],
  standalone: false
})
export class ModelBuilderComponent  implements OnInit {
  selectedFile: File | null = null
  modelName: string | null = null

  selectedModelCategory = 'Latin-Classification'
  modelCategory = ['Latin-Classification', 'Baybayin-Classification', 'Latin-Baybayin-Classification']

  preprocessingMethods: string[] = []
  preprocessing: string[] = []

  selectedFeatureExtractionMethod = "ORB"
  featureExtractionMethods: string[] = [];

  vocab: string[] = []
  classification: string[] = [];

  constructor(private imageSystem: ImageClassificationSystemService) { }

  async ngOnInit() {
    try {
      const methods = await this.imageSystem.getModelPipelineMethods();
      console.log(methods)

      methods.forEach(method => {
        switch (method.category_name) {
          case 'preprocessing':
            this.preprocessingMethods.push(method.module_name);
            break;
          case 'feature_extraction':
            this.featureExtractionMethods.push(method.module_name);
            break;
          case 'feature_encoding':
            this.vocab.push(method.module_name);
            break;
          case 'classification':
            this.classification.push(method.module_name);
            break;
          default:
            console.warn('Unknown category:', method.category_name);
        }
      });
      console.log(this.preprocessing)
    } catch (error) {
      console.error(error);
    }
  }

  onFileSelected(event: Event) {
    const input = event.target as HTMLInputElement;
    if (!input.files?.length) return;

    const file = input.files[0];
    if (file.type !== 'application/zip') {
      alert('Only ZIP files are allowed!');
      return;
    }

    this.selectedFile = file;
    console.log('Selected file:', file.name);
  }

  togglePreprocessing(method: string) {
    const index = this.preprocessing.indexOf(method);
    if (index === -1) {
      this.preprocessing.push(method);
    } else {
      this.preprocessing.splice(index, 1);
    }
  }


}
