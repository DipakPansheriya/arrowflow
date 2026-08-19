import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { APP_CONFIG } from '../../config/app-config';

@Component({
  selector: 'app-download-cta',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './download-cta.component.html',
  styleUrls: ['./download-cta.component.scss']
})
export class DownloadCtaComponent implements OnInit {
  config = APP_CONFIG;
  downloadInfo: any = { isSupported: true, platformName: 'Windows', url: '#', platform: 'windows' };

  ngOnInit() {
    this.downloadInfo = this.config.getDownloadInfo();
  }
}
