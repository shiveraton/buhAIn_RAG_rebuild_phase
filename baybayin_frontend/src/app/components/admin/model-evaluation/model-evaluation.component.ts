import { Component, Input } from '@angular/core';

interface ModuleParameter{
  parameter: string;
  value: string | number;
}

@Component({
  selector: 'app-model-evaluation',
  templateUrl: './model-evaluation.component.html',
  styleUrls: ['./model-evaluation.component.scss'],
  standalone: false
})
export class ModelEvaluationComponent {
  selectedModelID: string = "Model A"
  models: string[] = ['Model A', 'Model B', 'Model C']
  modelCategory: string = "latin-classification"

  preprocessingMethods: string[] = ['grayscaling', 'binarization', 'noise reduction', 'segmentation', 'resize', 'thinning']
  
  featureExtractionModel: string = "ORB"
  featureExtractionParameter: ModuleParameter[] = [
    {parameter: 'n_features', value: 128},
    {parameter: 'scale_factor', value: 1.2},
    {parameter: 'n_levels', value: 8}
  ]

  @Input() experimentId!: number;


}
