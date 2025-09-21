
/**
 * Gestión de detección de gestos con MediaPipe tasks-vision (PoseLandmarker)
 * SlideMotion - Control de presentaciones por gestos
 */

class GestureDetector {
    constructor() {
        this.poseLandmarker = null;
        this.isInitialized = false;
        this.isDetecting = false;
        this.lastGestureTime = 0;
        this.gestureThreshold = 1500; // ms entre gestos (1.5 segundos para evitar spam)

        // Estado para evitar detecciones repetidas
        this.lastGestureType = null;
        this.armNeutralRequired = false;

        // Configuración de sensibilidad
        this.armRaisedThreshold = 0.3; // Diferencia Y entre hombro y codo
        this.confidenceThreshold = 0.7;

        // Callbacks
        this.onGestureDetected = null;
        this.onPoseDetected = null;
        this.onError = null;
    }

    /**
     * Inicializa MediaPipe tasks-vision PoseLandmarker
     */
    async initialize() {
        try {
            console.log('Inicializando MediaPipe tasks-vision PoseLandmarker...');

            // Verificar que FilesetResolver esté disponible
            if (typeof window.FilesetResolver === 'undefined') {
                throw new Error('MediaPipe tasks-vision no está cargado. Verifica que el CDN esté incluido.');
            }

            // Crear FilesetResolver para tasks-vision
            const vision = await window.FilesetResolver.forVisionTasks(
                "https://cdn.jsdelivr.net/npm/@mediapipe/tasks-vision@latest/wasm"
            );

            // Crear PoseLandmarker con configuración
            this.poseLandmarker = await window.PoseLandmarker.createFromOptions(vision, {
                baseOptions: {
                    modelAssetPath: "https://storage.googleapis.com/mediapipe-models/pose_landmarker/pose_landmarker_lite/float16/1/pose_landmarker_lite.task",
                    delegate: "GPU"
                },
                runningMode: "VIDEO",
                numPoses: 1,
                minPoseDetectionConfidence: this.confidenceThreshold,
                minPosePresenceConfidence: this.confidenceThreshold,
                minTrackingConfidence: this.confidenceThreshold
            });

            this.isInitialized = true;
            console.log('PoseLandmarker inicializado correctamente');

        } catch (error) {
            console.error('Error inicializando PoseLandmarker:', error);
            if (this.onError) {
                this.onError('Error de inicialización: ' + error.message);
            }
            throw error;
        }
    }

    /**
     * Inicia la detección de gestos en video
     */
    async startDetection(videoElement) {
        if (!this.isInitialized) {
            await this.initialize();
        }

        this.isDetecting = true;
        this.lastVideoTime = -1;

        // Iniciar loop de detección
        this.detectLoop(videoElement);
    }

    /**
     * Detiene la detección de gestos
     */
    stopDetection() {
        this.isDetecting = false;
        console.log('Detección de gestos detenida');
    }

    /**
     * Loop principal de detección
     */
    detectLoop(videoElement) {
        if (!this.isDetecting || !videoElement) {
            return;
        }

        // Procesar frame solo si el tiempo ha cambiado
        if (videoElement.currentTime !== this.lastVideoTime) {
            this.lastVideoTime = videoElement.currentTime;

            try {
                // Detectar pose en el frame actual
                const results = this.poseLandmarker.detectForVideo(
                    videoElement,
                    performance.now()
                );

                // Procesar resultados
                this.processPoseResults(results);

            } catch (error) {
                console.error('Error en detección:', error);
            }
        }

        // Continuar loop
        if (this.isDetecting) {
            requestAnimationFrame(() => this.detectLoop(videoElement));
        }
    }

    /**
     * Procesa los resultados de detección de pose
     */
    processPoseResults(results) {
        if (!results || !results.landmarks || results.landmarks.length === 0) {
            return;
        }

        const landmarks = results.landmarks[0]; // Primera pose detectada

        // Callback para pose detectada (opcional)
        if (this.onPoseDetected) {
            this.onPoseDetected(landmarks);
        }

        // Detectar gestos específicos
        this.detectArmGestures(landmarks);
    }

