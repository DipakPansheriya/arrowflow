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

  // Windows Direct Release Asset URL
  windowsDownloadUrl: 'https://github.com/DipakPansheriya/arrowflow/releases/latest/download/ArrowFlow.exe',
  localWindowsUrl: '/ArrowFlow.exe',

  // macOS Direct Release Asset URL
  macosDownloadUrl: 'https://github.com/DipakPansheriya/arrowflow/releases/latest/download/ArrowFlow.dmg',
  localMacosUrl: '/ArrowFlow.dmg'
};
