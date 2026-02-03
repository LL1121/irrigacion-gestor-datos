/**
 * Offline-First Upload System using IndexedDB
 * Handles image uploads with automatic queue processing when online
 */

const DB_NAME = 'UploadQueue';
const DB_VERSION = 1;
const STORE_NAME = 'pending_photos';
let db = null;

/**
 * Initialize IndexedDB database
 */
async function initDB() {
    return new Promise((resolve, reject) => {
        const request = indexedDB.open(DB_NAME, DB_VERSION);
        
        request.onerror = () => reject(request.error);
        request.onsuccess = () => {
            db = request.result;
            resolve(db);
        };
        
        request.onupgradeneeded = (event) => {
            const db = event.target.result;
            
            // Create object store if it doesn't exist
            if (!db.objectStoreNames.contains(STORE_NAME)) {
                const objectStore = db.createObjectStore(STORE_NAME, { 
                    keyPath: 'id', 
                    autoIncrement: true 
                });
                objectStore.createIndex('timestamp', 'timestamp', { unique: false });
                objectStore.createIndex('status', 'status', { unique: false });
            }
        };
    });
}

/**
 * Add upload to queue
 */
async function addToQueue(formData, fileBlob) {
    if (!db) await initDB();
    
    return new Promise((resolve, reject) => {
        const transaction = db.transaction([STORE_NAME], 'readwrite');
        const store = transaction.objectStore(STORE_NAME);
        
        const item = {
            valor_caudalimetro: formData.get('valor_caudalimetro'),
            observaciones: formData.get('observaciones'),
            csrfToken: formData.get('csrfmiddlewaretoken'),
            fileBlob: fileBlob,
            fileName: formData.get('foto_evidencia') ? formData.get('foto_evidencia').name : null,
            timestamp: new Date().toISOString(),
            status: 'pending'
        };
        
        const request = store.add(item);
        
        request.onsuccess = async () => {
            // Registrar background sync para sincronización automática
            if ('serviceWorker' in navigator && 'sync' in self.registration) {
                try {
                    await self.registration.sync.register('sync-uploads');
                    console.log('✓ Background sync registered for new upload');
                } catch (error) {
                    console.log('Could not register background sync:', error);
                }
            }
            resolve(request.result);
        };
        request.onerror = () => reject(request.error);
    });
}

/**
 * Get all pending uploads
 */
async function getPendingUploads() {
    if (!db) await initDB();
    
    return new Promise((resolve, reject) => {
        const transaction = db.transaction([STORE_NAME], 'readonly');
        const store = transaction.objectStore(STORE_NAME);
        const request = store.getAll();
        
        request.onsuccess = () => resolve(request.result);
        request.onerror = () => reject(request.error);
    });
}

/**
 * Delete upload from queue
 */
async function deleteFromQueue(id) {
    if (!db) await initDB();
    
    return new Promise((resolve, reject) => {
        const transaction = db.transaction([STORE_NAME], 'readwrite');
        const store = transaction.objectStore(STORE_NAME);
        const request = store.delete(id);
        
        request.onsuccess = () => resolve();
        request.onerror = () => reject(request.error);
    });
}

/**
 * Send form data to server
 */
