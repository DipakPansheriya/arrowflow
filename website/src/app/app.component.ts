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
    const targetUrl = platformOverride === 'macos' ? this.config.macosDownloadUrl 
                    : platformOverride === 'windows' ? this.config.windowsDownloadUrl 
                    : this.config.getDownloadInfo().url;
    window.location.href = targetUrl;
  }

  switchOS(os: 'windows' | 'macos') {
    this.userOS = os;
  }
}
