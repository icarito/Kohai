#!/usr/bin/env python3
"""
Worker proceso independiente para MediaPipe pose detection
Este script captura video directamente y envía solo los resultados
Usa memoria compartida para frames
"""
import sys
import cv2
import numpy as np
import time
import json
from analysis.shared_frame_buffer import SharedFrameManager


def main():
    """Función principal del worker"""
    print("Worker MediaPipe iniciado", file=sys.stderr)
    
    try:
        # Importar MediaPipe solo aquí para evitar conflictos
        import mediapipe as mp
        print("MediaPipe importado exitosamente en worker", file=sys.stderr)
        
        # Configurar MediaPipe para pose detection ULTRA-OPTIMIZADO
        mp_pose = mp.solutions.pose
        pose = mp_pose.Pose(
            static_image_mode=False,
            model_complexity=0,  # Modelo más simple = máxima velocidad
            enable_segmentation=False,
            min_detection_confidence=0.2,  # Más bajo para detectar más poses
            min_tracking_confidence=0.2,   # Más bajo para mejor tracking continuo
            smooth_landmarks=True,         # CLAVE: Suavizado interno de MediaPipe
            smooth_segmentation=False
        )
        
        print("Pose detector inicializado en worker", file=sys.stderr)
        
        # Configurar captura de video 
        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            print("Error: No se pudo abrir la cámara", file=sys.stderr)
            return
        
        # Configuración de cámara optimizada para alta velocidad
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        cap.set(cv2.CAP_PROP_FPS, 60)      # Intentar 60 FPS si la cámara lo soporta
        cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)  # Buffer mínimo para reducir latencia
        cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc('M', 'J', 'P', 'G'))  # MJPEG para mayor velocidad
        
        print("Cámara inicializada en worker", file=sys.stderr)
        
        # Crear buffer de frames compartido
        frame_manager = SharedFrameManager(frame_shape=(480, 640, 3))
        buffer_name = frame_manager.create_buffer()
        
        # Enviar nombre del buffer al proceso principal
        init_message = {
            'type': 'init',
            'shared_buffer_name': buffer_name,
            'status': 'ready'
        }
        
        init_json = json.dumps(init_message)
        init_data = init_json.encode('utf-8')
        sys.stdout.buffer.write(len(init_data).to_bytes(4, byteorder='little'))
        sys.stdout.buffer.write(init_data)
        sys.stdout.buffer.flush()
        
        print(f"Buffer compartido creado: {buffer_name}", file=sys.stderr)
        
        # Loop principal: capturar de cámara y procesar
        frame_counter = 0
        last_valid_landmarks = None  # Para interpolación cuando no hay detección
        last_detection_frame = 0     # Frame donde se detectó la última pose
        pose_persistence_frames = 10  # Reducido para más fluidez: 10 frames (~0.33 segundos)
        
        # Buffer de resultado actual para consistencia
        current_result = {
            'landmarks': None,
            'pose_detected': False,
            'pose_confidence': 'none',
            'frame_shape': (480, 640, 3),
            'frame_id': 0
        }
        
        while True:
            try:
                # Capturar frame
                ret, frame = cap.read()
                if not ret:
                    continue
                
                frame_counter += 1
                
                # Flipear horizontalmente para efecto espejo
                frame = cv2.flip(frame, 1)
                
                # Escribir frame al buffer compartido (todos los frames)
                frame_manager.put_frame(frame, frame_counter)
                
                # Solo mostrar cada 50 frames para reducir overhead de I/O
                if frame_counter % 50 == 0:
                    print(f"Frame {frame_counter} procesado", file=sys.stderr)
                
                # PROCESAR POSE EN TODOS LOS FRAMES para máxima fluidez
                rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                results = pose.process(rgb_frame)
                
                # Preparar resultado con tracking mejorado y persistencia
                frames_since_detection = frame_counter - last_detection_frame
                
                if results.pose_landmarks:
                    # NUEVA DETECCIÓN REAL
                    landmarks = []
                    for landmark in results.pose_landmarks.landmark:
                        landmarks.append({
                            'x': landmark.x,
                            'y': landmark.y,
                            'z': landmark.z,
                            'visibility': landmark.visibility
                        })
                    
                    # Actualizar landmarks válidos y frame de detección
                    last_valid_landmarks = landmarks
                    last_detection_frame = frame_counter
                    
                    current_result = {
                        'landmarks': landmarks,
                        'pose_detected': True,
                        'pose_confidence': 'high',  # Alta confianza cuando se detecta
                        'frame_shape': frame.shape,
                        'frame_id': frame_counter
                    }
                    
                elif last_valid_landmarks and frames_since_detection <= pose_persistence_frames:
                    # MANTENER POSE ANTERIOR si está dentro del rango de persistencia
                    if frames_since_detection <= 3:
                        confidence_level = 'interpolated'
                    elif frames_since_detection <= 7:
                        confidence_level = 'fading'
                    else:
                        confidence_level = 'fading'
                    
                    current_result = {
                        'landmarks': last_valid_landmarks,
                        'pose_detected': True,
                        'pose_confidence': confidence_level,
                        'frame_shape': frame.shape,
                        'frame_id': frame_counter,
                        'frames_since_detection': frames_since_detection
                    }
                    
                else:
                    # NO HAY POSE o muy antigua
                    current_result = {
                        'landmarks': None,
                        'pose_detected': False,
                        'pose_confidence': 'none',
                        'frame_shape': frame.shape,
                        'frame_id': frame_counter
                    }
                
                # ENVIAR RESULTADO SIEMPRE (para cada frame)
                result_json = json.dumps(current_result)
                result_data = result_json.encode('utf-8')
                result_size = len(result_data)
                
                # Solo mostrar cada 50 frames para reducir overhead
                if frame_counter % 50 == 0:
                    confidence_text = current_result.get('pose_confidence', 'unknown')
                    print(f"Resultado frame {frame_counter}: {'pose detectada' if current_result['pose_detected'] else 'sin pose'} ({confidence_text})", file=sys.stderr)
                
                # Escribir tamaño y datos
                sys.stdout.buffer.write(result_size.to_bytes(4, byteorder='little'))
                sys.stdout.buffer.write(result_data)
                sys.stdout.buffer.flush()
                
                # Controlar FPS - OPTIMIZADO para máxima velocidad
                time.sleep(0.01)  # Reducido para más velocidad: ~100 FPS teórico
                
            except KeyboardInterrupt:
                print("Worker interrumpido por usuario", file=sys.stderr)
                break
            except Exception as e:
                print(f"Error procesando frame {frame_counter}: {e}", file=sys.stderr)
                continue
        
    except Exception as e:
        print(f"Error en worker: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc(file=sys.stderr)
    finally:
        # Limpiar recursos
        if 'cap' in locals():
            cap.release()
        if 'frame_manager' in locals():
            frame_manager.cleanup()
        print("Worker terminado", file=sys.stderr)


if __name__ == '__main__':
    main()