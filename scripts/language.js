/* DinoRPG Maintenance — Lightweight browser language detection (FR/EN/ES/DE).
 * Only the French entry pages auto-redirect. Explicit language pages remain stable.
 * A visitor's manual selection takes precedence over browser preferences.
 */
(() => {
  'use strict';

  const supported = new Set(['fr', 'en', 'es', 'de']);
  const preferenceKey = 'dinorpg-maintenance-language';

  function normalizedLanguage(value) {
    const language = String(value || '').split(/[-_]/, 1)[0].toLowerCase();
    return supported.has(language) ? language : null;
  }

  function savedLanguage() {
    try {
      return normalizedLanguage(localStorage.getItem(preferenceKey));
    } catch {
      // Some privacy settings / browsers disable localStorage.
      return null;
    }
  }

  function preferredBrowserLanguage() {
    const options = navigator.languages && navigator.languages.length
      ? navigator.languages
      : [navigator.language];

    for (const language of options) {
      const normalized = normalizedLanguage(language);
      if (normalized) return normalized;
    }
    return 'fr';
  }

  // Auto-detect only on French entry pages, never on explicitly selected /en/, /es/ or /de/.
  // This also works under GitHub Pages project paths and with direct file:// previews.
  const entry = document.documentElement.dataset.autoLanguage;
  const preferred = savedLanguage() || preferredBrowserLanguage();
  if ((entry === 'maintenance' || entry === 'credits') && preferred !== 'fr') {
    const page = entry === 'credits' ? 'credits.html' : '';
    location.replace(new URL(`${preferred}/${page}`, document.baseURI).href);
    return;
  }

  function saveManualLanguage() {
    document.querySelectorAll('a[hreflang]').forEach((link) => {
      const language = normalizedLanguage(link.getAttribute('hreflang'));
      if (!language) return;
      link.addEventListener('click', () => {
        try {
          localStorage.setItem(preferenceKey, language);
        } catch {
          // Navigation still works even if storage is blocked.
        }
      });
    });
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', saveManualLanguage, { once: true });
  } else {
    saveManualLanguage();
  }
})();
