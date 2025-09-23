/**
 * SlideMotion - Presentation Mode JavaScript
 * Maneja la lógica del modo presentación fullscreen con gestos y navegación
 */

class PresentationMode {
    constructor(config) {
        // Configuración inicial desde Django
        this.currentSlideNumber = config.currentSlideNumber;
        this.totalSlides = config.totalSlides;
        this.presentationId = config.presentationId;
        this.detailUrl = config.detailUrl;

        // Estado interno
        this.gesturesEnabled = false;
        this.gestureDetector = null;
        this.cameraManager = null;
        this.controlsVisible = false;
        this.controlsTimeout = null;
        this.cameraDebugVisible = false;

        // Referencias DOM
        this.initDOMReferences();

        // Inicializar
        this.init();
    }

    initDOMReferences() {
        this.slideContainer = document.getElementById('slide-container');
        this.currentSlideImg = document.getElementById('current-slide');
        this.controlsOverlay = document.getElementById('controls-overlay');
        this.currentSlideNumberEl = document.getElementById('current-slide-number');
        this.prevBtn = document.getElementById('prev-btn');
        this.nextBtn = document.getElementById('next-btn');
        this.gestureToggle = document.getElementById('gesture-toggle');
        this.gestureFeedback = document.getElementById('gesture-feedback');
        this.cameraOverlay = document.getElementById('camera-overlay');
        this.gestureCamera = document.getElementById('gesture-camera');
    }

    init() {
        this.setupEventListeners();
        this.showControlsTemporarily();
        console.log('Modo presentación inicializado - solo cámara visible');
    }

    setupEventListeners() {
        // Botones de navegación
        this.prevBtn.addEventListener('click', () => this.navigateSlide('prev'));
        this.nextBtn.addEventListener('click', () => this.navigateSlide('next'));

        // Toggle de gestos
        this.gestureToggle.addEventListener('click', () => this.toggleGestures());

        // Controles de teclado
        document.addEventListener('keydown', (e) => this.handleKeyNavigation(e));

        // Mostrar controles al mover mouse
        document.addEventListener('mousemove', () => this.showControlsTemporarily());

        // Ocultar controles al hacer click en slide
        this.slideContainer.addEventListener('click', () => this.hideControls());
    }

    async navigateSlide(direction) {
        let newSlideNumber = this.currentSlideNumber;

        if (direction === 'next' && this.currentSlideNumber < this.totalSlides) {
            newSlideNumber = this.currentSlideNumber + 1;
        } else if (direction === 'prev' && this.currentSlideNumber > 1) {
            newSlideNumber = this.currentSlideNumber - 1;
        } else {
            // Mostrar feedback cuando no se puede navegar
            if (direction === 'next' && this.currentSlideNumber >= this.totalSlides) {
                this.showGestureFeedback('🏁 Final de la presentación', 'warning');
            } else if (direction === 'prev' && this.currentSlideNumber <= 1) {
                this.showGestureFeedback('⏮️ Inicio de la presentación', 'warning');
            }
            return; // No navigation needed
        }

        try {
            // Usar fetch para cargar nuevo slide
            const response = await fetch(`/presentar/${this.presentationId}/slide/${newSlideNumber}/`);

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            const data = await response.json();
            this.updateSlide(data);

            // Mostrar feedback de éxito con dirección
            if (direction === 'next') {
                this.showGestureFeedback('Siguiente slide →', 'success');
            } else if (direction === 'prev') {
                this.showGestureFeedback('← Slide anterior', 'success');
            }

            console.log(`Navegado a slide ${newSlideNumber}`);

        } catch (error) {
            console.error('Error navegando slide:', error);
            this.showGestureFeedback('Error de navegación', 'error');
        }
    }

    updateSlide(slideData) {
        // Actualizar imagen del slide con transición
        this.currentSlideImg.style.opacity = '0';

        setTimeout(() => {
            this.currentSlideImg.src = slideData.slide_image_url;
            this.currentSlideImg.alt = `Slide ${slideData.slide_number}`;
            this.currentSlideNumber = slideData.slide_number;
            this.currentSlideNumberEl.textContent = slideData.slide_number;

            // Fade in
            this.currentSlideImg.style.opacity = '1';
        }, 150);

        // Actualizar estado de botones
        this.prevBtn.disabled = !slideData.has_previous;
        this.nextBtn.disabled = !slideData.has_next;
    }

