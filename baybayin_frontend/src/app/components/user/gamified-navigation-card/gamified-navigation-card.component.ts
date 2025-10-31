import { Component, Input } from '@angular/core';

@Component({
  selector: 'app-gamified-navigation-card',
  templateUrl: './gamified-navigation-card.component.html',
  styleUrls: ['./gamified-navigation-card.component.scss'],
  standalone: false
})
export class GamifiedNavigationCardComponent {
  @Input() title!: string;
  @Input() icon!: string;

  @Input() bgColor: string = '#7ECC71';
  @Input() borderColor: string = '#6AAB5F';

  isHovered = false;
}
