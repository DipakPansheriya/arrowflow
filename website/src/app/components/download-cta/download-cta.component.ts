import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { APP_CONFIG } from '../../config/app-config';

@Component({
  selector: 'app-download-cta',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './download-cta.component.html',
  styleUrls: ['./download-cta.component.scss']
})
export class DownloadCtaComponent {
  config = APP_CONFIG;

  downloadExe() {
    this.config.triggerDownload();
  }
}
