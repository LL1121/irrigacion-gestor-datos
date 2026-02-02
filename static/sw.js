const CACHE_VERSION = 'v2';
const CACHE_NAME = `irrigacion-cache-${CACHE_VERSION}`;
const ASSETS_TO_CACHE = [
  '/',
  '/dashboard/',
  '/cargar/',
  '/static/offline-upload.js',
  'https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css',
  'https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js',
  'https://cdn.jsdelivr.net/npm/bootstrap-icons@1.10.0/font/bootstrap-icons.css',
  'https://cdn.jsdelivr.net/npm/sweetalert2@11/dist/sweetalert2.all.min.js'
];

self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => cache.addAll(ASSETS_TO_CACHE)).catch((err) => {
      console.error('SW install caching failed:', err);
    })
  );
});

self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((keys) =>
      Promise.all(
        keys
          .filter((key) => key !== CACHE_NAME)
          .map((oldKey) => caches.delete(oldKey))
      )
    )
  );
});

self.addEventListener('fetch', (event) => {
  if (event.request.method !== 'GET') return;

  const acceptHeader = event.request.headers.get('accept') || '';
  const isHTML = event.request.mode === 'navigate' || acceptHeader.includes('text/html');

  if (isHTML) {
    // Network First for HTML
    event.respondWith(
      fetch(event.request)
        .then((response) => {
          const responseClone = response.clone();
          caches.open(CACHE_NAME).then((cache) => cache.put(event.request, responseClone));
          return response;
        })
        .catch(() => caches.match(event.request))
    );
  } else {
    // Cache First for static assets
    event.respondWith(
      caches.match(event.request).then((cached) => {
        if (cached) return cached;
        return fetch(event.request)
          .then((response) => {
            const responseClone = response.clone();
            caches.open(CACHE_NAME).then((cache) => cache.put(event.request, responseClone));
            return response;
          })
          .catch(() => cached);
      })
    );
  }
});

// Background Sync - Sincronización automática de mediciones pendientes
self.addEventListener('sync', (event) => {
  if (event.tag === 'sync-uploads') {
    event.waitUntil(syncPendingUploads());
  }
});

// Periodic Background Sync - Intenta sincronizar cada cierto tiempo
self.addEventListener('periodicsync', (event) => {
  if (event.tag === 'periodic-sync-uploads') {
    event.waitUntil(syncPendingUploads());
  }
});

// Función para sincronizar uploads pendientes desde el service worker
async function syncPendingUploads() {
  try {
    // Abrir IndexedDB
    const db = await openDB();
    const tx = db.transaction(['pending_photos'], 'readonly');
    const store = tx.objectStore('pending_photos');
    const pending = await getAllFromStore(store);
    
    if (pending.length === 0) {
      console.log('No pending uploads to sync');
      return;
    }
    
    console.log(`Background sync: Processing ${pending.length} uploads...`);
    
    for (const item of pending) {
      try {
        const formData = new FormData();
        formData.append('valor_caudalimetro', item.valor_caudalimetro);
        formData.append('observaciones', item.observaciones || '');
        formData.append('csrfmiddlewaretoken', item.csrfToken);
        
        if (item.fileBlob) {
          formData.append('foto_evidencia', item.fileBlob, item.fileName);
        }
        
        const response = await fetch('/cargar/', {
          method: 'POST',
          body: formData,
          credentials: 'same-origin'
        });
        
        if (response.ok) {
          // Eliminar del storage
          const deleteTx = db.transaction(['pending_photos'], 'readwrite');
          const deleteStore = deleteTx.objectStore('pending_photos');
          await deleteStore.delete(item.id);
          
          console.log(`✓ Background synced item ${item.id}`);
          
          // Notificar al cliente
          self.clients.matchAll().then(clients => {
            clients.forEach(client => {
              client.postMessage({
                type: 'SYNC_SUCCESS',
                itemId: item.id,
                timestamp: item.timestamp
              });
            });
          });
        }
      } catch (error) {
        console.error(`Failed to sync item ${item.id}:`, error);
      }
    }
  } catch (error) {
    console.error('Background sync failed:', error);
    throw error; // Reintentará automáticamente
  }
}

// Helper functions para IndexedDB en service worker
function openDB() {
  return new Promise((resolve, reject) => {
    const request = indexedDB.open('UploadQueue', 1);
    request.onsuccess = () => resolve(request.result);
    request.onerror = () => reject(request.error);
  });
}

function getAllFromStore(store) {
  return new Promise((resolve, reject) => {
    const request = store.getAll();
    request.onsuccess = () => resolve(request.result);
    request.onerror = () => reject(request.error);
  });
}
