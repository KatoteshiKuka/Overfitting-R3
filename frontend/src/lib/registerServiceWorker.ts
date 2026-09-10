/**
 * Registra il service worker che rende l'app installabile sul telefono.
 *
 * Solo in produzione: in sviluppo un worker che serve il guscio dalla cache maschera le
 * modifiche appena fatte, e si finisce a chiedersi perché il codice non abbia effetto.
 * Per provare la PWA dal telefono si usa `pnpm preview --host`, che serve la build vera.
 */
export function registerServiceWorker(): void {
  if (!import.meta.env.PROD) return;
  if (!('serviceWorker' in navigator)) return;

  window.addEventListener('load', () => {
    navigator.serviceWorker.register('/sw.js').catch(() => {
      // Senza service worker l'app funziona lo stesso: si perde solo l'installabilità.
    });
  });
}
