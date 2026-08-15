import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { APP_CONFIG } from '../../config/app-config';

interface FaqItem {
  question: string;
  answer: string;
  open: boolean;
}

@Component({
  selector: 'app-faq',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './faq.component.html',
  styleUrls: ['./faq.component.scss']
})
export class FaqComponent {
  config = APP_CONFIG;

  faqs: FaqItem[] = [
    {
      question: 'What is ArrowFlow?',
      answer: 'ArrowFlow is a lightweight Windows desktop automation utility focused on VS Code workflow automation, randomized keyboard press generation, mouse click execution, and file tab switching.',
      open: true
    },
    {
      question: 'Which operating system is supported?',
      answer: 'ArrowFlow is natively compiled for 64-bit Windows 10 and Windows 11. It utilizes native Win32 API functions for window targeting and low-level keyboard listeners.',
      open: false
    },
    {
      question: 'How do I install ArrowFlow?',
      answer: 'ArrowFlow requires zero installation! It is distributed as a single standalone executable (ArrowFlow.exe). Simply download the EXE file and launch it directly.',
      open: false
    },
    {
      question: 'Does ArrowFlow require Python?',
      answer: 'No. ArrowFlow is packaged into a self-contained Windows executable via PyInstaller. All dependencies, libraries, and binaries are bundled inside the standalone EXE.',
      open: false
    },
    {
      question: 'How do I select VS Code?',
      answer: 'Open ArrowFlow, log in, and use the "TARGET WINDOW" dropdown selector to choose your running Visual Studio Code window. ArrowFlow automatically scans and highlights active VS Code windows.',
      open: false
    },
    {
      question: 'How does the random per-minute target work?',
      answer: 'At the start of every 60-second cycle, ArrowFlow generates a single random integer target N between your configured MIN and MAX bounds (e.g. 10 to 40). It then schedules N decoupled keyboard events and N mouse clicks independently across the 60-second window.',
      open: false
    },
    {
      question: 'How does Mouse Automation work?',
      answer: 'When enabled, Mouse Automation executes atomic left mouse clicks inside the active editor text region of VS Code. It automatically skips redundant window focus calls and cursor moves if the mouse is already positioned inside editor bounds.',
      open: false
    },
    {
      question: 'How does File Switching work?',
      answer: 'File Switching executes Ctrl+Shift+Tab keyboard shortcut sequences at minute transitions. You can configure the minimum and maximum tab count per cycle.',
      open: false
    },
    {
      question: 'What does ESC do?',
      answer: 'Pressing the global ESC key acts as an instant master toggle: if automation is currently running (ON), pressing ESC turns it OFF; if automation is currently stopped (OFF), pressing ESC turns it ON.',
      open: false
    },
    {
      question: 'Where can I download the latest version?',
      answer: `You can download the latest official release (v${APP_CONFIG.version}) directly from the Download section on this website or via official release repositories.`,
      open: false
    }
  ];

  toggleFaq(index: number) {
    this.faqs[index].open = !this.faqs[index].open;
  }
}
