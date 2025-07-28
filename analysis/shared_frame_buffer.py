"""
Buffer de frames compartido entre procesos usando memoria compartida
"""
import multiprocessing.shared_memory as shm
import numpy as np
import threading
import time


class SharedFrameBuffer:
    """
    Buffer circular de frames en memoria compartida
    Permite que un proceso escriba frames y otro los lea sin copia
    """
    
    def __init__(self, frame_shape=(480, 640, 3), buffer_size=5, name=None):
        self.frame_shape = frame_shape
        self.buffer_size = buffer_size
        self.frame_bytes = np.prod(frame_shape) * np.dtype(np.uint8).itemsize
        
        # Tamaño total: frames + metadatos (write_idx, read_idx, frame_counters)
        metadata_size = 4 * (buffer_size + 2)  # 2 índices + contador por frame
        total_size = (self.frame_bytes * buffer_size) + metadata_size
        
        if name:
            # Consumidor: conectar a memoria existente
            self.shm = shm.SharedMemory(name=name)
            self.is_creator = False
        else:
            # Productor: crear nueva memoria compartida
            self.shm = shm.SharedMemory(create=True, size=total_size)
            self.is_creator = True
            
            # Inicializar metadatos
            self._get_metadata_view()[:] = 0
        
        self.name = self.shm.name
        self.lock = threading.Lock()
        
    def _get_metadata_view(self):
        """Obtiene vista de los metadatos (índices y contadores)"""
        offset = self.frame_bytes * self.buffer_size
        return np.frombuffer(
            self.shm.buf[offset:offset + 4 * (self.buffer_size + 2)], 
            dtype=np.int32
        )
    
    def _get_frame_view(self, slot):
        """Obtiene vista del frame en el slot especificado"""
        offset = slot * self.frame_bytes
        return np.frombuffer(
            self.shm.buf[offset:offset + self.frame_bytes], 
            dtype=np.uint8
        ).reshape(self.frame_shape)
    
    def write_frame(self, frame, frame_counter):
        """Escribe un frame al buffer (solo desde el proceso productor)"""
        if not self.is_creator:
            return False
            
        with self.lock:
            metadata = self._get_metadata_view()
            write_idx = metadata[0]
            
            # Escribir frame
            frame_view = self._get_frame_view(write_idx)
            frame_view[:] = frame
            
            # Actualizar contador del frame
            metadata[2 + write_idx] = frame_counter
            
            # Avanzar índice de escritura
            metadata[0] = (write_idx + 1) % self.buffer_size
            
        return True
    
    def read_latest_frame(self):
        """Lee el frame más reciente (desde el proceso consumidor)"""
        metadata = self._get_metadata_view()
        write_idx = metadata[0]
        
        # El frame más reciente está en (write_idx - 1)
        latest_slot = (write_idx - 1) % self.buffer_size
        
        # Verificar si hay datos
        frame_counter = metadata[2 + latest_slot]
        if frame_counter == 0:
            return None, 0
        
        # Leer frame
        frame_view = self._get_frame_view(latest_slot)
        return frame_view.copy(), frame_counter  # Copiar para evitar race conditions
    
    def cleanup(self):
        """Limpia recursos"""
        if self.is_creator:
            self.shm.unlink()  # Solo el creador debe unlink
        self.shm.close()


class SharedFrameManager:
    """
    Gestor que simplifica el uso del buffer compartido
    """
    
    def __init__(self, frame_shape=(480, 640, 3)):
        self.frame_shape = frame_shape
        self.buffer = None
        self.last_frame_counter = 0
    
    def create_buffer(self):
        """Crea buffer (desde el proceso worker)"""
        self.buffer = SharedFrameBuffer(self.frame_shape)
        return self.buffer.name
    
    def connect_buffer(self, buffer_name):
        """Conecta a buffer existente (desde el proceso UI)"""
        self.buffer = SharedFrameBuffer(self.frame_shape, name=buffer_name)
        return True
    
    def put_frame(self, frame, frame_counter):
        """Pone frame en buffer"""
        if self.buffer:
            return self.buffer.write_frame(frame, frame_counter)
        return False
    
    def get_latest_frame(self):
        """Obtiene último frame disponible"""
        if not self.buffer:
            return None, 0
        
        frame, frame_counter = self.buffer.read_latest_frame()
        
        # Solo devolver si es un frame nuevo
        if frame_counter > self.last_frame_counter:
            self.last_frame_counter = frame_counter
            return frame, frame_counter
        
        return None, frame_counter
    
    def cleanup(self):
        """Limpia recursos"""
        if self.buffer:
            self.buffer.cleanup()
