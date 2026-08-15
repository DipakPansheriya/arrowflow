import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { APP_CONFIG } from '../../config/app-config';

interface DocSection {
  id: string;
  title: string;
  category: string;
}

@Component({
  selector: 'app-documentation',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './documentation.component.html',
  styleUrls: ['./documentation.component.scss']
})
export class DocumentationComponent {
  config = APP_CONFIG;
  activeSection = 'getting-started';

  sections: DocSection[] = [
    { id: 'getting-started', title: '1. Getting Started', category: 'Overview' },
    { id: 'authentication', title: '2. Authentication', category: 'Overview' },
    { id: 'vscode-selection', title: '3. VS Code Selection', category: 'Configuration' },
    { id: 'arrow-range', title: '4. Arrow Press Range', category: 'Configuration' },
    { id: 'per-minute-target', title: '5. Random Per-Minute Target', category: 'Core Engine' },
    { id: 'keyboard-automation', title: '6. Keyboard Automation', category: 'Core Engine' },
    { id: 'mouse-automation', title: '7. Mouse Automation', category: 'Core Engine' },
    { id: 'file-switching', title: '8. File Switching', category: 'Core Engine' },
    { id: 'esc-toggle', title: '9. ESC Toggle', category: 'Hotkeys' },
    { id: 'start-stop', title: '10. Start / Stop', category: 'Control' },
    { id: 'window-behavior', title: '11. Window / Taskbar Behavior', category: 'Interface' },
    { id: 'troubleshooting', title: '12. Troubleshooting', category: 'Help' },
    { id: 'faq-section', title: '13. Frequently Asked Questions', category: 'Help' }
  ];

  setActiveSection(id: string) {
    this.activeSection = id;
    const element = document.getElementById(id);
    if (element) {
      element.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
  }
}
