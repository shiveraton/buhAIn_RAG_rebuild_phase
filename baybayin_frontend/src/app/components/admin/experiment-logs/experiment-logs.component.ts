import { Component, EventEmitter, Output } from '@angular/core';

@Component({
  selector: 'app-experiment-logs',
  templateUrl: './experiment-logs.component.html',
  styleUrls: ['./experiment-logs.component.scss'],
  standalone: false
})
export class ExperimentLogsComponent {
  @Output() selectExperiment = new EventEmitter<number>();
  searchTerm: string = '';

  experiments = [
    { id: 1, dataset: 'BuhAIn-v2', methods: 'Grayscale, Binarization, Noise Reduction', featureModel: 'HOG', classifier: 'SVM-RBF', accuracy: '92.1%' },
    { id: 2, dataset: 'BuhAIn-v2', methods: 'Grayscale, Thinning', featureModel: 'SIFT', classifier: 'Random Forest', accuracy: '89.7%' },
    { id: 3, dataset: 'BuhAIn-v1', methods: 'Grayscale, Binarization, Thinning', featureModel: 'HOG', classifier: 'CNN-ResNet50', accuracy: '94.3%' },
  ];

  get filteredExperiments() {
    return this.experiments.filter(e =>
      Object.values(e).some(val =>
        val.toString().toLowerCase().includes(this.searchTerm.toLowerCase())
      )
    );
  }
}
