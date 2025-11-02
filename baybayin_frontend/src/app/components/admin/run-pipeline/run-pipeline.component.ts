import { Component } from '@angular/core';
import { ToastController } from '@ionic/angular';

@Component({
  selector: 'app-run-pipeline',
  templateUrl: './run-pipeline.component.html',
  styleUrls: ['./run-pipeline.component.scss'],
  standalone: false
})
export class RunPipelineComponent {
  isRunning = false;
  currentExperiment: string | null = null;

  constructor(private toastController: ToastController) {}

  async handleRunPipeline() {
    this.isRunning = true;
    this.currentExperiment = `EXP-${String(Math.floor(Math.random() * 10000)).padStart(4, '0')}`;

    setTimeout(async () => {
      this.isRunning = false;
      const toast = await this.toastController.create({
        message: `Experiment ${this.currentExperiment} finished successfully.`,
        duration: 2000,
        color: 'success',
      });
      toast.present();
    }, 3000);
  }
}