    handleKeyNavigation(event) {
        switch(event.key) {
            case 'ArrowRight':
            case ' ': // Spacebar
                event.preventDefault();
                this.navigateSlide('next');
                break;
            case 'ArrowLeft':
                event.preventDefault();
                this.navigateSlide('prev');
                break;
            case 'Escape':
                event.preventDefault();
                window.location.href = this.detailUrl;
                break;
            case 'g':
            case 'G':
                event.preventDefault();
                this.toggleGestures();
                break;
        }
    }

    async toggleGestures() {
        if (!this.gesturesEnabled) {
            try {
                // Inicializar detección de gestos (cámara en background)
                await this.initializeGesturesInBackground();
                this.gesturesEnabled = true;
                this.gestureToggle.textContent = '⏹️ Detener Gestos';
                this.gestureToggle.classList.remove('bg-green-600', 'hover:bg-green-700');
                this.gestureToggle.classList.add('bg-red-600', 'hover:bg-red-700');

                // Mostrar cámara
                this.cameraOverlay.style.display = 'block';
                this.cameraOverlay.style.opacity = '1';

                this.showGestureFeedback('Gestos activados. Mueve los brazos para navegar', 'success');
            } catch (error) {
                console.error('Error activando gestos:', error);
                this.showGestureFeedback('Error activando gestos', 'error');
            }
        } else {
            // Detener gestos
            this.stopGestures();
            this.gesturesEnabled = false;
            this.gestureToggle.textContent = '🤚 Activar Gestos';
            this.gestureToggle.classList.remove('bg-red-600', 'hover:bg-red-700');
            this.gestureToggle.classList.add('bg-green-600', 'hover:bg-green-700');

            // Limpiar landmarks y ocultar cámara
            this.clearLandmarksCanvas();
            this.cameraOverlay.style.opacity = '0';
            setTimeout(() => {
                this.cameraOverlay.style.display = 'none';
            }, 300); // Esperar a que termine la transición

            this.showGestureFeedback('Gestos desactivados', 'info');
        }
    }

    async initializeGesturesInBackground() {
        // Esperar a que MediaPipe esté disponible
        await this.waitForMediaPipe();

        // Inicializar clases
        this.gestureDetector = new GestureDetector();
        this.cameraManager = new CameraManager();

        // Configurar callbacks
        this.gestureDetector.onGestureDetected = (gestureData) => this.handleGestureDetected(gestureData);
        this.gestureDetector.onPoseDetected = (landmarks) => this.handlePoseDetected(landmarks);
        this.gestureDetector.onError = (error) => this.handleGestureError(error);

        // Inicializar cámara (funcionará en background aunque no se vea)
        await this.cameraManager.startCamera(null, this.gestureCamera);

        // Iniciar detección
        await this.gestureDetector.startDetection(this.gestureCamera);

        console.log('Gestos inicializados en background - cámara mediana funcional');
    }

    // Función legacy mantenida por compatibilidad
    async initializeGestures() {
        await this.initializeGesturesInBackground();
    }

    stopGestures() {
        if (this.gestureDetector) {
            this.gestureDetector.stopDetection();
        }
        if (this.cameraManager) {
            this.cameraManager.stopCamera();
        }
    }

    handleGestureDetected(gestureData) {
        console.log('Gesto detectado en presentación:', gestureData);

        // Navegar según el gesto (navigateSlide ya maneja el feedback)
        if (gestureData.type === 'next_slide') {
            this.navigateSlide('next');
        } else if (gestureData.type === 'prev_slide') {
            this.navigateSlide('prev');
        }
    }

    handlePoseDetected(landmarks) {
        // Dibujar landmarks siempre que los gestos estén activos
        if (this.gesturesEnabled) {
            this.drawPoseOnCanvas(landmarks);
        }
    }