async function sendToServer(formData) {
    console.log('Enviando POST a /cargar/...');
    try {
        const response = await fetch('/cargar/', {
            method: 'POST',
            body: formData,
            credentials: 'same-origin',
            headers: {
                'X-Requested-With': 'XMLHttpRequest',
                'Accept': 'application/json'
            }
        });
        
        console.log(`Response status: ${response.status}, url: ${response.url}`);
        
        if (!response.ok) {
            console.log('Server returned HTTP error!');
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        // Intentar parsear como JSON
        let data = null;
        try {
            data = await response.json();
            console.log('Response JSON:', data);
            
            // Verificar si la respuesta indica éxito
            if (data.success === false) {
                console.error('Server returned success: false', data.message);
                throw new Error(data.message || 'Server error');
            }
        } catch (jsonError) {
            // Si no es JSON válido, asumir que el redirect fue exitoso
            console.log('Response is not JSON (probably a redirect), assuming success');
        }
        
        console.log('Upload successful!');
        return response;
    } catch (error) {
        console.error('sendToServer error:', error.message);
        throw error;
    }
}

/**
 * Process upload queue - send all pending uploads to server
 */
async function processUploadQueue() {
    if (!navigator.onLine) {
        console.log('Still offline. Cannot process queue.');
        return;
    }
    
    try {
        const pendingUploads = await getPendingUploads();
        
        if (pendingUploads.length === 0) {
            console.log('No pending uploads in queue.');
            return;
        }
        
        console.log(`Processing ${pendingUploads.length} pending upload(s)...`);
        
        for (const item of pendingUploads) {
            try {
                // Reconstruct FormData (ubicacion_manual is now auto-assigned by backend from empresa_perfil)
                const formData = new FormData();
                formData.append('valor_caudalimetro', item.valor_caudalimetro);
                formData.append('observaciones', item.observaciones || '');
                formData.append('csrfmiddlewaretoken', item.csrfToken);
                
                if (item.fileBlob) {
                    formData.append('foto_evidencia', item.fileBlob, item.fileName);
                }
                
                // Send to server
                await sendToServer(formData);
                
                // Delete from queue on success
                await deleteFromQueue(item.id);
                
                console.log(`✓ Uploaded item ${item.id} successfully`);
                
                // Show success notification
                showNotification(
                    '¡Sincronizado!',
                    `Medición de ${item.timestamp.substring(0, 10)} subida exitosamente`,
                    'success'
                );
                
            } catch (error) {
                console.error(`Failed to upload item ${item.id}:`, error);
                
                // Don't delete from queue if upload fails
                showNotification(
                    'Error al sincronizar',
                    `No se pudo subir medición de ${item.timestamp.substring(0, 10)}. Se reintentará.`,
                    'error'
                );
            }
        }
        
        // Refresh page if all uploads were successful
        const remainingUploads = await getPendingUploads();
        if (remainingUploads.length === 0 && pendingUploads.length > 0) {
            setTimeout(() => {
                window.location.href = '/';
            }, 2000);
        }
        
    } catch (error) {
        console.error('Error processing upload queue:', error);
    }
}

/**
 * Show notification using SweetAlert2
 */
function showNotification(title, message, icon = 'info') {
    if (typeof Swal !== 'undefined') {
        Swal.fire({
            icon: icon,
            title: title,
            text: message,
            position: 'top-end',
            toast: true,
            showConfirmButton: false,
            timer: icon === 'success' ? 3000 : 5000,
            timerProgressBar: true
        });
    } else {
        alert(`${title}: ${message}`);
    }
}

/**
 * Initialize offline upload system
 */
async function initOfflineUpload() {
    try {
        // Initialize database
        await initDB();
        console.log('✓ IndexedDB initialized');
        
        // Register Background Sync for automatic upload
        if ('serviceWorker' in navigator) {
            try {
                const registration = await navigator.serviceWorker.ready;
                if ('sync' in registration) {
                    await registration.sync.register('sync-uploads');
                    console.log('✓ Background Sync registered');
                }
            } catch (error) {
                console.log('Background Sync not available:', error);
            }
        }
        
        // Register Periodic Background Sync (si está disponible)
        if ('serviceWorker' in navigator) {
            try {
                const registration = await navigator.serviceWorker.ready;
                if ('periodicSync' in registration) {
                    await registration.periodicSync.register('periodic-sync-uploads', {
                        minInterval: 60 * 60 * 1000 // 1 hora
                    });
                    console.log('✓ Periodic Background Sync registered');
                }
            } catch (error) {
                console.log('Periodic Background Sync not available:', error);
            }
        }
        
        // Add network status listeners
        window.addEventListener('online', async () => {
            console.log('✓ Connection restored. Triggering automatic sync...');
            
            // Intentar registrar background sync
            if ('serviceWorker' in navigator && 'sync' in self.registration) {
                await self.registration.sync.register('sync-uploads');
            } else {
                // Fallback: sincronizar directamente si background sync no está disponible
                await processUploadQueue();
            }
        });
        
        window.addEventListener('offline', () => {
            console.log('⚠ Connection lost. Uploads will be queued.');
            showNotification(
                'Sin conexión',
                'Las mediciones se guardarán localmente y se sincronizarán automáticamente',
                'warning'
            );
        });
        
        // Listen for sync messages from service worker
        if ('serviceWorker' in navigator) {
            navigator.serviceWorker.addEventListener('message', (event) => {
                if (event.data.type === 'SYNC_SUCCESS') {
                    showNotification(
                        '¡Sincronizado!',
                        `Medición sincronizada automáticamente`,
                        'success'
                    );
                }
            });
        }
        
        // Process queue on page load if online
        if (navigator.onLine) {
            await processUploadQueue();
        }
        
        console.log('✓ Offline upload system ready with automatic background sync');
        
    } catch (error) {
        console.error('Failed to initialize offline upload system:', error);
    }
}

/**
 * Update pending badge (if exists)
 */
async function updatePendingBadge() {
    try {
        const pendingCount = await getPendingCount();
        const badge = document.getElementById('pending-uploads-badge');
        if (badge) {
            if (pendingCount > 0) {
                badge.textContent = pendingCount;
                badge.style.display = 'inline-block';
            } else {
                badge.style.display = 'none';
            }
        }
    } catch (error) {
        console.log('Could not update pending badge:', error);
    }
}

/**
 * Get count of pending uploads
 */
async function getPendingCount() {
    try {
        const uploads = await getPendingUploads();
        return uploads.length;
    } catch (error) {
        console.log('Could not get pending count:', error);
        return 0;
    }
}

/**
 * Handle form submission with offline support
 */
async function handleFormSubmit(event, form) {
    console.log('handleFormSubmit called!');
    event.preventDefault();
    
    const formData = new FormData(form);
    
    const fileInput = form.querySelector('input[type="file"]');
    const fileBlob = fileInput && fileInput.files[0] ? fileInput.files[0] : null;
    
    // Check if online
    if (navigator.onLine) {
        try {
            // Send immediately
            showNotification(
                'Enviando...',
                'Guardando medición en el servidor',
                'info'
            );
            
            await sendToServer(formData);
            
            showNotification(
                '¡Éxito!',
                'Medición guardada correctamente',
                'success'
            );
            
            // Redirect to dashboard
            setTimeout(() => {
                window.location.href = '/';
            }, 1500);
            
        } catch (error) {
            console.error('Upload failed:', error);
            
            // If server fails but we're "online", queue it anyway
            showNotification(
                'Error de servidor',
                'Se guardará en cola para reintentar',
                'warning'
            );
            
            await addToQueue(formData, fileBlob);
            await updatePendingBadge();
            
            setTimeout(() => {
                window.location.href = '/';
            }, 2000);
        }
        
    } else {
        // Offline - queue for later
        try {
            await addToQueue(formData, fileBlob);
            await updatePendingBadge();
            
            showNotification(
                'Sin conexión',
                'Foto guardada en cola para subir luego',
                'info'
            );
            
            // Redirect to dashboard
            setTimeout(() => {
                window.location.href = '/';
            }, 2000);
            
        } catch (error) {
            console.error('Failed to queue upload:', error);
            showNotification(
                'Error',
                'No se pudo guardar la medición localmente',
                'error'
            );
        }
    }
}

// Export functions for use in other scripts
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        initDB,
        addToQueue,
        getPendingUploads,
        deleteFromQueue,
        processUploadQueue,
        initOfflineUpload,
        handleFormSubmit,
        getPendingCount,
        updatePendingBadge
    };
}
