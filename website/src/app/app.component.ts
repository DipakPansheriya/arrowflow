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
    const platform = platformOverride || this.userOS;
    let targetUrl = platform === 'macos' ? this.config.macosDownloadUrl : this.config.windowsDownloadUrl;
    const localUrl = platform === 'macos' ? this.config.localMacosUrl : this.config.localWindowsUrl;
    const filename = platform === 'macos' ? 'ArrowFlow.dmg' : 'ArrowFlow.exe';

    // If downloadUrl contains default placeholder, use local static binary
    if (targetUrl.includes('USERNAME') || targetUrl.includes('YOUR_DIRECT_EXE_DOWNLOAD_URL')) {
      targetUrl = localUrl;
    }

    // Trigger direct browser file download
    const anchor = document.createElement('a');
    anchor.href = targetUrl;
    anchor.download = filename;
    anchor.target = '_self';
    document.body.appendChild(anchor);
    anchor.click();
    document.body.removeChild(anchor);
  }

  switchOS(os: 'windows' | 'macos') {
    this.userOS = os;
  }
}
