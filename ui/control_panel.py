"""
Panel de control lateral con categorías, técnicas, grabación y métricas
"""
import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
gi.require_version('GObject', '2.0')

from gi.repository import Gtk, Adw, GLib, GObject, Gio


class ControlPanel(Gtk.Box):
    """Panel de control lateral derecho con pestañas"""
    
    __gsignals__ = {
        'technique-changed': (GObject.SignalFlags.RUN_FIRST, None, (str, str)),
        'capture-requested': (GObject.SignalFlags.RUN_FIRST, None, (int, int)),
        'record-requested': (GObject.SignalFlags.RUN_FIRST, None, (int, int)),
        'overlay-toggled': (GObject.SignalFlags.RUN_FIRST, None, (bool,)),
        'reference-loaded': (GObject.SignalFlags.RUN_FIRST, None, (object,)),
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
        
        # Emitir señal inicial para establecer la técnica por defecto
        GLib.idle_add(self.emit_technique_changed)
    
    def setup_ui(self):
        """Configura la interfaz del panel de control con técnicas en la parte superior."""
        # Sección de selección de técnicas (fuera de pestañas)
        self.append(self.setup_technique_selection())

        # Notebook para las pestañas (Métricas primero, luego Captura)
        self.notebook = Gtk.Notebook()
        self.notebook.set_tab_pos(Gtk.PositionType.TOP)
        self.notebook.set_margin_top(10)
        self.append(self.notebook)

        # Agregar primero la página de Métricas, luego la de Captura
        self.notebook.append_page(self.create_analyze_page(), Gtk.Label(label="📊 Métricas"))
        self.notebook.append_page(self.create_record_page(), Gtk.Label(label="🎥 Capturar"))
        # Establecer la página de Métricas como la página por defecto
        self.notebook.set_current_page(0)

    def setup_technique_selection(self):
        """Configura la sección de selección de técnicas en la parte superior"""
        group = Adw.PreferencesGroup()
        group.set_title("⚙️ Técnica Activa")
        
        # Dropdown para categorías
        self.category_dropdown = Gtk.DropDown()
        self.category_dropdown.set_size_request(200, -1)  # Hacer más ancho
        self.setup_category_dropdown()
        self.category_dropdown.connect('notify::selected', self.on_category_dropdown_changed)
        
        category_row = Adw.ActionRow()
        category_row.set_title("📂 Categoría")
        category_row.add_suffix(self.category_dropdown)
        group.add(category_row)
        
        # Dropdown para técnicas específicas
        self.technique_dropdown = Gtk.DropDown()
        self.technique_dropdown.set_size_request(200, -1)  # Hacer más ancho
        self.update_technique_dropdown()
        self.technique_dropdown.connect('notify::selected', self.on_technique_changed)
        
        technique_row = Adw.ActionRow()
        technique_row.set_title("🎯 Técnica")
        technique_row.add_suffix(self.technique_dropdown)
        group.add(technique_row)
        
        return group
    
    def setup_category_dropdown(self):
        """Configura el dropdown de categorías"""
        categories = [
            ("stances", "🧘 Posiciones"),
            ("golpes", "👊 Golpes"),
            ("patadas", "🦵 Patadas"),
            ("bloqueos", "🛡️ Bloqueos"),
            ("katas", "🥋 Katas"),
        ]
        
        string_list = Gtk.StringList()
        self.category_list = []  # Para mapear índices a IDs
        
        for category_id, display_name in categories:
            string_list.append(display_name)
            self.category_list.append(category_id)
        
        self.category_dropdown.set_model(string_list)
        self.category_dropdown.set_selected(0)  # Seleccionar stances por defecto

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

    def setup_recording_section(self):
        """Configura la sección de controles de grabación en una sola fila horizontal y compacta"""
        group = Adw.PreferencesGroup()
        group.set_title("🎬 Controles de Captura")

        # Botones de acción
        actions_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        actions_box.set_homogeneous(True)
        self.capture_button = Gtk.Button(label="📸 Capturar")
        self.capture_button.add_css_class("suggested-action")
        self.capture_button.set_tooltip_text("Captura una pose individual para análisis")
        self.capture_button.connect('clicked', self.on_capture_clicked)
        actions_box.append(self.capture_button)
        self.record_button = Gtk.Button(label="🎥 Grabar")
        self.record_button.add_css_class("destructive-action")
        self.record_button.set_tooltip_text("Graba una secuencia de movimientos")
        self.record_button.connect('clicked', self.on_record_clicked)
        actions_box.append(self.record_button)

        # Controles de tiempo
        timing_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        timing_box.set_homogeneous(False)
        timing_box.append(Gtk.Label(label="Prep:"))
        self.countdown_spin = Gtk.SpinButton()
        self.countdown_spin.set_range(1, 10)
        self.countdown_spin.set_value(3)
        self.countdown_spin.set_increments(1, 1)
        self.countdown_spin.set_tooltip_text("Tiempo de preparación antes de la captura")
        timing_box.append(self.countdown_spin)
        timing_box.append(Gtk.Label(label="Dur:"))
        self.duration_spin = Gtk.SpinButton()
        self.duration_spin.set_range(1, 60)
        self.duration_spin.set_value(5)
        self.duration_spin.set_increments(1, 5)
        self.duration_spin.set_tooltip_text("Duración de la grabación en segundos")
        timing_box.append(self.duration_spin)

        # Layout horizontal y compacto
        main_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=20)
        main_box.set_homogeneous(False)
        main_box.append(actions_box)
        main_box.append(timing_box)
        group.add(main_box)
        return group
    
    def setup_status_section(self):
        """Configura la sección de estado y calibración"""
        group = Adw.PreferencesGroup()
        group.set_title("📡 Estado del Sistema")
        
        self.pose_status_label = Gtk.Label(label="Esperando pose...")
        self.pose_status_label.set_halign(Gtk.Align.START)
        
        status_row = Adw.ActionRow(title="🔍 Detección de Pose")
        status_row.add_suffix(self.pose_status_label)
        group.add(status_row)
        
        return group
    
    def setup_metrics_section(self):
        """Configura la sección de métricas en tiempo real"""
        self.metrics_group = Adw.PreferencesGroup()
        self.metrics_group.set_title("📈 Análisis en Tiempo Real")
        
        self.score_label = Gtk.Label(label="--/100")
        self.score_label.set_halign(Gtk.Align.END)
        
        score_row = Adw.ActionRow(title="🏆 Puntuación General")
        score_row.add_suffix(self.score_label)
        self.metrics_group.add(score_row)
        
        self.metrics_rows = []
        
        return self.metrics_group
    
    def setup_comparison_section(self):
        """Configura la sección de comparación y overlay"""
        group = Adw.PreferencesGroup()
        group.set_title("🔍 Sistema de Referencia")
        
        self.overlay_switch = Gtk.Switch()
        self.overlay_switch.set_active(True)  # Activado por defecto
        self.overlay_switch.connect('notify::active', self.on_overlay_toggled)
        
        overlay_row = Adw.ActionRow(title="👁️ Mostrar Referencia")
        overlay_row.add_suffix(self.overlay_switch)
        group.add(overlay_row)
        
        buttons_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        buttons_box.set_homogeneous(True)
        
        # Botón para cargar referencia
        load_ref_button = Gtk.Button(label="📁 Cargar Referencia")
        load_ref_button.set_tooltip_text("Cargar técnica de referencia guardada")
        load_ref_button.connect('clicked', self.on_load_reference_clicked)
        buttons_box.append(load_ref_button)
        
        save_ref_button = Gtk.Button(label="💾 Guardar")
        save_ref_button.set_tooltip_text("Guardar técnica actual como referencia")
        save_ref_button.connect('clicked', self.on_save_reference_clicked)
        buttons_box.append(save_ref_button)
        
        buttons_row = Adw.ActionRow(title="📚 Gestión de Referencias")
        buttons_row.add_suffix(buttons_box)
        group.add(buttons_row)
        
        auto_learn_button = Gtk.Button(label="🧠 Auto-Learn")
        auto_learn_button.set_tooltip_text("Entrenar el sistema automáticamente")
        auto_learn_button.connect('clicked', self.on_auto_learn_clicked)
        
        learn_row = Adw.ActionRow(title="🤖 Aprendizaje Automático")
        learn_row.add_suffix(auto_learn_button)
        group.add(learn_row)
        
        return group
    
    # === ACTUALIZACIONES DE UI ===

    def update_pose_status(self, pose_data):
        """Actualiza el label de estado de la pose."""
        def _update():
            if not pose_data:
                status_text = '<span color="orange">Desconectado</span>'
            elif pose_data.get('pose_detected'):
                confidence = pose_data.get('pose_confidence', 'unknown')
                if confidence == 'high':
                    status_text = '<span color="green"><b>Detectada</b></span>'
                elif confidence == 'interpolated':
                    status_text = '<span color="yellow">Tracking...</span>'
                elif confidence == 'fading':
                    status_text = '<span color="orange">Perdiendo...</span>'
                else:
                    status_text = '<span color="green">Detectada</span>'
            else:
                status_text = '<span color="red">No Detectada</span>'
            self.pose_status_label.set_markup(status_text)
            return False
        GLib.idle_add(_update)

    def update_metrics(self, metrics):
        """Actualiza los widgets de métricas con nuevos datos."""
        def _update():
            # Limpiar métricas anteriores
            for row in self.metrics_rows:
                self.metrics_group.remove(row)
            self.metrics_rows.clear()

            if not metrics:
                self.score_label.set_markup("--/100")
                return False

            # Actualizar puntuación
            if 'score' in metrics:
                score = metrics['score']
                grade = metrics.get('grade', '')
                score_text = f"<b>{score:.0f}</b>/100 <small>({grade})</small>"
                self.score_label.set_markup(score_text)

            # Obtener las métricas a mostrar para la técnica actual
            metrics_to_display = self.stance_metric_map.get(self.current_technique, [])

            # Crear y añadir nuevas filas de métricas
            for key, title, fmt in metrics_to_display:
                if key in metrics:
                    value = metrics[key]
                    value_str = fmt.format(value)
                    label = Gtk.Label()
                    label.set_halign(Gtk.Align.END)
                    label.set_markup(f"<tt>{value_str}</tt>")
                    row = Adw.ActionRow(title=title)
                    row.add_suffix(label)
                    self.metrics_group.add(row)
                    self.metrics_rows.append(row)
            return False
        GLib.idle_add(_update)

    # === MANEJADORES DE EVENTOS ===

    def on_category_dropdown_changed(self, dropdown, param):
        """Maneja el cambio en el dropdown de categorías"""
        selected = dropdown.get_selected()
        if selected < len(self.category_list):
            self.current_category = self.category_list[selected]
            self.update_technique_dropdown()
            self.emit_technique_changed()
    
    def on_technique_changed(self, dropdown, param):
        """Maneja el cambio de técnica"""
        selected = dropdown.get_selected()
        techniques = self.techniques_data.get(self.current_category, [])
        
        if selected < len(techniques):
            self.current_technique = techniques[selected][0]
            self.emit_technique_changed()
    
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
            # Actualizar técnica actual al primer elemento
            self.current_technique = techniques[0][0]
    
    def emit_technique_changed(self):
        """Emite señal de cambio de técnica"""
        self.emit('technique-changed', self.current_category, self.current_technique)
    
    def on_capture_clicked(self, button):
        """Maneja click en botón de captura"""
        countdown = int(self.countdown_spin.get_value())
        duration = int(self.duration_spin.get_value())
        self.emit('capture-requested', countdown, duration)
    
    def on_record_clicked(self, button):
        """Maneja la acción de grabación."""
        countdown = int(self.countdown_spin.get_value())
        duration = int(self.duration_spin.get_value())
        print(f"Grabación solicitada: countdown={countdown}s, duración={duration}s")
        self.emit('record-requested', countdown, duration)
    
    def on_overlay_toggled(self, switch, param):
        """Maneja el evento de activación/desactivación del overlay."""
        active = switch.get_active()
        print(f"Overlay: {'ON' if active else 'OFF'}")
        self.emit('overlay-toggled', active)
    
    def on_load_reference_clicked(self, button):
        """Maneja la acción de cargar una referencia."""
        print("Cargar referencia solicitado desde el panel de control.")
        
        # Crear diálogo de selección de archivos
        dialog = Gtk.FileChooserDialog(
            title="Seleccionar archivo de referencia",
            transient_for=self.get_root(),
            action=Gtk.FileChooserAction.OPEN
        )
        
        # Agregar botones
        dialog.add_button("Cancelar", Gtk.ResponseType.CANCEL)
        dialog.add_button("Abrir", Gtk.ResponseType.ACCEPT)
        
        # Filtro para archivos JSON
        filter_json = Gtk.FileFilter()
        filter_json.set_name("Archivos JSON (*.json)")
        filter_json.add_pattern("*.json")
        dialog.add_filter(filter_json)
        
        # Establecer directorio inicial
        try:
            import os
            ref_dir = os.path.abspath("data/references")
            if os.path.exists(ref_dir):
                dialog.set_current_folder(Gio.File.new_for_path(ref_dir))
        except Exception as e:
            print(f"No se pudo establecer directorio inicial: {e}")
        
        # Mostrar diálogo de forma asíncrona
        dialog.connect('response', self.on_file_dialog_response)
        dialog.present()
    
    def on_file_dialog_response(self, dialog, response):
        """Maneja la respuesta del diálogo de selección de archivos."""
        if response == Gtk.ResponseType.ACCEPT:
            file = dialog.get_file()
            if file:
                filepath = file.get_path()
                print(f"Archivo seleccionado: {filepath}")
                self.load_reference_file(filepath)
        
        dialog.destroy()
    
    def load_reference_file(self, filepath):
        """Carga un archivo de referencia y emite señal para mostrarlo."""
        try:
            import json
            
            with open(filepath, 'r') as f:
                reference_data = json.load(f)
            
            print(f"Referencia cargada: {reference_data.get('technique', 'Desconocida')}")
            
            # Emitir señal para que el VideoWidget cargue la referencia
            self.emit('reference-loaded', reference_data)
            
        except Exception as e:
            print(f"Error cargando referencia: {e}")
            # TODO: Mostrar diálogo de error
    
    def on_save_reference_clicked(self, button):
        """Maneja la acción de guardar una referencia."""
        print("Guardar referencia solicitado desde el panel de control.")
        # Aquí puedes agregar la lógica para guardar la referencia actual si es necesario.
    
    def on_auto_learn_clicked(self, button):
        """Maneja la acción de aprendizaje automático."""
        print("Aprendizaje automático solicitado desde el panel de control.")
        # Aquí puedes agregar la lógica para el aprendizaje automático si es necesario.
