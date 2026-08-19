// =========================================================================
// ARROWFLOW LANDING PAGE — CENTRAL DOWNLOAD CONFIGURATION
// =========================================================================
// Replace windowsDownloadUrl and macosDownloadUrl with your direct GitHub Release asset URLs:
//
// Windows Direct Asset URL Example:
// "https://github.com/<owner>/<repo>/releases/download/v1.0.0/ArrowFlow.exe"
//
// macOS Direct Asset URL Example:
// "https://github.com/<owner>/<repo>/releases/download/v1.0.0/ArrowFlow.dmg"
//
// IMPORTANT: The URLs MUST point directly to the actual release asset files (.exe / .dmg),
// NOT to the GitHub repository homepage or release list page.
// =========================================================================

export const APP_CONFIG = {
  name: 'ArrowFlow',
  subtitle: 'Cross-Platform VS Code Automation',
  description: 'Lightweight desktop automation for Windows & macOS.',
  version: 'v1.0.0',

  // Download URLs & Fallbacks
  downloadUrl: '/ArrowFlow.exe',
  windowsDownloadUrl: 'https://github.com/DipakPansheriya/arrowflow/releases/latest/download/ArrowFlow.exe',
  localWindowsUrl: '/ArrowFlow.exe',

  macosDownloadUrl: 'https://github.com/DipakPansheriya/arrowflow/releases/latest/download/ArrowFlow.dmg',
  localMacosUrl: '/ArrowFlow.dmg',

  triggerDownload(platformOverride?: 'windows' | 'macos') {
    if (typeof window === 'undefined') return;

    let isMac = false;
    if (window.navigator) {
      const platform = window.navigator.platform.toLowerCase();
      const userAgent = window.navigator.userAgent.toLowerCase();
      isMac = platform.includes('mac') || userAgent.includes('macintosh') || userAgent.includes('mac os');
    }

    const platform = platformOverride || (isMac ? 'macos' : 'windows');
    const localUrl = platform === 'macos' ? this.localMacosUrl : this.localWindowsUrl;
    const filename = platform === 'macos' ? 'ArrowFlow.dmg' : 'ArrowFlow.exe';

    const anchor = document.createElement('a');
    anchor.href = localUrl;
    anchor.download = filename;
    anchor.target = '_self';
    document.body.appendChild(anchor);
    anchor.click();
    document.body.removeChild(anchor);
  }
};
