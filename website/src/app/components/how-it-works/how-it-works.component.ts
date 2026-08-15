import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';

@Component({
  selector: 'app-how-it-works',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './how-it-works.component.html',
  styleUrls: ['./how-it-works.component.scss']
})
export class HowItWorksComponent {
  steps = [
    {
      num: '01',
      title: 'Open ArrowFlow',
      description: 'Download and launch ArrowFlow.exe. No Python runtime or installation wizard required.'
    },
    {
      num: '02',
      title: 'Enter Password',
      description: 'Enter your secure access password on the lock screen to unlock the application controls.'
    },
    {
      num: '03',
      title: 'Configure Settings',
      description: 'Select your target VS Code window from the dropdown, adjust Arrow Press Range (MIN/MAX), and enable File Switching.'
    },
    {
      num: '04',
      title: 'Start Automation',
      description: 'Click START AUTOMATION or press ESC. Use ALT+SPACE anytime to toggle Taskbar and window visibility.'
    }
  ];
}
