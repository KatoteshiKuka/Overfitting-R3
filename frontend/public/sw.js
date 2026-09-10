/*
  Service worker minimo.

  Serve a rendere l'app installabile sul telefono e a non lasciare una pagina bianca
  quando la rete cade a metà demo. Non fa cache dei dati: presidi, code e arrivi devono
  essere quelli veri del momento — mostrare un'attesa vecchia sarebbe peggio che non
  mostrarla. In cache finisce solo il guscio dell'applicazione.
*/

const CACHE = 'healthpulse-shell-v1';
const SHELL = ['/', '/manifest.webmanifest', '/icon.svg'];

self.addEventListener('install', (event) => {
  event.waitUntil(
    caches
      .open(CACHE)
      .then((cache) => cache.addAll(SHELL))
      .then(() => self.skipWaiting()),
  );
});

self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches
      .keys()
      .then((keys) => Promise.all(keys.filter((key) => key !== CACHE).map((key) => caches.delete(key))))
      .then(() => self.clients.claim()),
  );
});

self.addEventListener('fetch', (event) => {
  const { request } = event;
  if (request.method !== 'GET') return;

  const url = new URL(request.url);
  // Le chiamate all'API non si mettono mai in cache: un dato sanitario vecchio inganna.
  if (url.pathname.startsWith('/api/')) return;
  // Le mappe hanno già la loro cache nel browser e occuperebbero spazio inutilmente.
  if (url.origin !== self.location.origin) return;

  if (request.mode === 'navigate') {
    // Prima la rete, così un aggiornamento si vede subito; la cache è la rete di sicurezza.
    event.respondWith(
      fetch(request).catch(() => caches.match('/').then((hit) => hit ?? Response.error())),
    );
    return;
  }

  event.respondWith(
    caches.match(request).then((hit) => hit ?? fetch(request)),
  );
});
