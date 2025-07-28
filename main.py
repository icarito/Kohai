#!/usr/bin/env python3
"""
KOHAI - Karate Motion Analysis System
Entry point para la aplicación GTK4
"""

import sys
import multiprocessing as mp
import time

def init_multiprocessing():
    """Configurar multiprocessing antes de cualquier import de GTK o MediaPipe"""
    # CRÍTICO: usar 'spawn' para crear procesos completamente independientes
    # Esto evita que MediaPipe y GTK se mezclen
    mp.set_start_method('spawn', force=True)
    print("Multiprocessing configurado con método 'spawn'")

# Configurar multiprocessing INMEDIATAMENTE antes de cualquier otro import
init_multiprocessing()

# AHORA sí importar GTK (después de configurar multiprocessing)
import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')

from gi.repository import Gtk, Adw, GLib
from ui.main_window import KohaiMainWindow

class KohaiApplication(Adw.Application):
    """Aplicación principal de Kohai"""
    
    def __init__(self):
        super().__init__(application_id="com.kohai.karate-analyzer")
        self.connect('activate', self.on_activate)
    
    def on_activate(self, app):
        """Callback cuando la aplicación se activa"""
        print("Activando aplicación...")
        
        try:
            # Crear ventana principal de forma simple
            self.win = KohaiMainWindow(application=app)
            print("Ventana creada")
            
            # Configurar y mostrar inmediatamente
            self.win.set_default_size(1200, 800)
            self.win.present()
            
            print(f"Ventana mostrada - Visible: {self.win.get_visible()}")
            
        except Exception as e:
            print(f"Error creando ventana: {e}")
            import traceback
            traceback.print_exc()


def main():
    """Función main"""
    print("Iniciando aplicación Kohai...")
    
    app = KohaiApplication()
    return app.run(sys.argv)


if __name__ == '__main__':
    # El multiprocessing ya está configurado al inicio del archivo
    sys.exit(main())
