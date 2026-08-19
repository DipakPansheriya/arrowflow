import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { APP_CONFIG } from '../../config/app-config';

@Component({
  selector: 'app-hero',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './hero.component.html',
  styleUrls: ['./hero.component.scss']
})
export class HeroComponent implements OnInit {
  config = APP_CONFIG;
  downloadInfo: any = { isSupported: true, platformName: 'Windows', url: '#', platform: 'windows' };

  ngOnInit() {
    this.downloadInfo = this.config.getDownloadInfo();
  }

  // Interactive Live Mockup State
  mockupRunning = false;
  mockupTarget = 27;
  mockupCurrent = 0;
  mockupPct = 0;
  mockupFileSwitch = false;
  intervalId: any = null;

  startMockupSimulation() {
    if (this.mockupRunning) {
      this.stopMockupSimulation();
      return;
    }

    this.mockupRunning = true;
    this.mockupTarget = Math.floor(Math.random() * (40 - 10 + 1)) + 10;
    this.mockupCurrent = 0;
    this.mockupPct = 0;

    this.intervalId = setInterval(() => {
      if (this.mockupCurrent < this.mockupTarget) {
        this.mockupCurrent++;
        this.mockupPct = Math.round((this.mockupCurrent / this.mockupTarget) * 100);
      } else {
        this.stopMockupSimulation();
      }
    }, 150);
  }

  stopMockupSimulation() {
    this.mockupRunning = false;
    if (this.intervalId) {
      clearInterval(this.intervalId);
      this.intervalId = null;
    }
  }

  downloadExe() {
    this.config.triggerDownload();
  }
}