    /**
     * Detecta gestos de brazos levantados
     */
    detectArmGestures(landmarks) {
        const now = Date.now();

        // Evitar detecciones muy frecuentes
        if (now - this.lastGestureTime < this.gestureThreshold) {
            return;
        }

        // Landmarks de brazos (según MediaPipe tasks-vision)
        const leftShoulder = landmarks[11];   // Hombro izquierdo
        const rightShoulder = landmarks[12];  // Hombro derecho
        const leftElbow = landmarks[13];      // Codo izquierdo
        const rightElbow = landmarks[14];     // Codo derecho
        const leftWrist = landmarks[15];      // Muñeca izquierda
        const rightWrist = landmarks[16];     // Muñeca derecha

        // Verificar si los landmarks esenciales están presentes
        if (!leftShoulder || !rightShoulder || !leftElbow || !rightElbow) {
            return;
        }

        // Verificar que el cuerpo esté a distancia apropiada y completo
        if (!this.isBodyAtCorrectDistance(landmarks)) {
            return;
        }

        // Detectar brazo derecho levantado (con muñeca si está disponible)
        const rightArmRaised = this.isArmRaised(rightShoulder, rightElbow, rightWrist);

        // Detectar brazo izquierdo levantado (con muñeca si está disponible)
        const leftArmRaised = this.isArmRaised(leftShoulder, leftElbow, leftWrist);

        // Estado neutral: ningún brazo levantado
        const neutralState = !rightArmRaised && !leftArmRaised;

        // Si estamos en posición neutral, permitir nuevos gestos
        if (neutralState && this.armNeutralRequired) {
            this.armNeutralRequired = false;
            this.lastGestureType = null;
        }

        // Procesar gestos detectados solo si no requerimos posición neutral
        if (!this.armNeutralRequired) {
            if (rightArmRaised && !leftArmRaised && this.lastGestureType !== 'next_slide') {
                this.triggerGesture('next_slide', 'Brazo derecho levantado');
                this.armNeutralRequired = true;
            } else if (leftArmRaised && !rightArmRaised && this.lastGestureType !== 'prev_slide') {
                this.triggerGesture('prev_slide', 'Brazo izquierdo levantado');
                this.armNeutralRequired = true;
            }
        }
    }

    /**
     * Verifica si el cuerpo está a la distancia correcta y completamente visible
     */
    isBodyAtCorrectDistance(landmarks) {
        // Landmarks de brazos completos
        const leftShoulder = landmarks[11];  // Hombro izquierdo
        const rightShoulder = landmarks[12]; // Hombro derecho
        const leftElbow = landmarks[13];     // Codo izquierdo
        const rightElbow = landmarks[14];    // Codo derecho
        const leftWrist = landmarks[15];     // Muñeca izquierda
        const rightWrist = landmarks[16];    // Muñeca derecha

        // 1. Verificar que ambos brazos estén completos (hombro-codo-muñeca)
        const leftArmComplete = leftShoulder && leftElbow && leftWrist;
        const rightArmComplete = rightShoulder && rightElbow && rightWrist;

        if (!leftArmComplete || !rightArmComplete) {
            return false; // Brazos incompletos
        }

        // 2. Verificar que los hombros no ocupen más del 70% del ancho (no muy cerca)
        const shoulderWidth = Math.abs(rightShoulder.x - leftShoulder.x);
        if (shoulderWidth > 0.7) {
            return false; // Muy cerca: hombros muy anchos
        }

        // 3. Verificar que los brazos tengan espacio para moverse (no cortados)
        const leftArmSpace = leftWrist.x > 0.05; // Margen izquierdo
        const rightArmSpace = rightWrist.x < 0.95; // Margen derecho

        if (!leftArmSpace || !rightArmSpace) {
            return false; // Brazos cortados en los bordes
        }

        return true; // Brazos completos y distancia correcta
    }

    /**
     * Determina si un brazo está levantado (algoritmo mejorado)
     */
    isArmRaised(shoulder, elbow, wrist = null) {
        // Algoritmo mejorado: codo Y muñeca deben estar por encima del hombro
        const elbowAboveShoulder = shoulder.y - elbow.y > this.armRaisedThreshold;

        if (!elbowAboveShoulder) {
            return false; // Si codo no está arriba del hombro, no es gesto válido
        }

        if (wrist) {
            // También verificar que muñeca esté por encima del hombro
            const wristAboveShoulder = shoulder.y - wrist.y > this.armRaisedThreshold;
            if (!wristAboveShoulder) {
                return false; // Si muñeca no está arriba del hombro, no es gesto válido
            }
        }

        // Si llegamos aquí, el brazo está realmente levantado
        const basicRaised = true;

        // Algoritmo 2: Ángulo del brazo (más robusto)
        let angleRaised = false;
        if (wrist) {
            // Calcular ángulo del antebrazo respecto a la horizontal
            const forearmDx = wrist.x - elbow.x;
            const forearmDy = wrist.y - elbow.y;
            const forearmAngle = Math.atan2(forearmDy, forearmDx) * (180 / Math.PI);

            // Si el antebrazo apunta hacia arriba (ángulo negativo en coordenadas de imagen)
            angleRaised = forearmAngle < -30; // Brazo levantado si ángulo < -30°
        }

        // Algoritmo 3: Threshold más permisivo
        const relaxedThreshold = this.armRaisedThreshold * 0.7;
        const relaxedRaised = yDifference > relaxedThreshold;

        // Combinar algoritmos: si cualquiera detecta, considerarlo levantado
        return basicRaised || angleRaised || relaxedRaised;
    }

