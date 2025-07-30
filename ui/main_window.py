"""
Ventana principal de Kohai con layout de video + panel de control
"""
import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')

from gi.repository import Gtk, Adw, GLib
from .video_widget import VideoWidget
from .control_panel import ControlPanel


class KohaiMainWindow(Adw.ApplicationWindow):
    """Ventana principal de la aplicación Kohai"""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
        # Configuración básica de ventana - tamaño más razonable
        self.set_title("Kohai - Karate Motion Analysis")
        self.set_default_size(1000, 700)  # Tamaño más pequeño
        self.set_size_request(800, 600)   # Tamaño mínimo
        
        # IMPORTANTES: Configuraciones adicionales para garantizar visibilidad
        self.set_resizable(True)
        self.set_modal(False)
        
        # Crear layout principal
        self.setup_ui()
        
        # Conectar señales
        self.setup_signals()
        
        # Conectar al evento 'map' para iniciar el proceso de análisis
        # cuando la ventana esté lista para ser mostrada.
        # Esta es la forma más segura de evitar conflictos con la inicialización de GTK.
        self.connect('map', self.on_window_mapped)
    
    def setup_ui(self):
        """Configura la interfaz de usuario"""
        
        # Para AdwApplicationWindow, usamos ToolbarView en lugar de set_titlebar
        toolbar_view = Adw.ToolbarView()
        
        # Header bar
        header = Adw.HeaderBar()
        header.set_title_widget(Gtk.Label(label="Kohai - Análisis de Karate"))
        
        # Botón de menú hamburguesa
        menu_button = Gtk.MenuButton()
        menu_button.set_icon_name("open-menu-symbolic")
        menu_button.set_tooltip_text("Menú principal")
        header.pack_end(menu_button)
        
        # Crear menú simple
        popover = Gtk.PopoverMenu()
        menu_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        menu_box.set_margin_top(12)
        menu_box.set_margin_bottom(12)
        menu_box.set_margin_start(12)
        menu_box.set_margin_end(12)
        
        # Opciones del menú
        calibrate_btn = Gtk.Button(label="⚙️ Calibrar Cámara")
        calibrate_btn.add_css_class("flat")
        calibrate_btn.connect('clicked', self.on_calibrate_clicked)
        
        about_btn = Gtk.Button(label="ℹ️ Acerca de")
        about_btn.add_css_class("flat")
        about_btn.connect('clicked', self.on_about_clicked)
        
        quit_btn = Gtk.Button(label="❌ Salir")
        quit_btn.add_css_class("flat")
        quit_btn.connect('clicked', self.on_quit_clicked)
        
        menu_box.append(calibrate_btn)
        menu_box.append(Gtk.Separator())
        menu_box.append(about_btn)
        menu_box.append(Gtk.Separator())
        menu_box.append(quit_btn)
        
        popover.set_child(menu_box)
        menu_button.set_popover(popover)
        
        # Agregar header al toolbar view
        toolbar_view.add_top_bar(header)
        
        # Layout principal: Panel horizontal ajustable
        self.main_paned = Gtk.Paned(orientation=Gtk.Orientation.HORIZONTAL)
        self.main_paned.set_shrink_start_child(False)
        self.main_paned.set_shrink_end_child(False)
        self.main_paned.set_resize_start_child(True)
        self.main_paned.set_resize_end_child(False)
        
        # Widget de video (lado izquierdo)
        self.video_widget = VideoWidget()
        self.main_paned.set_start_child(self.video_widget)
        
        # Panel de control (lado derecho) - con scroll
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        scrolled.set_min_content_width(350)  # Ancho mínimo del panel
        scrolled.set_max_content_width(450)  # Ancho máximo del panel
        
        self.control_panel = ControlPanel()
        scrolled.set_child(self.control_panel)
        self.main_paned.set_end_child(scrolled)
        
        # Establecer contenido del toolbar view
        toolbar_view.set_content(self.main_paned)
        
        # Establecer posición inicial del divisor 
        GLib.idle_add(self.set_initial_paned_position)
        
        self.set_content(toolbar_view)
    
    def create_menu_model(self):
        """Crea el modelo de menú principal - TODO: Implementar para GTK4"""
        # TODO: Implementar menú apropiado para GTK4
        pass
    
    def setup_signals(self):
        """Configura las señales y callbacks"""
        
        # Conectar señales del panel de control al widget de video
        self.control_panel.connect('technique-changed', self.on_technique_changed)
        self.control_panel.connect('capture-requested', self.on_capture_requested)
        self.control_panel.connect('record-requested', self.on_record_requested)
        self.control_panel.connect('overlay-toggled', self.on_overlay_toggled)
        self.control_panel.connect('reference-loaded', self.on_reference_loaded)
        
        # Conectar señales del widget de video al panel de control
        self.video_widget.connect('pose-detected', self.on_pose_detected)
        self.video_widget.connect('metrics-updated', self.on_metrics_updated)
    
    def on_window_mapped(self, widget):
        """
        Se llama cuando la ventana se muestra por primera vez.
        Es el momento ideal para iniciar procesos en segundo plano de forma segura.
        """
        print("Ventana mapeada. Iniciando proceso de análisis de pose.")
        self.video_widget.start_analysis_process()
        
        # Asegurar que el VideoWidget tiene la técnica inicial del ControlPanel
        GLib.idle_add(self.sync_initial_technique)
        
        # Desconectar para que no se llame de nuevo si la ventana se oculta y se vuelve a mostrar.
        self.disconnect_by_func(self.on_window_mapped)
    
    def sync_initial_technique(self):
        """Sincroniza la técnica inicial del ControlPanel con el VideoWidget"""
        self.video_widget.set_active_technique(
            self.control_panel.current_category,
            self.control_panel.current_technique
        )
        print(f"Técnica inicial sincronizada: {self.control_panel.current_category} -> {self.control_panel.current_technique}")
        return False  # No repetir
        
    def set_initial_paned_position(self):
        """Establece la posición inicial del panel (75% video)"""
        width = self.get_allocated_width()
        if width > 0:
            # 75% para video, 25% para control panel
            self.main_paned.set_position(int(width * 0.75))
        return False  # No repetir el callback
    
    # Signal handlers
    def on_technique_changed(self, control_panel, category, technique):
        """Maneja el cambio de técnica seleccionada"""
        print(f"Técnica cambiada: {category} -> {technique}")
        self.video_widget.set_active_technique(category, technique)
    
    def on_capture_requested(self, control_panel, countdown, duration):
        """Maneja la solicitud de captura de pose"""
        print(f"Captura solicitada: countdown={countdown}s, duration={duration}s")
        self.video_widget.start_capture(countdown)
    
    def on_record_requested(self, control_panel, countdown, duration):
        """Maneja la solicitud de grabación de kata/técnica"""
        print(f"Grabación solicitada: countdown={countdown}s, duration={duration}s")
        self.video_widget.start_recording(countdown, duration)
    
    def on_pose_detected(self, video_widget, pose_data):
        """Maneja la detección de pose"""
        # Pasar datos de pose al panel de control para análisis
        self.control_panel.update_pose_status(pose_data)
    
    def on_metrics_updated(self, video_widget, metrics):
        """Maneja la actualización de métricas"""
        # Actualizar métricas en el panel de control
        self.control_panel.update_metrics(metrics)
    
    def on_overlay_toggled(self, control_panel, enabled):
        """Maneja el toggle del overlay de pose detection"""
        self.video_widget.set_overlay_enabled(enabled)
    
    def on_reference_loaded(self, control_panel, reference_data):
        """Maneja la carga de una referencia"""
        print(f"Referencia cargada en main window: {reference_data.get('technique', 'Desconocida')}")
        self.video_widget.load_reference_data(reference_data)
    
    # Menu callbacks
    def on_calibrate_clicked(self, button):
        """Callback para calibración"""
        print("Calibración solicitada")
        # TODO: Mostrar dialog de calibración
    
    def on_about_clicked(self, button):
        """Callback para 'Acerca de'"""
        dialog = Adw.AboutWindow()
        dialog.set_transient_for(self)
        dialog.set_application_name("Kohai")
        dialog.set_application_icon("applications-games")
        dialog.set_developer_name("Karate Analysis Team")
        dialog.set_version("1.0")
        dialog.set_comments("Sistema de análisis biomecánico para karate Goju-Ryu")
        dialog.set_website("https://github.com/tu-usuario/kohai")
        dialog.set_license_type(Gtk.License.MIT_X11)
        dialog.present()
    
    def on_quit_clicked(self, button):
        """Callback para salir"""
        self.video_widget.cleanup()
        self.close()
