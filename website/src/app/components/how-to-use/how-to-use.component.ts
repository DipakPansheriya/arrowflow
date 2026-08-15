import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';

@Component({
  selector: 'app-how-to-use',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './how-to-use.component.html',
  styleUrls: ['./how-to-use.component.scss']
})
export class HowToUseComponent {
  useSteps = [
    {
      step: 'Step 1',
      title: 'Download ArrowFlow.exe',
      description: 'Get the standalone Windows executable binary from the download section. No installation wizard required.'
    },
    {
      step: 'Step 2',
      title: 'Launch Executable',
      description: 'Double click ArrowFlow.exe on Windows 10 or 11. The application starts with default Taskbar button visibility.'
    },
    {
      step: 'Step 3',
      title: 'Enter Password Authentication',
      description: 'Enter your access password on the dark lock screen interface and press ENTER or click UNLOCK.'
    },
    {
      step: 'Step 4',
      title: 'Select Target VS Code Window',
      description: 'Choose your open Visual Studio Code window from the target window dropdown list. Click Refresh if newly opened.'
    },
    {
      step: 'Step 5',
      title: 'Configure Arrow Press Range',
      description: 'Set your desired MIN and MAX press bounds (e.g. MIN: 10, MAX: 40). A new target is generated every 60 seconds.'
    },
    {
      step: 'Step 6',
      title: 'Configure Optional Mouse Automation',
      description: 'Mouse clicks execute safely inside active VS Code editor text bounds in parallel with keyboard events.'
    },
    {
      step: 'Step 7',
      title: 'Configure File Switching Options',
      description: 'Toggle File Switching ON/OFF and set MIN/MAX tab counts for Ctrl+Shift+Tab file switching sequence at minute transitions.'
    },
    {
      step: 'Step 8',
      title: 'Press START AUTOMATION',
      description: 'Click ▶ START AUTOMATION to initiate the worker thread. Live progress bar and target counters update automatically.'
    },
    {
      step: 'Step 9',
      title: 'Use ESC & ALT+SPACE Global Shortcuts',
      description: 'Press global ESC key anytime to toggle ON/OFF. Press ALT+SPACE to toggle window and Taskbar button visibility.'
    }
  ];
}
