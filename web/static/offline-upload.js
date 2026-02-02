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
        
        request.onsuccess = () => resolve(request.result);
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
    const response = await fetch('/cargar/', {
        method: 'POST',
        body: formData,
        credentials: 'same-origin'
    });
    
    if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
    }
    
    return response;
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
 * Get pending uploads count for UI badge
 */
async function getPendingCount() {
    try {
        const pending = await getPendingUploads();
        return pending.length;
    } catch (error) {
        console.error('Error getting pending count:', error);
        return 0;
    }
}

/**
 * Update UI to show pending uploads count
 */
async function updatePendingBadge() {
    const count = await getPendingCount();
    const badge = document.getElementById('pendingUploadsBadge');
    
    if (badge) {
        if (count > 0) {
            badge.textContent = count;
            badge.style.display = 'inline-block';
        } else {
            badge.style.display = 'none';
        }
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
        
        // Update pending badge
        await updatePendingBadge();
        
        // Add network status listeners
        window.addEventListener('online', async () => {
            console.log('✓ Connection restored. Processing upload queue...');
            showNotification(
                'Conexión restaurada',
                'Sincronizando mediciones pendientes...',
                'info'
            );
            await processUploadQueue();
            await updatePendingBadge();
        });
        
        window.addEventListener('offline', () => {
            console.log('⚠ Connection lost. Uploads will be queued.');
            showNotification(
                'Sin conexión',
                'Las mediciones se guardarán localmente',
                'warning'
            );
        });
        
        // Process queue on page load if online
        if (navigator.onLine) {
            await processUploadQueue();
        }
        
        console.log('✓ Offline upload system ready');
        
    } catch (error) {
        console.error('Failed to initialize offline upload system:', error);
    }
}

/**
 * Handle form submission with offline support
 */
async function handleFormSubmit(event, form) {
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
