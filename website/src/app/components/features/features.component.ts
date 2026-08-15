import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';

interface FeatureItem {
  id: string;
  icon: string;
  title: string;
  description: string;
  tag: string;
}

@Component({
  selector: 'app-features',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './features.component.html',
  styleUrls: ['./features.component.scss']
})
export class FeaturesComponent {
  features: FeatureItem[] = [
    {
      id: 'randomized',
      icon: '🎲',
      title: 'Randomized Automation',
      description: 'Generates a unique target count and randomized timing offsets for every 60-second minute window.',
      tag: 'Core Feature'
    },
    {
      id: 'press-range',
      icon: '🎚️',
      title: 'Configurable Press Range',
      description: 'Custom MIN and MAX inputs (e.g. 10 to 40) control the dynamic per-minute activity target bounds.',
      tag: 'Customizable'
    },
    {
      id: 'keyboard',
      icon: '⌨️',
      title: 'Keyboard Automation',
      description: 'Automates UP, DOWN, LEFT, and RIGHT arrow key inputs with randomized direction selection.',
      tag: 'Input Engine'
    },
    {
      id: 'mouse',
      icon: '🖱️',
      title: 'Mouse Automation',
      description: 'Executes atomic left mouse clicks safely centered inside the active VS Code editor text region.',
      tag: 'Input Engine'
    },
    {
      id: 'vscode-selection',
      icon: '🎯',
      title: 'VS Code Target Selection',
      description: 'Enumerates running top-level windows and auto-selects active Visual Studio Code editor windows.',
      tag: 'Targeting'
    },
    {
      id: 'file-switching',
      icon: '📑',
      title: 'File Switching',
      description: 'Performs dynamic Ctrl+Shift+Tab sequences at minute transitions based on configurable MIN/MAX ranges.',
      tag: 'Workflow'
    },
    {
      id: 'esc-toggle',
      icon: '⚡',
      title: 'ESC Global Toggle',
      description: 'Global ESC key shortcut acts as a master ON/OFF toggle from any application without focusing ArrowFlow.',
      tag: 'Control'
    },
    {
      id: 'taskbar-behavior',
      icon: '🪟',
      title: 'Modern Windows UI',
      description: 'Dark-themed responsive desktop interface with ALT+SPACE taskbar and window visibility toggling.',
      tag: 'Interface'
    }
  ];
}
