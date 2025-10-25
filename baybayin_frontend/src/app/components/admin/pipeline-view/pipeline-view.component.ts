import { Component, Input } from '@angular/core';

@Component({
  selector: 'app-pipeline-view',
  templateUrl: './pipeline-view.component.html',
  styleUrls: ['./pipeline-view.component.scss'],
  standalone: false
})
export class PipelineViewComponent {
  @Input() experimentId!: number;

  pipelineSteps = [
    { name: "Original Data", status: "completed", description: "Raw input images" },
    { name: "Grayscale", status: "completed", description: "Convert to grayscale" },
    { name: "Binarization", status: "completed", description: "Threshold processing" },
    { name: "Noise Reduction", status: "completed", description: "Gaussian filter applied" },
    { name: "Thinning", status: "completed", description: "Morphological thinning" },
    { name: "Feature Extraction", status: "completed", description: "HOG features extracted" },
    { name: "Model Training", status: "completed", description: "SVM classifier trained" },
  ];
}
