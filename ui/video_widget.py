"""
Widget de video con integración de OpenCV y MediaPipe para pose detection
"""
import gi
gi.require_version('Gtk', '4.0')
gi.require_version('GObject', '2.0')

from gi.repository import Gtk, GLib, GdkPixbuf, Gdk, GObject
import cv2
import numpy as np
import threading
import time
from analysis.subprocess_pose_detector import SubprocessPoseDetector
from analysis.stance_analyzer import StanceAnalyzer


class VideoWidget(Gtk.Box):
    """Widget que maneja el video feed y pose detection"""
    
    __gsignals__ = {
        'pose-detected': (GObject.SignalFlags.RUN_FIRST, None, (object,)),
        'metrics-updated': (GObject.SignalFlags.RUN_FIRST, None, (object,)),
    }
    
    def __init__(self):
        super().__init__(orientation=Gtk.Orientation.VERTICAL)
        print("Inicializando VideoWidget...")
        
        # Estado
        self.camera = None
        self.running = False
        self.current_technique = "sanchin-dachi"  # Técnica por defecto
        self.current_category = "stances"
        self.capturing = False
        self.recording = False
        
        # Componentes de análisis
        self.stance_analyzer = StanceAnalyzer()
        
        # IMPORTANTE: No inicializar el detector aquí para evitar problemas con GTK
        # Se iniciará cuando la ventana esté completamente cargada
        self.pose_detector = None
        
        # Estado del procesamiento
        self.last_processed_frame = None
        self.overlay_enabled = True
        self.frame_skip_counter = 0
        self.last_frame_from_worker = None  # Para almacenar último frame del worker
        
        # Datos de referencia
        self.reference_data = None
        self.reference_landmarks = None
        self.show_reference_overlay = True
        
        # Estados para suavidad de pose
        self.last_pose_result = None
        self.last_pose_timestamp = time.time()
        self.pose_timeout = 0.5  # Reducido a 0.5 segundos para mayor responsividad
        
        # Setup UI
        self.setup_ui()
        print("UI configurada")
        
        # NO inicializar cámara inmediatamente - puede causar bloqueos
        # Se inicializará de forma asíncrona cuando la ventana esté lista
        print("VideoWidget inicializado (esperando worker para video)")
    
    def start_analysis_process(self):
        """
        Inicia el proceso de análisis de pose de forma completamente asíncrona.
        Este método es llamado desde la ventana principal cuando la UI ya está visible.
        """
        print("Iniciando el proceso de análisis de pose de forma asíncrona...")
        
        # Usar GLib.idle_add para hacer toda la inicialización en el siguiente ciclo
        # Esto evita que GTK se bloquee esperando a la cámara o al subproceso
        GLib.idle_add(self._async_start_everything)
    
    def process_frame(self, frame):
        """Procesa un frame y actualiza el overlay"""
        if self.pose_detector:
            pose_result = self.pose_detector.process_frame(frame)
            if pose_result:
                self.last_pose_result = pose_result
                self.last_pose_timestamp = time.time()

                # Enviar landmarks al StanceAnalyzer
                metrics = self.stance_analyzer.analyze(pose_result)
                self.emit('metrics-updated', metrics)

                # Dibujar overlay
                self.draw_overlay(frame, pose_result)

        return frame

    def draw_overlay(self, frame, pose_result):
        """Dibuja los landmarks en el frame"""
        for landmark in pose_result['landmarks']:
            x, y = int(landmark[0] * frame.shape[1]), int(landmark[1] * frame.shape[0])
            cv2.circle(frame, (x, y), 5, (0, 255, 0), -1)
    
    def _async_start_everything(self):
        """Inicia cámara y detector de forma asíncrona sin bloquear GTK"""
        try:
            print("Iniciando cámara de forma asíncrona...")
            
            # 1. Inicializar la cámara
            self.init_camera()
            
            print("Creando detector en proceso asíncrono...")
            
            # 2. Crear el detector si no existe
            if self.pose_detector is None:
                self.pose_detector = SubprocessPoseDetector()
            
            # 3. Iniciar el proceso sin esperar a que responda
            if self.pose_detector and not self.pose_detector.is_alive():
                self.pose_detector.start()
                print("Detector iniciado de forma asíncrona")
            
        except Exception as e:
            print(f"Error en inicialización asíncrona: {e}")
            import traceback
            traceback.print_exc()
        
        return False  # No repetir
            
    def setup_ui(self):
        """Configura la interfaz del widget de video"""
        
        # Contenedor principal con clase CSS
        self.add_css_class("video-container")
        
        # Imagen para mostrar el video
        self.video_image = Gtk.Picture()
        self.video_image.set_hexpand(True)
        self.video_image.set_vexpand(True)
        self.video_image.set_content_fit(Gtk.ContentFit.CONTAIN)
        
        # Overlay para countdown y métricas
        self.overlay = Gtk.Overlay()
        self.overlay.set_child(self.video_image)
        
        # Label para countdown
        self.countdown_label = Gtk.Label()
        self.countdown_label.set_markup('<span size="72000" weight="bold" color="red">3</span>')
        self.countdown_label.set_halign(Gtk.Align.CENTER)
        self.countdown_label.set_valign(Gtk.Align.CENTER)
        self.countdown_label.set_visible(False)
        self.overlay.add_overlay(self.countdown_label)
        
        # Label para métricas en tiempo real
        self.metrics_label = Gtk.Label()
        self.metrics_label.set_markup('<span size="small" color="white">Video: Activo</span>')
        self.metrics_label.set_halign(Gtk.Align.START)
        self.metrics_label.set_valign(Gtk.Align.START)
        self.metrics_label.set_margin_top(10)
        self.metrics_label.set_margin_start(10)
        self.overlay.add_overlay(self.metrics_label)
        
        # Label para estado de grabación
        self.recording_label = Gtk.Label()
        self.recording_label.set_markup('<span size="large" weight="bold" color="red">● REC</span>')
        self.recording_label.set_halign(Gtk.Align.END)
        self.recording_label.set_valign(Gtk.Align.START)
        self.recording_label.set_margin_top(10)
        self.recording_label.set_margin_end(10)
        self.recording_label.set_visible(False)
        self.overlay.add_overlay(self.recording_label)
        
        self.append(self.overlay)
        
        # Aplicar CSS
        self.apply_css()
    
    def apply_css(self):
        """Aplica estilos CSS al widget"""
        css_provider = Gtk.CssProvider()
        css = """
        .video-container {
            background-color: #000000;
            border-radius: 8px;
            margin: 10px;
        }
        """
        css_provider.load_from_data(css.encode())
        
        display = Gdk.Display.get_default()
        Gtk.StyleContext.add_provider_for_display(
            display, css_provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )
    
    def init_camera(self):
        """Ya no necesitamos cámara aquí - el worker la maneja directamente"""
        try:
            # Solo crear un frame dummy para mostrar algo inicial
            dummy_frame = np.zeros((480, 640, 3), dtype=np.uint8)
            cv2.putText(dummy_frame, "Conectando con detector...", 
                       (50, 240), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
            
            self.running = True
            
            # Timer para actualizar UI - MÁXIMA FLUIDEZ
            GLib.timeout_add(16, self.update_frame)  # ~60 FPS para máxima responsividad
            
            # Mostrar frame inicial
            self.update_video_display(dummy_frame)
            
            print("Sistema de video inicializado (esperando frames del worker)")
                
        except Exception as e:
            print(f"Error inicializando sistema de video: {e}")
    
    def update_frame(self):
        """Actualiza UI con frames y resultados del worker"""
        if not self.running:
            return False
        
        try:
            display_frame = None
            current_pose_result = None
            
            # Obtener TODOS los resultados disponibles para usar el más reciente
            if self.pose_detector:
                try:
                    # Leer todos los resultados disponibles para evitar lag
                    while True:
                        result = self.pose_detector.get_result()
                        if result is None:
                            break
                        current_pose_result = result  # Quedarse con el más reciente
                        # Actualizar timestamp y estado si tenemos resultado válido
                        if result.get('pose_detected'):
                            self.last_pose_result = result
                            self.last_pose_timestamp = time.time()
                    
                    # Si no tenemos resultado nuevo, usar el último válido si no ha expirado
                    if (current_pose_result is None and 
                        self.last_pose_result is not None and 
                        (time.time() - self.last_pose_timestamp) < self.pose_timeout):
                        current_pose_result = self.last_pose_result
                    
                    # Obtener frame desde memoria compartida
                    shared_frame, frame_counter = self.pose_detector.get_latest_frame()
                    
                    if shared_frame is not None:
                        # Usar frame de memoria compartida como base
                        base_frame = shared_frame.copy()
                        self.last_frame_from_worker = base_frame
                    elif self.last_frame_from_worker is not None:
                        # Usar último frame disponible
                        base_frame = self.last_frame_from_worker
                    else:
                        # Frame dummy si aún no tenemos frames
                        base_frame = np.zeros((480, 640, 3), dtype=np.uint8)
                        cv2.putText(base_frame, "Conectando...", 
                                   (250, 240), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
                    
                    # Escalar a tamaño de UI
                    display_frame = cv2.resize(base_frame, (640, 480))
                    
                    # Si hay resultado de pose, procesar landmarks
                    if current_pose_result:
                        # Si hay landmarks y overlay habilitado, dibujar con nivel de confianza
                        if (current_pose_result.get('pose_detected') and 
                            current_pose_result.get('landmarks') and 
                            self.overlay_enabled):
                            confidence = current_pose_result.get('pose_confidence', 'high')
                            display_frame = self._draw_pose_landmarks(display_frame, current_pose_result['landmarks'], confidence)
                            
                        # Añadir texto de estado con información de confianza y persistencia
                        confidence = current_pose_result.get('pose_confidence', 'unknown')
                        frames_since = current_pose_result.get('frames_since_detection', 0)
                        
                        if current_pose_result.get('pose_detected'):
                            if confidence == 'high':
                                status = "POSE DETECTADA"
                                color = (0, 255, 0)  # Verde brillante para detección real
                            elif confidence == 'interpolated':
                                status = f"POSE TRACKING ({frames_since})"
                                color = (0, 255, 255)  # Amarillo para interpolado reciente
                            elif confidence == 'fading':
                                status = f"POSE FADING ({frames_since})"
                                color = (0, 150, 255)  # Naranja para pose antigua
                            else:
                                status = "POSE DETECTADA"
                                color = (0, 200, 0)  # Verde más suave
                        else:
                            status = "Sin pose"
                            color = (0, 0, 255)  # Rojo
                        
                        cv2.putText(display_frame, status, (10, 30), 
                                   cv2.FONT_HERSHEY_SIMPLEX, 1, color, 2)
                        
                        # Añadir frame ID para debug
                        frame_id = current_pose_result.get('frame_id', 0)
                        cv2.putText(display_frame, f"Frame: {frame_id}", (10, 460), 
                                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
                        
                        # Emitir señal de pose detectada de forma asíncrona
                        GLib.idle_add(self._emit_pose_signal, current_pose_result)
                    else:
                        # Sin resultado de pose, mostrar video en vivo
                        cv2.putText(display_frame, "Video en vivo", (10, 30), 
                                   cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
                    
                except Exception as e:
                    print(f"Error procesando resultado: {e}")
                    pass  # Ignorar errores para evitar bloqueos
            
            # Si no tenemos frame, mostrar mensaje de espera
            if display_frame is None:
                display_frame = np.zeros((480, 640, 3), dtype=np.uint8)
                cv2.putText(display_frame, "Esperando detector...", 
                           (180, 240), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
            
            # Actualizar UI
            self.update_video_display(display_frame)
            
        except Exception as e:
            print(f"Error en update_frame: {e}")
        
        return True  # Continuar el timer
    
    def _emit_pose_signal(self, result):
        """Emite señal de pose de forma asíncrona"""
        try:
            self.emit('pose-detected', result)
            
            # Analizar stance si corresponde
            if (result.get('pose_detected') and 
                self.current_category == "stances" and 
                result.get('landmarks')):
                self.analyze_stance_from_landmarks(
                    result['landmarks'], 
                    result['processed_frame']
                )
        except:
            pass  # Ignorar errores
        
        return False  # No repetir
    
    def analyze_stance_from_landmarks(self, landmarks, frame):
        """Analiza stance desde landmarks deserializados"""
        if self.current_category != "stances" or not self.current_technique:
            return
        
        try:
            # Convertir landmarks de dict a objeto similar a MediaPipe
            landmark_objects = []
            for lm in landmarks:
                # Crear objeto simple con las propiedades necesarias
                class Landmark:
                    def __init__(self, x, y, z, visibility):
                        self.x = x
                        self.y = y
                        self.z = z
                        self.visibility = visibility
                
                landmark_objects.append(Landmark(lm['x'], lm['y'], lm['z'], lm['visibility']))
            
            # Analizar stance
            metrics = self.stance_analyzer.analyze_stance(
                self.current_technique, 
                landmark_objects
            )
            
            if metrics:
                print(f"Métricas calculadas: {metrics}")
                self.emit('metrics-updated', metrics)
                
        except Exception as e:
            print(f"Error analizando stance: {e}")
    
    def set_overlay_enabled(self, enabled):
        """Activa/desactiva el overlay de pose detection"""
        self.overlay_enabled = enabled
        print(f"Overlay: {'ON' if enabled else 'OFF'}")
    
    def draw_metrics_overlay(self, frame, metrics):
        """Dibuja métricas sobre el frame"""
        if not metrics:
            return frame
        
        y_offset = 30
        font = cv2.FONT_HERSHEY_SIMPLEX
        
        # Score general
        if 'score' in metrics:
            color = (0, 255, 0) if metrics['score'] >= 80 else (0, 255, 255) if metrics['score'] >= 60 else (0, 0, 255)
            cv2.putText(frame, f"Score: {metrics['score']:.0f}/100", 
                       (10, y_offset), font, 0.7, color, 2)
            y_offset += 30
        
        # Feedback principal
        if 'feedback' in metrics and metrics['feedback']:
            feedback_text = metrics['feedback'][0]  # Primer feedback
            cv2.putText(frame, feedback_text[:40], 
                       (10, y_offset), font, 0.5, (0, 255, 255), 1)
        
        return frame
    
    def _draw_pose_landmarks(self, frame, landmarks, confidence='high'):
        """Dibuja landmarks de pose con efectos visuales basados en confianza"""
        try:
            height, width = frame.shape[:2]
            
            # Primero dibujar la referencia si está disponible y habilitada
            if (self.reference_landmarks and self.show_reference_overlay and 
                self.overlay_enabled):
                frame = self._draw_reference_overlay(frame, self.reference_landmarks)
            
            # Ajustar opacidad y colores basado en confianza
            if confidence == 'high':
                alpha = 1.0
                line_thickness = 3
                point_radius_mult = 1.0
            elif confidence == 'interpolated':
                alpha = 0.8
                line_thickness = 2
                point_radius_mult = 0.9
            elif confidence == 'fading':
                alpha = 0.5
                line_thickness = 2
                point_radius_mult = 0.7
            else:
                alpha = 0.6
                line_thickness = 2
                point_radius_mult = 0.8
            
            # Preparar puntos para dibujo eficiente
            points = []
            for landmark in landmarks:
                if landmark['visibility'] > 0.3:  # Umbral más bajo para más puntos
                    x = int(landmark['x'] * width)
                    y = int(landmark['y'] * height)
                    points.append((x, y))
                else:
                    points.append(None)
            
            # Crear overlay para efectos de transparencia
            overlay = frame.copy()
            
            # Dibujar puntos con colores ajustados por confianza
            for i, point in enumerate(points):
                if point:
                    # Color basado en la importancia del landmark
                    if i in [11, 12, 23, 24]:  # Torso - azul
                        color = (255, 0, 0)
                        radius = int(6 * point_radius_mult)
                    elif i in [13, 14, 15, 16]:  # Brazos - verde
                        color = (0, 255, 0)
                        radius = int(5 * point_radius_mult)
                    elif i in [25, 26, 27, 28]:  # Piernas - rojo
                        color = (0, 0, 255)
                        radius = int(5 * point_radius_mult)
                    else:  # Otros - amarillo
                        color = (0, 255, 255)
                        radius = int(4 * point_radius_mult)
                    
                    cv2.circle(overlay, point, radius, color, -1)
            
            # Dibujar conexiones principales con grosor ajustado
            important_connections = [
                # Torso principal
                (11, 12), (11, 23), (12, 24), (23, 24),
                # Brazos principales  
                (11, 13), (13, 15), (12, 14), (14, 16),
                # Piernas principales
                (23, 25), (25, 27), (24, 26), (26, 28),
                # Cabeza principal
                (0, 1), (1, 2), (2, 3), (0, 4), (4, 5), (5, 6)
            ]
            
            for connection in important_connections:
                if (connection[0] < len(points) and connection[1] < len(points) and
                    points[connection[0]] and points[connection[1]]):
                    cv2.line(overlay, points[connection[0]], points[connection[1]], 
                            (0, 255, 255), line_thickness)  # Líneas amarillas
            
            # Aplicar overlay con transparencia
            cv2.addWeighted(overlay, alpha, frame, 1 - alpha, 0, frame)
            
            return frame
            
        except Exception as e:
            print(f"Error dibujando landmarks: {e}")
            return frame  # Devolver frame original en caso de error
    
    def _draw_reference_overlay(self, frame, reference_landmarks):
        """Dibuja la pose de referencia como overlay semitransparente"""
        try:
            height, width = frame.shape[:2]
            
            # Crear overlay para la referencia
            ref_overlay = frame.copy()
            
            # Manejar diferentes formatos de landmarks de referencia
            points = []
            
            # Si reference_landmarks es un diccionario (datos promedio o formato incorrecto)
            if isinstance(reference_landmarks, dict):
                # Verificar si es un formato incorrecto (un solo landmark promedio)
                if 'x' in reference_landmarks and 'y' in reference_landmarks:
                    print("Advertencia: Formato de referencia incorrecto detectado (landmarks promedio en lugar de lista)")
                    # No se puede dibujar un solo punto promedio, necesitamos 33 landmarks
                    return frame
                else:
                    # Convertir diccionario a lista de landmarks
                    landmark_list = []
                    # Asumiendo que las claves son índices de landmarks
                    for key in sorted(reference_landmarks.keys()):
                        if isinstance(key, str) and key.isdigit():
                            landmark_list.append(reference_landmarks[key])
                    reference_landmarks = landmark_list
            
            # Verificar que tenemos suficientes landmarks para dibujar
            if not reference_landmarks or len(reference_landmarks) < 10:
                print(f"Advertencia: Insuficientes landmarks de referencia ({len(reference_landmarks) if reference_landmarks else 0})")
                return frame
            
            # Procesar landmarks de referencia
            for i, landmark in enumerate(reference_landmarks):
                if isinstance(landmark, dict):
                    # Formato dict con x, y, z, visibility
                    if landmark.get('visibility', 0) > 0.5:
                        x = int(landmark['x'] * width)
                        y = int(landmark['y'] * height)
                        points.append((x, y))
                    else:
                        points.append(None)
                elif isinstance(landmark, (list, tuple)) and len(landmark) >= 2:
                    # Formato lista/tupla [x, y, ...]
                    x = int(landmark[0] * width)
                    y = int(landmark[1] * height)
                    points.append((x, y))
                else:
                    points.append(None)
            
            # Dibujar puntos de referencia con colores distintivos (magenta/morado)
            for i, point in enumerate(points):
                if point:
                    # Colores distintivos para la referencia
                    if i in [11, 12, 23, 24]:  # Torso - magenta claro
                        color = (255, 100, 255)
                        radius = 4
                    elif i in [13, 14, 15, 16]:  # Brazos - magenta
                        color = (200, 0, 200)
                        radius = 3
                    elif i in [25, 26, 27, 28]:  # Piernas - morado
                        color = (150, 0, 150)
                        radius = 3
                    else:  # Otros - magenta suave
                        color = (180, 100, 180)
                        radius = 2
                    
                    cv2.circle(ref_overlay, point, radius, color, -1)
            
            # Dibujar conexiones de referencia
            important_connections = [
                # Torso principal
                (11, 12), (11, 23), (12, 24), (23, 24),
                # Brazos principales  
                (11, 13), (13, 15), (12, 14), (14, 16),
                # Piernas principales
                (23, 25), (25, 27), (24, 26), (26, 28),
                # Cabeza principal
                (0, 1), (1, 2), (2, 3), (0, 4), (4, 5), (5, 6)
            ]
            
            for connection in important_connections:
                if (connection[0] < len(points) and connection[1] < len(points) and
                    points[connection[0]] and points[connection[1]]):
                    cv2.line(ref_overlay, points[connection[0]], points[connection[1]], 
                            (255, 150, 255), 2)  # Líneas magenta
            
            # Aplicar overlay de referencia con transparencia baja
            cv2.addWeighted(ref_overlay, 0.3, frame, 0.7, 0, frame)
            
            # Agregar texto indicando que es la referencia
            cv2.putText(frame, "REFERENCIA", (10, height - 20), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 150, 255), 2)
            
            return frame
            
        except Exception as e:
            print(f"Error dibujando overlay de referencia: {e}")
            return frame
    
    def update_video_display(self, frame):
        """Actualiza la imagen mostrada en la UI"""
        try:
            # Convertir BGR a RGB
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            
            # Asegurar que el frame sea contiguo en memoria
            rgb_frame = np.ascontiguousarray(rgb_frame)
            
            # Crear GdkPixbuf con datos copiados
            height, width, channels = rgb_frame.shape
            
            # Crear una copia de los datos para evitar problemas de threading
            data = rgb_frame.copy().tobytes()
            
            pixbuf = GdkPixbuf.Pixbuf.new_from_data(
                data,
                GdkPixbuf.Colorspace.RGB,
                False,
                8,
                width,
                height,
                width * channels
            )
            
            # Actualizar en el hilo principal de GTK
            if pixbuf:
                texture = Gdk.Texture.new_for_pixbuf(pixbuf)
                self.video_image.set_paintable(texture)
            
        except Exception as e:
            print(f"Error actualizando display: {e}")
    
    def set_active_technique(self, category, technique):
        """Establece la técnica activa desde el ControlPanel"""
        self.current_category = category
        self.current_technique = technique
        print(f"Técnica activa establecida: {category} -> {technique}")

    def set_active_reference(self, reference):
        """Establece la referencia activa desde el ControlPanel"""
        self.current_reference = reference
        print(f"Referencia activa establecida: {reference}")
    
    def start_capture(self, countdown):
        """Inicia captura de pose con countdown y calcula el promedio de 3 imágenes"""
        print(f"Iniciando captura: countdown={countdown}s")

        def capture_thread():
            # Mostrar countdown
            for i in range(countdown, 0, -1):
                GLib.idle_add(self.show_countdown, str(i))
                time.sleep(1)

            GLib.idle_add(self.hide_countdown)

            # Capturar 3 imágenes consecutivas
            captured_landmarks = []
            for _ in range(3):
                if self.last_pose_result:
                    captured_landmarks.append(self.last_pose_result['landmarks'])
                time.sleep(0.1)  # Pausa breve entre capturas

            # Calcular promedio de landmarks
            if captured_landmarks:
                averaged_landmarks = self.calculate_average_landmarks(captured_landmarks)
                self.save_captured_data(averaged_landmarks)
                print("Captura completada con promedio calculado")

        threading.Thread(target=capture_thread, daemon=True).start()

    def calculate_average_landmarks(self, landmarks_list):
        """Calcula el promedio de una lista de landmarks"""
        import numpy as np

        # Verificar que landmarks_list no esté vacío
        if not landmarks_list:
            raise ValueError("La lista de landmarks está vacía")

        # Cada elemento en landmarks_list debería ser una lista de 33 landmarks
        if not landmarks_list[0] or len(landmarks_list[0]) == 0:
            raise ValueError("Los landmarks están vacíos")

        num_landmarks = len(landmarks_list[0])  # Debería ser 33
        num_captures = len(landmarks_list)
        
        # Inicializar arrays para promediar
        averaged_landmarks = []
        
        # Calcular promedio para cada landmark (0-32)
        for landmark_idx in range(num_landmarks):
            x_values = []
            y_values = []
            z_values = []
            visibility_values = []
            
            # Recopilar valores de todas las capturas para este landmark
            for capture_landmarks in landmarks_list:
                if landmark_idx < len(capture_landmarks):
                    landmark = capture_landmarks[landmark_idx]
                    x_values.append(landmark['x'])
                    y_values.append(landmark['y'])
                    z_values.append(landmark['z'])
                    visibility_values.append(landmark['visibility'])
            
            # Calcular promedios
            avg_landmark = {
                'x': np.mean(x_values),
                'y': np.mean(y_values),
                'z': np.mean(z_values),
                'visibility': np.mean(visibility_values)
            }
            
            averaged_landmarks.append(avg_landmark)
        
        return averaged_landmarks

    def save_captured_data(self, averaged_landmarks):
        """Guarda los landmarks promedio y metadatos en un archivo JSON"""
        import json
        from datetime import datetime

        # Verificar que la técnica actual está configurada
        if not self.current_technique:
            print("Advertencia: Técnica no configurada, usando técnica por defecto 'sanchin-dachi'")
            self.current_technique = "sanchin-dachi"
            self.current_category = "stances"

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"data/references/captured_pose_{timestamp}.json"

        data = {
            "landmarks": averaged_landmarks,
            "timestamp": timestamp,
            "technique": self.current_technique,
            "category": self.current_category
        }

        with open(filename, 'w') as f:
            json.dump(data, f, indent=4)

        print(f"Datos capturados guardados en {filename}")
    
    def start_recording(self, countdown, duration):
        """Inicia grabación de kata/técnica con countdown"""
        print(f"Iniciando grabación: countdown={countdown}s, duration={duration}s")
        
        def recording_thread():
            # Mostrar countdown
            for i in range(countdown, 0, -1):
                GLib.idle_add(self.show_countdown, str(i))
                time.sleep(1)
            
            GLib.idle_add(self.hide_countdown)
            GLib.idle_add(self.show_recording_indicator)
            
            # Grabar por duration segundos
            self.recording = True
            time.sleep(duration)
            self.recording = False
            
            GLib.idle_add(self.hide_recording_indicator)
            print("Grabación completada")
        
        threading.Thread(target=recording_thread, daemon=True).start()
    
    def show_countdown(self, number):
        """Muestra número de countdown"""
        self.countdown_label.set_markup(
            f'<span size="72000" weight="bold" color="red">{number}</span>'
        )
        self.countdown_label.set_visible(True)
        return False
    
    def hide_countdown(self):
        """Oculta countdown"""
        self.countdown_label.set_visible(False)
        return False
    
    def show_recording_indicator(self):
        """Muestra indicador de grabación"""
        self.recording_label.set_visible(True)
        return False
    
    def hide_recording_indicator(self):
        """Oculta indicador de grabación"""
        self.recording_label.set_visible(False)
        return False
    
    def cleanup(self):
        """Limpia recursos al cerrar"""
        self.running = False
        
        # Detener el proceso de pose detection
        if self.pose_detector:
            self.pose_detector.stop()
        
        # Liberar cámara
        if self.camera:
            self.camera.release()

    def load_reference_json(self, filepath):
        """Carga un archivo JSON de referencia y calcula métricas"""
        import json

        try:
            # Leer el archivo JSON
            with open(filepath, 'r') as f:
                data = json.load(f)

            # Verificar que el archivo contiene landmarks
            if 'landmarks' not in data:
                raise ValueError("El archivo JSON no contiene landmarks")

            # Extraer landmarks y calcular métricas
            reference_landmarks = data['landmarks']
            metrics = self.stance_analyzer.analyze_stance(self.current_technique, [reference_landmarks])

            # Emitir las métricas calculadas
            if metrics:
                print(f"Métricas calculadas desde referencia: {metrics}")
                self.emit('metrics-updated', metrics)
            else:
                print("No se pudieron calcular métricas desde la referencia")

        except Exception as e:
            print(f"Error al cargar el archivo JSON de referencia: {e}")
    
    def on_technique_changed(self, combo):
        """Actualiza la técnica activa cuando se selecciona una nueva opción"""
        self.current_technique = combo.get_active_text()
        print(f"Técnica cambiada a: {self.current_technique}")
    
    def load_reference_data(self, reference_data):
        """Carga datos de referencia para mostrar overlay de comparación"""
        try:
            self.reference_data = reference_data
            self.reference_landmarks = reference_data.get('landmarks', [])
            
            technique = reference_data.get('technique', 'Desconocida')
            timestamp = reference_data.get('timestamp', 'Desconocido')
            
            print(f"Referencia cargada: {technique} (capturada: {timestamp})")
            print(f"Landmarks de referencia: {len(self.reference_landmarks) if isinstance(self.reference_landmarks, list) else 'datos de landmarks disponibles'}")
            
            # Si la referencia no coincide con la técnica actual, mostrar advertencia
            if technique != self.current_technique:
                print(f"Advertencia: Referencia es de '{technique}' pero técnica actual es '{self.current_technique}'")
            
        except Exception as e:
            print(f"Error cargando datos de referencia: {e}")
            self.reference_data = None
            self.reference_landmarks = None
# Registrar el tipo para señales
GObject.type_register(VideoWidget)
