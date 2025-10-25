import { Component, OnInit } from '@angular/core';

@Component({
  selector: 'app-image-trans-system',
  templateUrl: './image-trans-system.page.html',
  styleUrls: ['./image-trans-system.page.scss'],
  standalone: false
})
export class ImageTransSystemPage implements OnInit {
  activeTab: string = 'pipeline'
  selectedExperimentId: number = 1;

  constructor() { }

  ngOnInit() {
  }

  changeTab(tab: string) {
    this.activeTab = tab;
  }

  onSelectExperiment(id: number) {
    this.selectedExperimentId = id;
  }

}