    drawPoseOnCanvas(landmarks) {
        const canvas = document.getElementById('gesture-canvas');
        const ctx = canvas.getContext('2d');

        // Ajustar tamaño del canvas al video
        if (this.gestureCamera.videoWidth && this.gestureCamera.videoHeight) {
            canvas.width = this.gestureCamera.videoWidth;
            canvas.height = this.gestureCamera.videoHeight;
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
                ctx.arc(x, y, 4, 0, 2 * Math.PI);
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

    handleGestureError(error) {
        console.error('Error de gesto:', error);
        this.showGestureFeedback('Error de detección', 'error');
    }

    showGestureFeedback(message, type = 'info') {
        this.gestureFeedback.textContent = message;
        this.gestureFeedback.className = `gesture-feedback show ${type}`;

        setTimeout(() => {
            this.gestureFeedback.classList.remove('show');
        }, 2000);
    }

    showControlsTemporarily() {
        this.controlsVisible = true;
        this.controlsOverlay.style.opacity = '1';
        this.controlsOverlay.style.pointerEvents = 'auto';

        // Cancelar timeout anterior
        if (this.controlsTimeout) {
            clearTimeout(this.controlsTimeout);
        }

        // Ocultar después de 3 segundos
        this.controlsTimeout = setTimeout(() => {
            this.hideControls();
        }, 3000);
    }

    hideControls() {
        this.controlsVisible = false;
        this.controlsOverlay.style.opacity = '0';
        this.controlsOverlay.style.pointerEvents = 'none';
    }

    toggleCameraDebug() {
        if (!this.gesturesEnabled) {
            this.showGestureFeedback('Primero activa los gestos (G)', 'info');
            return;
        }

        if (this.cameraDebugVisible) {
            this.hideCameraDebug();
        } else {
            this.showCameraDebug();
        }
    }

    showCameraDebug() {
        this.cameraDebugVisible = true;
        // Hacer la cámara grande y mostrar landmarks
        this.cameraOverlay.style.width = '256px';
        this.cameraOverlay.style.height = '192px';
        this.cameraOverlay.style.opacity = '1';
        // El canvas de landmarks se dibuja automáticamente
        this.showGestureFeedback('Debug activado: puntos verdes muestran detección de brazos', 'info');
    }

    hideCameraDebug() {
        this.cameraDebugVisible = false;
        // Cámara mediana pero sin landmarks visibles
        this.cameraOverlay.style.width = '128px';
        this.cameraOverlay.style.height = '96px';
        this.cameraOverlay.style.opacity = '0.8';
        // Limpiar canvas de landmarks
        this.clearLandmarksCanvas();
    }

    clearLandmarksCanvas() {
        const canvas = document.getElementById('gesture-canvas');
        if (canvas) {
            const ctx = canvas.getContext('2d');
            ctx.clearRect(0, 0, canvas.width, canvas.height);
        }
    }

    captureSnapshot() {
        if (!this.gestureCamera || this.gestureCamera.videoWidth === 0) {
            return; // Cámara no está lista
        }

        // Crear canvas temporal para capturar frame
        const canvas = document.createElement('canvas');
        const ctx = canvas.getContext('2d');

        // Configurar tamaño del canvas
        canvas.width = this.gestureCamera.videoWidth;
        canvas.height = this.gestureCamera.videoHeight;

        // Dibujar frame actual del video
        ctx.drawImage(this.gestureCamera, 0, 0);

        // Convertir a imagen y mostrar
        const dataURL = canvas.toDataURL('image/jpeg', 0.8);
        cameraSnapshot.src = dataURL;
    }

    // Función auxiliar para esperar MediaPipe
    waitForMediaPipe() {
        return new Promise((resolve, reject) => {
            let attempts = 0;
            const maxAttempts = 50;

            const checkMediaPipe = () => {
                if (window.FilesetResolver && window.PoseLandmarker) {
                    resolve();
                } else if (attempts < maxAttempts) {
                    attempts++;
                    setTimeout(checkMediaPipe, 100);
                } else {
                    reject(new Error('MediaPipe no se cargó'));
                }
            };

            checkMediaPipe();
        });
    }
}

// Funciones globales para compatibilidad (legacy)
let presentationMode = null;

function initializePresentationMode(config) {
    presentationMode = new PresentationMode(config);
}

// Exportar para uso global
window.PresentationMode = PresentationMode;
window.initializePresentationMode = initializePresentationMode;