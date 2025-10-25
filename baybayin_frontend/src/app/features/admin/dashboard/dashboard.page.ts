import { Component, OnInit } from '@angular/core';
import { Router } from '@angular/router';

@Component({
  selector: 'app-dashboard',
  templateUrl: './dashboard.page.html',
  styleUrls: ['./dashboard.page.scss'],
  standalone: false
})
export class DashboardPage implements OnInit{
   totalUsers = 1200;
  totalTrivia = 450;
  highestAccuracy = 95;

  totalExperiments = 25;

  topUsers = [
    { name: 'Alice', score: 1200 },
    { name: 'Bob', score: 1100 },
    { name: 'Charlie', score: 1050 }
  ];

  recentExperiments = [
    { id: 'EXP-023', accuracy: 92 },
    { id: 'EXP-022', accuracy: 90 },
    { id: 'EXP-021', accuracy: 88 }
  ];

  constructor() { }

  ngOnInit(): void { }
}
