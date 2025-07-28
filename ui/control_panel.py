"""
Panel de control lateral con categorías, técnicas, grabación y métricas
"""
import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
gi.require_version('GObject', '2.0')

from gi.repository import Gtk, Adw, GLib, GObject


class ControlPanel(Gtk.Box):
    """Panel de control lateral derecho con pestañas"""
    
    __gsignals__ = {
        'technique-changed': (GObject.SignalFlags.RUN_FIRST, None, (str, str)),
        'capture-requested': (GObject.SignalFlags.RUN_FIRST, None, (int, int)),
        'record-requested': (GObject.SignalFlags.RUN_FIRST, None, (int, int)),
        'overlay-toggled': (GObject.SignalFlags.RUN_FIRST, None, (bool,)),
    }
    
    def __init__(self):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        self.set_margin_top(10)
        self.set_margin_bottom(10)
        self.set_margin_start(10)
        self.set_margin_end(10)
        
        # Estado
        self.current_category = "stances"
        self.current_technique = "sanchin-dachi"
        
        # Datos de técnicas
        self.techniques_data = {
            "stances": [
                ("sanchin-dachi", "Sanchin-dachi"),
                ("zenkutsu-dachi", "Zenkutsu-dachi"),
                ("shiko-dachi", "Shiko-dachi"),
                ("neko-ashi-dachi", "Neko-ashi-dachi"),
            ],
            "golpes": [
                ("seiken-zuki", "Seiken-zuki"),
                ("gyaku-zuki", "Gyaku-zuki"),
                ("uraken-uchi", "Uraken-uchi"),
                ("shuto-uchi", "Shuto-uchi"),
            ],
            "patadas": [
                ("mae-geri", "Mae-geri"),
                ("yoko-geri", "Yoko-geri"),
                ("mawashi-geri", "Mawashi-geri"),
                ("kansetsu-geri", "Kansetsu-geri"),
            ],
            "bloqueos": [
                ("jodan-uke", "Jodan-uke"),
                ("chudan-uke", "Chudan-uke"),
                ("gedan-barai", "Gedan-barai"),
                ("shuto-uke", "Shuto-uke"),
            ],
            "katas": [
                ("sanchin", "Sanchin"),
                ("gekisai-dai-ichi", "Gekisai Dai Ichi"),
                ("saifa", "Saifa"),
                ("seiyunchin", "Seiyunchin"),
            ],
        }
        
        # Mapa de métricas a mostrar por cada stance
        self.stance_metric_map = {
            'sanchin-dachi': [
                ('stance_width_ratio', 'Ancho Stance', '{:.2f}x'),
                ('left_knee_angle', 'Rodilla Izq', '{:.1f}°'),
                ('right_knee_angle', 'Rodilla Der', '{:.1f}°'),
                ('knee_symmetry', 'Simetría', '{:.1f}°'),
            ],
            'zenkutsu-dachi': [
                ('stance_length_ratio', 'Largo Stance', '{:.2f}x'),
                ('front_knee_angle', 'Rodilla Frontal', '{:.1f}°'),
                ('back_knee_angle', 'Rodilla Trasera', '{:.1f}°'),
            ],
            'shiko-dachi': [
                ('stance_width_ratio', 'Ancho Stance', '{:.2f}x'),
                ('left_knee_angle', 'Rodilla Izq', '{:.1f}°'),
                ('right_knee_angle', 'Rodilla Der', '{:.1f}°'),
                ('left_foot_angle', 'Ángulo Pie Izq', '{:.1f}°'),
                ('right_foot_angle', 'Ángulo Pie Der', '{:.1f}°'),
            ],
            'neko-ashi-dachi': [
                ('stance_length_ratio', 'Largo Stance', '{:.2f}x'),
                ('front_knee_angle', 'Rodilla Frontal', '{:.1f}°'),
                ('back_knee_angle', 'Rodilla Trasera', '{:.1f}°'),
            ]
        }
        
        self.setup_ui()
    
    def setup_ui(self):
        """Configura la interfaz del panel de control con pestañas."""
        
        title = Gtk.Label()
        title.set_markup('<span size="medium" weight="bold">Panel de Control</span>')
        title.set_halign(Gtk.Align.START)
        title.set_margin_bottom(10)
        self.append(title)

        # Notebook para las pestañas
        self.notebook = Gtk.Notebook()
        self.notebook.set_tab_pos(Gtk.PositionType.TOP)
        self.append(self.notebook)

        # Crear y agregar las páginas
        self.notebook.append_page(self.create_setup_page(), Gtk.Label(label="🥋 Técnica"))
        self.notebook.append_page(self.create_record_page(), Gtk.Label(label="🎥 Grabar"))
        self.notebook.append_page(self.create_analyze_page(), Gtk.Label(label="📊 Analizar"))

    def create_setup_page(self):
        """Crea la página de 'Técnica'."""
        page = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=15)
        page.set_margin_top(10)
        page.set_margin_bottom(10)
        page.set_margin_start(10)
        page.set_margin_end(10)
        
        page.append(self.setup_category_section())
        page.append(self.setup_technique_section())
        
        return page

    def create_record_page(self):
        """Crea la página de 'Grabar'."""
        page = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=15)
        page.set_margin_top(10)
        page.set_margin_bottom(10)
        page.set_margin_start(10)
        page.set_margin_end(10)

        page.append(self.setup_recording_section())
        
        return page

    def create_analyze_page(self):
        """Crea la página de 'Analizar'."""
        page = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=15)
        page.set_margin_top(10)
        page.set_margin_bottom(10)
        page.set_margin_start(10)
        page.set_margin_end(10)

        page.append(self.setup_status_section())
        page.append(self.setup_metrics_section())
        page.append(self.setup_comparison_section())
        
        return page

    def setup_category_section(self):
        """Configura la sección de selección de categoría"""
        group = Adw.PreferencesGroup()
        group.set_title("Categoría")
        
        self.category_buttons = {}
        first_button = None
        
        categories = [
            ("stances", "🧘 Stances"),
            ("golpes", "👊 Golpes"),
            ("patadas", "🦵 Patadas"),
            ("bloqueos", "🛡️ Bloqueos"),
            ("katas", "🥋 Katas"),
        ]
        
        for category_id, category_label in categories:
            if first_button is None:
                button = Gtk.CheckButton()
                first_button = button
            else:
                button = Gtk.CheckButton()
                button.set_group(first_button)
            
            button.set_label(category_label)
            button.connect('toggled', self.on_category_changed, category_id)
            
            self.category_buttons[category_id] = button
            
            row = Adw.ActionRow()
            row.set_activatable_widget(button)
            row.add_prefix(button)
            group.add(row)
        
        self.category_buttons["stances"].set_active(True)
        
        return group
    
    def setup_technique_section(self):
        """Configura la sección de selección de técnica"""
        self.technique_group = Adw.PreferencesGroup()
        self.technique_group.set_title("Técnica")
        
        self.technique_dropdown = Gtk.DropDown()
        self.update_technique_dropdown()
        self.technique_dropdown.connect('notify::selected', self.on_technique_changed)
        
        row = Adw.ActionRow()
        row.set_title("Seleccionar")
        row.add_suffix(self.technique_dropdown)
        self.technique_group.add(row)
        
        return self.technique_group
    
    def setup_recording_section(self):
        """Configura la sección de controles de grabación"""
        group = Adw.PreferencesGroup()
        group.set_title("Controles")
        
        buttons_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        buttons_box.set_homogeneous(True)
        
        self.capture_button = Gtk.Button(label="📸 Capturar")
        self.capture_button.add_css_class("suggested-action")
        self.capture_button.connect('clicked', self.on_capture_clicked)
        buttons_box.append(self.capture_button)
        
        self.record_button = Gtk.Button(label="🎥 Grabar")
        self.record_button.add_css_class("destructive-action")
        self.record_button.connect('clicked', self.on_record_clicked)
        buttons_box.append(self.record_button)
        
        buttons_row = Adw.ActionRow()
        buttons_row.set_title("Acciones")
        buttons_row.add_suffix(buttons_box)
        group.add(buttons_row)
        
        timing_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        
        self.countdown_spin = Gtk.SpinButton()
        self.countdown_spin.set_range(1, 10)
        self.countdown_spin.set_value(3)
        self.countdown_spin.set_increments(1, 1)
        
        self.duration_spin = Gtk.SpinButton()
        self.duration_spin.set_range(1, 60)
        self.duration_spin.set_value(5)
        self.duration_spin.set_increments(1, 5)
        
        timing_box.append(Gtk.Label(label="Prep:"))
        timing_box.append(self.countdown_spin)
        timing_box.append(Gtk.Label(label="Dur:"))
        timing_box.append(self.duration_spin)
        
        timing_row = Adw.ActionRow()
        timing_row.set_title("Tiempos (s)")
        timing_row.add_suffix(timing_box)
        group.add(timing_row)
        
        return group
    
    def setup_status_section(self):
        """Configura la sección de estado y calibración"""
        group = Adw.PreferencesGroup()
        group.set_title("Estado")
        
        self.pose_status_label = Gtk.Label(label="Esperando pose...")
        self.pose_status_label.set_halign(Gtk.Align.START)
        
        status_row = Adw.ActionRow(title="Detección de Pose")
        status_row.add_suffix(self.pose_status_label)
        group.add(status_row)
        
        return group
    
    def setup_metrics_section(self):
        """Configura la sección de métricas en tiempo real"""
        self.metrics_group = Adw.PreferencesGroup()
        self.metrics_group.set_title("Métricas Live")
        
        self.score_label = Gtk.Label(label="--/100")
        self.score_label.set_halign(Gtk.Align.END)
        
        score_row = Adw.ActionRow(title="Score General")
        score_row.add_suffix(self.score_label)
        self.metrics_group.add(score_row)
        
        self.metrics_rows = []
        
        return self.metrics_group
    
    def setup_comparison_section(self):
        """Configura la sección de comparación y overlay"""
        group = Adw.PreferencesGroup()
        group.set_title("Comparación")
        
        self.overlay_switch = Gtk.Switch()
        self.overlay_switch.set_active(True)  # Activado por defecto
        self.overlay_switch.connect('notify::active', self.on_overlay_toggled)
        
        overlay_row = Adw.ActionRow(title="Mostrar Referencia", subtitle="Overlay de técnica ideal")
        overlay_row.add_suffix(self.overlay_switch)
        group.add(overlay_row)
        
        buttons_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        buttons_box.set_homogeneous(True)
        
        load_ref_button = Gtk.Button(label="📁 Cargar")
        load_ref_button.connect('clicked', self.on_load_reference_clicked)
        buttons_box.append(load_ref_button)
        
        save_ref_button = Gtk.Button(label="💾 Guardar")
        save_ref_button.connect('clicked', self.on_save_reference_clicked)
        buttons_box.append(save_ref_button)
        
        buttons_row = Adw.ActionRow(title="Referencias")
        buttons_row.add_suffix(buttons_box)
        group.add(buttons_row)
        
        auto_learn_button = Gtk.Button(label="🧠 Auto-Learn")
        auto_learn_button.connect('clicked', self.on_auto_learn_clicked)
        
        learn_row = Adw.ActionRow(title="Aprendizaje Automático")
        learn_row.add_suffix(auto_learn_button)
        group.add(learn_row)
        
        return group
    
    def update_technique_dropdown(self):
        """Actualiza el dropdown de técnicas según la categoría"""
        if not hasattr(self, 'technique_dropdown'):
            return
            
        techniques = self.techniques_data.get(self.current_category, [])
        
        string_list = Gtk.StringList()
        for _, display_name in techniques:
            string_list.append(display_name)
        
        self.technique_dropdown.set_model(string_list)
        if len(techniques) > 0:
            self.technique_dropdown.set_selected(0)
    
    # Signal handlers
    def on_category_changed(self, button, category_id):
        """Maneja el cambio de categoría"""
        if button.get_active():
            self.current_category = category_id
            self.update_technique_dropdown()
            self.emit_technique_changed()
    
    def on_technique_changed(self, dropdown, param):
        """Maneja el cambio de técnica"""
        selected = dropdown.get_selected()
        techniques = self.techniques_data.get(self.current_category, [])
        
        if selected < len(techniques):
            self.current_technique = techniques[selected][0]
            self.emit_technique_changed()
    
    def emit_technique_changed(self):
        """Emite señal de cambio de técnica"""
        self.emit('technique-changed', self.current_category, self.current_technique)
    
    def on_capture_clicked(self, button):
        """Maneja click en botón de captura"""
        countdown = int(self.countdown_spin.get_value())
        duration = int(self.duration_spin.get_value())
        self.emit('capture-requested', countdown, duration)
    
    def on_record_clicked(self, button):
        """Maneja click en botón de grabación"""
        countdown = int(self.countdown_spin.get_value())
        duration = int(self.duration_spin.get_value())
        self.emit('record-requested', countdown, duration)
    
    def on_calibrate_clicked(self, button):
        """Maneja click en botón de calibración"""
        # Lógica de calibración (placeholder)
        self.pose_status_label.set_label("Calibrando...")
        GLib.timeout_add_seconds(2, self.calibration_complete, None)
    
    def calibration_complete(self, user_data):
        """Completa el proceso de calibración"""
        self.pose_status_label.set_label("Calibración completa")
        return False  # Para eliminar el timeout
    
    def on_overlay_toggled(self, switch, param):
        """Maneja toggle del overlay"""
        active = switch.get_active()
        print(f"Overlay: {'ON' if active else 'OFF'}")
        self.emit('overlay-toggled', active)
    
    def on_load_reference_clicked(self, button):
        """Maneja carga de referencia"""
        print("Cargar referencia solicitado")
    
    def on_save_reference_clicked(self, button):
        """Maneja guardado como referencia"""
        print("Guardar referencia solicitado")
    
    def on_auto_learn_clicked(self, button):
        """Maneja auto-learning"""
        print("Auto-learning solicitado")
    
    def update_pose_status(self, pose_data):
        """Actualiza el estado de detección de pose"""
        if pose_data and pose_data.get('pose_detected'):
            self.pose_status_label.set_label("✓ Pose detectada")
            self.pose_status_label.add_css_class("success")
        else:
            self.pose_status_label.set_label("✗ Sin pose")
            self.pose_status_label.remove_css_class("success")
    
    def update_metrics(self, metrics):
        """Actualiza las métricas mostradas"""
        if not metrics:
            return
        
        if 'score' in metrics:
            self.score_label.set_label(f"{metrics['score']:.0f}/100")
        
        for row in self.metrics_rows:
            self.metrics_group.remove(row)
        self.metrics_rows.clear()
        
        # Usar el mapa de métricas para la técnica actual
        metric_items_to_display = []
        if self.current_category == "stances":
            metric_items_to_display = self.stance_metric_map.get(self.current_technique, [])

        # Si no es un stance o no está en el mapa, no mostrar métricas detalladas
        if not metric_items_to_display:
            return

        for metric_key, metric_title, format_string in metric_items_to_display:
            if metric_key in metrics:
                value_label = Gtk.Label(label=format_string.format(metrics[metric_key]))
                value_label.set_halign(Gtk.Align.END)
                
                row = Adw.ActionRow(title=metric_title)
                row.add_suffix(value_label)
                
                self.metrics_group.add(row)
                self.metrics_rows.append(row)

GObject.type_register(ControlPanel)
