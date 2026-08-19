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

  getDownloadInfo(): { url: string; platformName: string; isSupported: boolean; platform: string } {
    if (typeof window === 'undefined') {
      return { url: this.windowsDownloadUrl, platformName: 'Windows', isSupported: true, platform: 'windows' };
    }

    const platform = window.navigator.platform.toLowerCase();
    const userAgent = window.navigator.userAgent.toLowerCase();
    
    const isMac = platform.includes('mac') || userAgent.includes('macintosh') || userAgent.includes('mac os');
    const isWin = platform.includes('win') || userAgent.includes('windows');
    
    if (isMac) {
      return { url: this.macosDownloadUrl, platformName: 'macOS', isSupported: true, platform: 'macos' };
    } else if (isWin) {
      return { url: this.windowsDownloadUrl, platformName: 'Windows', isSupported: true, platform: 'windows' };
    } else {
      // Default to windows for unsupported, but mark as unsupported
      return { url: this.windowsDownloadUrl, platformName: 'Unsupported', isSupported: false, platform: 'other' };
    }
  }
};
