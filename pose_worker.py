#!/usr/bin/env python3
"""
Worker proceso independiente para MediaPipe pose detection
Este script captura video directamente y envía solo los resultados
"""
import sys
import pickle
import cv2
import numpy as np
import time


def main():
    """Función main del worker"""
    print("Worker MediaPipe iniciado", file=sys.stderr)
    
    # Importar MediaPipe aquí, en un proceso completamente limpio
    try:
        import mediapipe as mp
        print("MediaPipe importado exitosamente en worker", file=sys.stderr)
        
        # Configurar pose detection
        mp_pose = mp.solutions.pose
        mp_drawing = mp.solutions.drawing_utils
        
        # Inicializar detector con configuración optimizada
        pose = mp_pose.Pose(
            static_image_mode=False,
            model_complexity=0,  # Usar modelo más simple (0 en lugar de 1)
            smooth_landmarks=False,  # Desactivar suavizado para mayor velocidad
            enable_segmentation=False,
            min_detection_confidence=0.7,  # Aumentar umbral para mayor velocidad
            min_tracking_confidence=0.5
        )
        print("Pose detector inicializado en worker", file=sys.stderr)
        
        # Inicializar cámara en el worker
        camera = cv2.VideoCapture(0)
        camera.set(cv2.CAP_PROP_FRAME_WIDTH, 320)  # Resolución más baja
        camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 240)
        camera.set(cv2.CAP_PROP_FPS, 30)
        
        if not camera.isOpened():
            print("Error: No se pudo abrir la cámara en worker", file=sys.stderr)
            return
        
        print("Cámara inicializada en worker", file=sys.stderr)
        
        # Loop principal: capturar de cámara y procesar
        frame_counter = 0
        last_pose_detected = False
        
        while True:
            try:
                # Capturar frame directamente de la cámara
                ret, frame = camera.read()
                if not ret:
                    continue
                
                frame_counter += 1
                
                # Flipear horizontalmente para efecto espejo
                frame = cv2.flip(frame, 1)
                
                # Solo mostrar cada 50 frames para reducir overhead de I/O
                if frame_counter % 50 == 0:
                    print(f"Frame {frame_counter} procesado", file=sys.stderr)
                
                # Procesar pose con optimización
                rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                results = pose.process(rgb_frame)
                
                # Preparar resultado (solo landmarks, no frame)
                if results.pose_landmarks:
                    last_pose_detected = True
                    
                    # Extraer landmarks
                    landmarks = []
                    for landmark in results.pose_landmarks.landmark:
                        landmarks.append({
                            'x': landmark.x,
                            'y': landmark.y,
                            'z': landmark.z,
                            'visibility': landmark.visibility
                        })
                    
                    result = {
                        'landmarks': landmarks,
                        'pose_detected': True,
                        'frame_shape': frame.shape,
                        'frame_id': frame_counter
                    }
                else:
                    last_pose_detected = False
                    result = {
                        'landmarks': None,
                        'pose_detected': False,
                        'frame_shape': frame.shape,
                        'frame_id': frame_counter
                    }
                
                # Serializar y enviar resultado (mucho más pequeño sin frame)
                result_data = pickle.dumps(result)
                result_size = len(result_data)
                
                # Solo mostrar cada 50 frames para reducir overhead
                if frame_counter % 50 == 0:
                    print(f"Resultado frame {frame_counter}: {'pose detectada' if result['pose_detected'] else 'sin pose'}", file=sys.stderr)
                
                # Escribir tamaño y datos
                sys.stdout.buffer.write(result_size.to_bytes(4, byteorder='little'))
                sys.stdout.buffer.write(result_data)
                sys.stdout.buffer.flush()
                
                # Controlar FPS para no saturar
                time.sleep(0.033)  # ~30 FPS
                
            except Exception as e:
                print(f"Error procesando frame: {e}", file=sys.stderr)
                break
        
        # Cleanup
        camera.release()
        pose.close()
        print("Worker MediaPipe terminado", file=sys.stderr)
        
    except Exception as e:
        print(f"Error en worker MediaPipe: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc(file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
