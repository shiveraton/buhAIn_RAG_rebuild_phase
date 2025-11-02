import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';

import { IonicModule } from '@ionic/angular';

import { ImageTransSystemPageRoutingModule } from './image-trans-system-routing.module';

import { ImageTransSystemPage } from './image-trans-system.page';

import { PipelineViewComponent } from 'src/app/components/admin/pipeline-view/pipeline-view.component';
import { ExperimentLogsComponent } from 'src/app/components/admin/experiment-logs/experiment-logs.component';
import { ModelBuilderComponent } from 'src/app/components/admin/model-builder/model-builder.component';
import { ModelEvaluationComponent } from 'src/app/components/admin/model-evaluation/model-evaluation.component';
import { RunPipelineComponent } from 'src/app/components/admin/run-pipeline/run-pipeline.component';

import { SharedModule } from 'src/app/shared/shared.module';

@NgModule({
  imports: [
    CommonModule,
    FormsModule,
    IonicModule,
    ImageTransSystemPageRoutingModule,
    SharedModule
  ],
  declarations: [
    ImageTransSystemPage,
    PipelineViewComponent,
    ExperimentLogsComponent,
    ModelBuilderComponent,
    ModelEvaluationComponent,
    RunPipelineComponent
  ]
})
export class ImageTransSystemPageModule {}
