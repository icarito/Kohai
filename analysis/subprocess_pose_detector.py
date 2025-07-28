"""
Proceso de pose detection usando subprocess en lugar de multiprocessing
Esto evita completamente los problemas de protobuf al usar un proceso externo
"""
import subprocess
import pickle
import threading
import queue
import time


class SubprocessPoseDetector:
    """
    Detector de pose que usa subprocess para ejecutar MediaPipe
    """
    
    def __init__(self):
        self.process = None
        # Solo necesitamos queue de salida ya que no enviamos frames
        self.output_queue = queue.Queue(maxsize=5)
        self.running = False
        
        # Solo thread de output ya que no enviamos input
        self.output_thread = None
    
    def start(self):
        """Inicia el proceso de pose detection de forma no bloqueante"""
        if self.running:
            return
        
        print("Iniciando subprocess de pose detection...")
        
        # Usar threading para evitar bloquear el hilo principal
        start_thread = threading.Thread(target=self._start_worker, daemon=True)
        start_thread.start()
    
    def _start_worker(self):
        """Worker que inicia el proceso en un hilo separado"""
        try:
            print("Creando proceso worker...")
            
            # Iniciar proceso worker - solo stdout para recibir resultados
            self.process = subprocess.Popen(
                ['python', 'pose_worker.py'],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                bufsize=0,
                cwd='.'  # Asegurar directorio correcto
            )
            
            print(f"Subprocess pose detector iniciado: PID {self.process.pid}")
            self.running = True
            
            # Solo necesitamos threads de output y error
            self.output_thread = threading.Thread(target=self._output_worker, daemon=True)
            self.error_thread = threading.Thread(target=self._error_worker, daemon=True)
            
            self.output_thread.start()
            self.error_thread.start()
            
            print("Threads de comunicación iniciados")
            
        except Exception as e:
            print(f"Error iniciando subprocess: {e}")
            self.running = False
    
    def _error_worker(self):
        """Thread para capturar errores del subprocess"""
        while self.running and self.process and self.process.poll() is None:
            try:
                line = self.process.stderr.readline()
                if line:
                    print(f"Worker stderr: {line.decode().strip()}")
            except:
                break
    
    def _input_worker(self):
        """Ya no necesitamos input worker - el proceso captura video directamente"""
        pass  # Método eliminado
    
    def _output_worker(self):
        """Thread que recibe resultados del proceso worker"""
        while self.running and self.process and self.process.poll() is None:
            try:
                # Leer tamaño del resultado
                size_data = self.process.stdout.read(4)
                if len(size_data) != 4:
                    print(f"Error leyendo tamaño: recibido {len(size_data)} bytes")
                    break
                
                result_size = int.from_bytes(size_data, byteorder='little')
                
                # Leer datos del resultado
                result_data = self.process.stdout.read(result_size)
                if len(result_data) != result_size:
                    print(f"Error leyendo datos: esperado {result_size}, recibido {len(result_data)}")
                    break
                
                # Deserializar resultado
                result = pickle.loads(result_data)
                
                # Añadir a queue de salida
                try:
                    self.output_queue.put_nowait(result)
                except queue.Full:
                    # Si está lleno, quitar el más viejo
                    try:
                        self.output_queue.get_nowait()
                        self.output_queue.put_nowait(result)
                    except queue.Empty:
                        pass
                
            except Exception as e:
                print(f"Error en output worker: {e}")
                import traceback
                traceback.print_exc()
                break
    
    def process_frame(self, frame):
        """
        Ya no procesamos frames - el worker captura directamente
        Este método se mantiene para compatibilidad pero no hace nada
        """
        return True  # Siempre exitoso porque no hacemos nada
    
    def get_result(self):
        """
        Obtiene resultado del procesamiento (non-blocking)
        """
        if not self.running:
            return None
        
        try:
            result = self.output_queue.get_nowait()
            return result
        except queue.Empty:
            return None
    
    def is_alive(self):
        """Verifica si el proceso está activo"""
        return (self.running and 
                self.process and 
                self.process.poll() is None)
    
    def stop(self):
        """Detiene el proceso de pose detection"""
        if not self.running:
            return
        
        self.running = False
        
        # Terminar proceso
        if self.process:
            try:
                self.process.terminate()
                self.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.process.kill()
                self.process.wait()
        
        print("Subprocess pose detector detenido")
