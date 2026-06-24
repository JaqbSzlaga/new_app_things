const CACHE_NAME = 'grocery-pantry-v5-fewer-products';
const STATIC_ASSETS = [
  '/',
  '/static/style.css?v=5',
  '/manifest.webmanifest',
  '/static/products/mleko.svg',
  '/static/products/jajka.svg',
  '/static/products/chleb.svg',
  '/static/products/maso.svg',
  '/static/products/ser.svg',
  '/static/products/makaron.svg',
  '/static/products/ryz.svg',
  '/static/products/cukier.svg',
  '/static/products/kawa.svg',
  '/static/products/woda.svg'
];

self.addEventListener('install', event => {
  event.waitUntil(caches.open(CACHE_NAME).then(cache => cache.addAll(STATIC_ASSETS)));
  self.skipWaiting();
});

self.addEventListener('activate', event => {
  event.waitUntil(
    caches.keys().then(keys => Promise.all(keys.filter(key => key !== CACHE_NAME).map(key => caches.delete(key))))
  );
  self.clients.claim();
});

self.addEventListener('fetch', event => {
  if (event.request.method !== 'GET') return;
  event.respondWith(
    fetch(event.request, { cache: 'no-store' }).catch(() => caches.match(event.request).then(response => response || caches.match('/')))
  );
});
