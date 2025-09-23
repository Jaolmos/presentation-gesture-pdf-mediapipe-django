/**
 * SlideMotion - Camera Configuration JavaScript
 * Maneja la configuración de cámara y pruebas de gestos
 */

class CameraConfigManager {
    constructor() {
        // Instancias de clases
        this.gestureDetector = null;
        this.cameraManager = null;
        this.cameraConfig = null;

        // Referencias DOM
        this.initDOMReferences();

        // Contador de gestos
        this.gestureCount = 0;

        // Inicializar cuando el DOM esté listo
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', () => this.init());
        } else {
            this.init();
        }
    }

    initDOMReferences() {
        this.cameraSelect = document.getElementById('cameraSelect');
        this.sensitivitySlider = document.getElementById('sensitivity');
        this.startCameraBtn = document.getElementById('startCameraBtn');
        this.stopCameraBtn = document.getElementById('stopCameraBtn');
        this.testGesturesBtn = document.getElementById('testGesturesBtn');
        this.cameraVideo = document.getElementById('cameraVideo');
        this.poseCanvas = document.getElementById('poseCanvas');
        this.cameraOverlay = document.getElementById('cameraOverlay');

        // Estados
        this.cameraStatus = document.getElementById('cameraStatus');
        this.detectionStatus = document.getElementById('detectionStatus');
        this.gestureCountEl = document.getElementById('gestureCount');
        this.lastGestureEl = document.getElementById('lastGesture');
        this.gestureTimeEl = document.getElementById('gestureTime');
    }

    async init() {
        try {
            // Debug: Verificar qué variables están disponibles después de cargar MediaPipe
            this.debugMediaPipeVariables();

            // Esperar a que MediaPipe esté disponible
            await this.waitForMediaPipe();
            await this.initializePage();
        } catch (error) {
            console.error('Error inicializando configuración de cámara:', error);
            alert('Error de inicialización: ' + error.message);
        }
    }

    debugMediaPipeVariables() {
        console.log('Variables globales disponibles:');
        console.log('FilesetResolver:', typeof FilesetResolver);
        console.log('PoseLandmarker:', typeof PoseLandmarker);
        console.log('vision:', typeof vision);
        console.log('window.vision:', typeof window.vision);
        console.log('Todas las keys de window que contienen "mediapipe", "vision", "pose":',
            Object.keys(window).filter(key =>
                key.toLowerCase().includes('mediapipe') ||
                key.toLowerCase().includes('vision') ||
                key.toLowerCase().includes('pose')
            )
        );
    }

    // Función para esperar a que MediaPipe esté disponible
    waitForMediaPipe() {
        return new Promise((resolve, reject) => {
            let attempts = 0;
            const maxAttempts = 50; // 5 segundos máximo

            const checkMediaPipe = () => {
                if (window.FilesetResolver && window.PoseLandmarker) {
                    console.log('MediaPipe cargado correctamente');
                    resolve();
                } else if (attempts < maxAttempts) {
                    attempts++;
                    setTimeout(checkMediaPipe, 100);
                } else {
                    reject(new Error('MediaPipe no se cargó después de 5 segundos'));
                }
            };

            checkMediaPipe();
        });
    }

    async initializePage() {
        try {
            // Inicializar clases
            this.gestureDetector = new GestureDetector();
            this.cameraManager = new CameraManager();
            this.cameraConfig = new CameraConfig();

            // Configurar callbacks del detector de gestos
            this.gestureDetector.onGestureDetected = (gestureData) => this.handleGestureDetected(gestureData);
            this.gestureDetector.onPoseDetected = (landmarks) => this.handlePoseDetected(landmarks);
            this.gestureDetector.onError = (error) => this.handleDetectionError(error);

            // Cargar configuración guardada
            this.loadSavedConfig();

            // Detectar cámaras disponibles
            await this.detectCameras();

            // Configurar event listeners
            this.setupEventListeners();

            console.log('Página de configuración inicializada correctamente');

        } catch (error) {
            console.error('Error inicializando página:', error);
            alert('Error de inicialización: ' + error.message);
        }
    }

    loadSavedConfig() {
        const config = this.cameraConfig.load();

        // Aplicar configuración a UI
        this.sensitivitySlider.value = config.sensitivity;

        // Aplicar configuración al detector
        if (this.gestureDetector) {
            this.gestureDetector.setSensitivity(config.sensitivity);
        }

        console.log('Configuración cargada:', config);
    }

    saveConfig() {
        const config = {
            sensitivity: parseFloat(this.sensitivitySlider.value),
            selectedCamera: this.cameraSelect.value
        };

        this.cameraConfig.save(config);

        // Aplicar nueva sensibilidad al detector
        if (this.gestureDetector) {
            this.gestureDetector.setSensitivity(config.sensitivity);
        }
    }

    async detectCameras() {
        try {
            this.cameraSelect.innerHTML = '<option value="">Detectando cámaras...</option>';

            const devices = await this.cameraManager.detectCameras();

            // Limpiar opciones
            this.cameraSelect.innerHTML = '';

            if (devices.length === 0) {
                this.cameraSelect.innerHTML = '<option value="">No se encontraron cámaras</option>';
                return;
            }

            // Añadir opciones de cámara
            devices.forEach((device, index) => {
                const option = document.createElement('option');
                option.value = device.deviceId;
                option.textContent = device.label || `Cámara ${index + 1}`;
                this.cameraSelect.appendChild(option);
            });

            // Seleccionar cámara guardada si existe
            const savedConfig = this.cameraConfig.load();
            if (savedConfig.selectedCamera) {
                this.cameraSelect.value = savedConfig.selectedCamera;
            }

            console.log(`${devices.length} cámaras detectadas`);

        } catch (error) {
            console.error('Error detectando cámaras:', error);
            this.cameraSelect.innerHTML = '<option value="">Error: Permisos de cámara denegados</option>';
        }
    }

    setupEventListeners() {
        this.startCameraBtn.addEventListener('click', () => this.startCamera());
        this.stopCameraBtn.addEventListener('click', () => this.stopCamera());
        this.testGesturesBtn.addEventListener('click', () => this.toggleGestureDetection());

        // Guardar configuración cuando cambie
        this.sensitivitySlider.addEventListener('input', () => this.saveConfig());
        this.cameraSelect.addEventListener('change', () => this.saveConfig());
    }

    async startCamera() {
        try {
            const deviceId = this.cameraSelect.value;
            if (!deviceId) {
                alert('Por favor selecciona una cámara');
                return;
            }

            await this.cameraManager.startCamera(deviceId, this.cameraVideo);

            // Actualizar UI
            this.cameraOverlay.style.display = 'none';
            this.startCameraBtn.disabled = true;
            this.stopCameraBtn.disabled = false;
            this.testGesturesBtn.disabled = false;

            this.updateCameraStatus('Conectada', true);

            console.log('Cámara iniciada correctamente');

        } catch (error) {
            console.error('Error iniciando cámara:', error);
            alert('Error al iniciar la cámara: ' + error.message);
        }
    }

    stopCamera() {
        // Detener detección si está activa
        if (this.gestureDetector && this.gestureDetector.isDetecting) {
            this.toggleGestureDetection();
        }

        // Detener cámara
        this.cameraManager.stopCamera();

        // Actualizar UI
        this.cameraOverlay.style.display = 'flex';
        this.startCameraBtn.disabled = false;
        this.stopCameraBtn.disabled = true;
        this.testGesturesBtn.disabled = true;

        this.updateCameraStatus('No conectada', false);

        console.log('Cámara detenida');
    }

    async toggleGestureDetection() {
        try {
            if (!this.gestureDetector.isDetecting) {
                // Iniciar detección
                await this.gestureDetector.startDetection(this.cameraVideo);

                this.testGesturesBtn.textContent = '⏹️ Detener Gestos';
                this.updateDetectionStatus('Activa', true);

            } else {
                // Detener detección
                this.gestureDetector.stopDetection();

                this.testGesturesBtn.textContent = '🤚 Probar Gestos';
                this.updateDetectionStatus('Inactiva', false);

                // Limpiar canvas
                const ctx = this.poseCanvas.getContext('2d');
                ctx.clearRect(0, 0, this.poseCanvas.width, this.poseCanvas.height);
            }

        } catch (error) {
            console.error('Error en detección de gestos:', error);
            alert('Error en detección de gestos: ' + error.message);
        }
    }

    // Callbacks para eventos de detección
    handleGestureDetected(gestureData) {
        this.gestureCount++;
        this.gestureCountEl.textContent = this.gestureCount;
        this.lastGestureEl.textContent = gestureData.description;
        this.gestureTimeEl.textContent = 'ahora';

        console.log('Gesto detectado:', gestureData);

        // Aquí se podría enviar el gesto a la presentación
        // TODO: Integrar con sistema de navegación de slides
    }

    handlePoseDetected(landmarks) {
        // Opcional: Dibujar pose en canvas
        this.drawPoseOnCanvas(landmarks);
    }

    handleDetectionError(error) {
        console.error('Error de detección:', error);
        this.updateDetectionStatus('Error: ' + error, false);
    }

    // Utilidades de UI
    updateCameraStatus(text, isActive) {
        this.cameraStatus.textContent = text;
        if (isActive) {
            this.cameraStatus.classList.add('text-green-600');
        } else {
            this.cameraStatus.classList.remove('text-green-600');
        }
    }

    updateDetectionStatus(text, isActive) {
        this.detectionStatus.textContent = text;
        if (isActive) {
            this.detectionStatus.classList.add('text-green-600');
        } else {
            this.detectionStatus.classList.remove('text-green-600');
        }
    }

    drawPoseOnCanvas(landmarks) {
        const canvas = this.poseCanvas;
        const ctx = canvas.getContext('2d');

        // Ajustar tamaño del canvas al video
        if (this.cameraVideo.videoWidth && this.cameraVideo.videoHeight) {
            canvas.width = this.cameraVideo.videoWidth;
            canvas.height = this.cameraVideo.videoHeight;
        }

        // Limpiar canvas
        ctx.clearRect(0, 0, canvas.width, canvas.height);

        // Dibujar landmarks principales (hombros, codos, muñecas)
        const keyPoints = [11, 12, 13, 14, 15, 16]; // Landmarks de brazos

        ctx.fillStyle = '#00ff00';
        ctx.strokeStyle = '#00ff00';
        ctx.lineWidth = 2;

        keyPoints.forEach(index => {
            const landmark = landmarks[index];
            if (landmark) {
                const x = landmark.x * canvas.width;
                const y = landmark.y * canvas.height;

                // Dibujar punto
                ctx.beginPath();
                ctx.arc(x, y, 5, 0, 2 * Math.PI);
                ctx.fill();
            }
        });

        // Dibujar conexiones de brazos
        this.drawConnection(ctx, landmarks, 11, 13, canvas); // Hombro izq -> Codo izq
        this.drawConnection(ctx, landmarks, 13, 15, canvas); // Codo izq -> Muñeca izq
        this.drawConnection(ctx, landmarks, 12, 14, canvas); // Hombro der -> Codo der
        this.drawConnection(ctx, landmarks, 14, 16, canvas); // Codo der -> Muñeca der
    }

    drawConnection(ctx, landmarks, fromIndex, toIndex, canvas) {
        const from = landmarks[fromIndex];
        const to = landmarks[toIndex];

        if (from && to) {
            ctx.beginPath();
            ctx.moveTo(from.x * canvas.width, from.y * canvas.height);
            ctx.lineTo(to.x * canvas.width, to.y * canvas.height);
            ctx.stroke();
        }
    }
}

// Inicializar cuando se carga la página
let cameraConfigManager = null;

// Función de inicialización para compatibilidad
function initializeCameraConfig() {
    if (!cameraConfigManager) {
        cameraConfigManager = new CameraConfigManager();
    }
    return cameraConfigManager;
}

// Exportar para uso global
window.CameraConfigManager = CameraConfigManager;
window.initializeCameraConfig = initializeCameraConfig;

// Auto-inicializar
window.addEventListener('load', function() {
    initializeCameraConfig();
});