import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { APP_CONFIG } from '../../config/app-config';

@Component({
  selector: 'app-footer',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './footer.component.html',
  styleUrls: ['./footer.component.scss']
})
export class FooterComponent {
  config = APP_CONFIG;
  currentYear = new Date().getFullYear();

  downloadExe() {
    window.open(this.config.downloadUrl, '_blank');
  }
}
