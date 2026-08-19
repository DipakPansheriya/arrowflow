import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { APP_CONFIG } from './config/app-config';

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './app.component.html',
  styleUrls: ['./app.component.scss']
})
export class AppComponent implements OnInit {
  config = APP_CONFIG;
  userOS: 'windows' | 'macos' | 'other' = 'windows';

  ngOnInit() {
    this.detectOperatingSystem();
  }

  detectOperatingSystem() {
    if (typeof window !== 'undefined' && window.navigator) {
      const platform = window.navigator.platform.toLowerCase();
      const userAgent = window.navigator.userAgent.toLowerCase();
      
      if (platform.includes('mac') || userAgent.includes('macintosh') || userAgent.includes('mac os')) {
        this.userOS = 'macos';
      } else {
        this.userOS = 'windows';
      }
    }
  }

  downloadExe(platformOverride?: 'windows' | 'macos') {
    this.config.triggerDownload(platformOverride);
  }

  switchOS(os: 'windows' | 'macos') {
    this.userOS = os;
  }
}