    /**
     * Dispara un evento de gesto detectado
     */
    triggerGesture(gestureType, gestureDescription) {
        const now = Date.now();
        this.lastGestureTime = now;
        this.lastGestureType = gestureType;

        const gestureData = {
            type: gestureType,
            description: gestureDescription,
            timestamp: now
        };

        console.log('Gesto detectado:', gestureData);

        // Callback para gesto detectado
        if (this.onGestureDetected) {
            this.onGestureDetected(gestureData);
        }
    }

    /**
     * Configura la sensibilidad de detección
     */
    setSensitivity(sensitivity) {
        // Convertir sensibilidad (0.1 - 1.0) a threshold de manera invertida
        // Sensibilidad alta = threshold bajo = más fácil detectar
        this.armRaisedThreshold = 0.35 - (sensitivity * 0.25); // Rango 0.35 - 0.1
        this.confidenceThreshold = Math.max(0.5, sensitivity);

        console.log('Sensibilidad actualizada:', {
            sensitivity: sensitivity,
            armRaisedThreshold: this.armRaisedThreshold.toFixed(3),
            confidenceThreshold: this.confidenceThreshold
        });
    }

    /**
     * Obtiene estadísticas de detección
     */
    getStats() {
        return {
            isInitialized: this.isInitialized,
            isDetecting: this.isDetecting,
            lastGestureTime: this.lastGestureTime,
            armRaisedThreshold: this.armRaisedThreshold,
            confidenceThreshold: this.confidenceThreshold
        };
    }
}

/**
 * Utilidad para gestión de configuración en localStorage
 */
class CameraConfig {
    constructor() {
        this.CONFIG_KEY = 'slidemotion_camera_config';
        this.defaultConfig = {
            sensitivity: 0.7,
            selectedCamera: '',
            gestureThreshold: 300,
            timestamp: 0
        };
    }

    /**
     * Carga configuración guardada
     */
    load() {
        try {
            const saved = localStorage.getItem(this.CONFIG_KEY);
            if (saved) {
                const config = JSON.parse(saved);
                return { ...this.defaultConfig, ...config };
            }
        } catch (error) {
            console.error('Error cargando configuración:', error);
        }
        return this.defaultConfig;
    }

    /**
     * Guarda configuración
     */
    save(config) {
        try {
            const configToSave = {
                ...this.load(),
                ...config,
                timestamp: Date.now()
            };
            localStorage.setItem(this.CONFIG_KEY, JSON.stringify(configToSave));
            console.log('Configuración guardada:', configToSave);
            return true;
        } catch (error) {
            console.error('Error guardando configuración:', error);
            return false;
        }
    }

    /**
     * Borra configuración
     */
    clear() {
        localStorage.removeItem(this.CONFIG_KEY);
        console.log('Configuración borrada');
    }
}

/**
 * Utilidades para gestión de cámaras
 */
class CameraManager {
    constructor() {
        this.stream = null;
        this.devices = [];
    }

    /**
     * Detecta cámaras disponibles
     */
    async detectCameras() {
        try {
            // Solicitar permisos primero
            const tempStream = await navigator.mediaDevices.getUserMedia({ video: true });
            tempStream.getTracks().forEach(track => track.stop());

            // Obtener dispositivos
            const devices = await navigator.mediaDevices.enumerateDevices();
            this.devices = devices.filter(device => device.kind === 'videoinput');

            console.log(`${this.devices.length} cámaras detectadas`);
            return this.devices;

        } catch (error) {
            console.error('Error detectando cámaras:', error);
            throw error;
        }
    }

    /**
     * Inicia cámara específica
     */
    async startCamera(deviceId, videoElement) {
        try {
            if (this.stream) {
                this.stopCamera();
            }

            const constraints = {
                video: {
                    deviceId: deviceId ? { exact: deviceId } : undefined,
                    width: { ideal: 1280 },
                    height: { ideal: 720 },
                    frameRate: { ideal: 30 }
                }
            };

            this.stream = await navigator.mediaDevices.getUserMedia(constraints);
            videoElement.srcObject = this.stream;

            console.log('Cámara iniciada correctamente');
            return true;

        } catch (error) {
            console.error('Error iniciando cámara:', error);
            throw error;
        }
    }

    /**
     * Detiene cámara actual
     */
    stopCamera() {
        if (this.stream) {
            this.stream.getTracks().forEach(track => track.stop());
            this.stream = null;
            console.log('Cámara detenida');
        }
    }

    /**
     * Verifica si hay cámara activa
     */
    isActive() {
        return this.stream !== null;
    }
}

// Exportar clases para uso global
window.GestureDetector = GestureDetector;
window.CameraConfig = CameraConfig;
window.CameraManager = CameraManager;