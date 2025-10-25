import { Component, Input } from '@angular/core';

@Component({
  selector: 'app-model-evaluation',
  templateUrl: './model-evaluation.component.html',
  styleUrls: ['./model-evaluation.component.scss'],
  standalone: false
})
export class ModelEvaluationComponent {
  @Input() experimentId!: number;

  confusionMatrix = [
    [45, 2, 1, 2],
    [3, 48, 1, 0],
    [1, 2, 46, 1],
    [2, 0, 2, 46],
  ];

  labels = ["Class A", "Class B", "Class C", "Class D"];
}
