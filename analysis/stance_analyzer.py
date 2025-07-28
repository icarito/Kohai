"""
Analizador de stances de karate Goju-Ryu
"""
import numpy as np
import math
from typing import Dict, List, Optional, Tuple


class StanceAnalyzer:
    """Analizador especializado en stances de karate"""
    
    def __init__(self):
        # Parámetros ideales para cada stance
        self.stance_parameters = {
            'sanchin-dachi': {
                'stance_width_ratio': (1.2, 1.5),  # relación con ancho de hombros
                'knee_angle_range': (160, 170),    # grados
                'max_knee_asymmetry': 10,          # grados de diferencia
                'max_knee_deviation': 0.05,        # desviación de alineación vertical
                'weight_distribution': (0.45, 0.55),  # rango de distribución de peso
                'description': 'Posición de tres conflictos'
            },
            'zenkutsu-dachi': {
                'stance_width_ratio': (1.8, 2.2),
                'front_knee_angle': (130, 150),
                'back_knee_angle': (165, 175),
                'weight_distribution': (0.6, 0.8),  # más peso en pierna delantera
                'description': 'Posición adelantada'
            },
            'shiko-dachi': {
                'stance_width_ratio': (2.0, 2.5),
                'knee_angle_range': (100, 120),
                'max_knee_asymmetry': 5,
                'foot_angle': (30, 45),  # ángulo de apertura de pies
                'description': 'Posición del sumo'
            },
            'neko-ashi-dachi': {
                'stance_width_ratio': (0.8, 1.2),
                'front_knee_angle': (140, 160),
                'back_knee_angle': (100, 130),
                'weight_distribution': (0.1, 0.3),  # mayoría del peso atrás
                'description': 'Posición del gato'
            }
        }
    
    def analyze_stance(self, stance_name: str, landmarks) -> Optional[Dict]:
        """Analiza un stance específico"""
        if stance_name not in self.stance_parameters:
            return None
        
        if not landmarks:
            return None
        
        # Métodos específicos por stance
        if stance_name == 'sanchin-dachi':
            return self.analyze_sanchin_dachi(landmarks)
        elif stance_name == 'zenkutsu-dachi':
            return self.analyze_zenkutsu_dachi(landmarks)
        elif stance_name == 'shiko-dachi':
            return self.analyze_shiko_dachi(landmarks)
        elif stance_name == 'neko-ashi-dachi':
            return self.analyze_neko_ashi_dachi(landmarks)
        
        return None
    
    def analyze_sanchin_dachi(self, landmarks) -> Dict:
        """Análisis específico de Sanchin-dachi"""
        metrics = {}
        feedback = []
        score = 100
        
        # Extraer puntos clave
        key_points = self.extract_key_points(landmarks)
        if not key_points:
            return {'score': 0, 'feedback': ['No se detectaron puntos clave suficientes']}
        
        # 1. Ancho de stance
        stance_width = self.calculate_stance_width(key_points)
        shoulder_width = self._calculate_distance(key_points['left_shoulder'], key_points['right_shoulder'])
        
        if shoulder_width > 0:
            width_ratio = stance_width / shoulder_width
            metrics['stance_width_ratio'] = width_ratio
            
            ideal_range = self.stance_parameters['sanchin-dachi']['stance_width_ratio']
            if not (ideal_range[0] <= width_ratio <= ideal_range[1]):
                feedback.append("Stance muy estrecho - separa más los pies")
                score -= 15
        
        # 2. Ángulos de rodillas
        left_knee_angle = self.calculate_knee_angle(key_points, 'left')
        right_knee_angle = self.calculate_knee_angle(key_points, 'right')
        
        if left_knee_angle and right_knee_angle:
            metrics['left_knee_angle'] = left_knee_angle
            metrics['right_knee_angle'] = right_knee_angle
            
            ideal_range = self.stance_parameters['sanchin-dachi']['knee_angle_range']
            
            # Evaluar rodilla izquierda
            if left_knee_angle < ideal_range[0]:
                feedback.append("Rodilla izquierda muy flexionada")
                score -= 10
            elif left_knee_angle > ideal_range[1]:
                feedback.append("Rodilla izquierda muy rígida")
                score -= 5
            
            # Evaluar rodilla derecha
            if right_knee_angle < ideal_range[0]:
                feedback.append("Rodilla derecha muy flexionada")
                score -= 10
            elif right_knee_angle > ideal_range[1]:
                feedback.append("Rodilla derecha muy rígida")
                score -= 5
            
            # 3. Simetría de rodillas
            knee_asymmetry = abs(left_knee_angle - right_knee_angle)
            metrics['knee_symmetry'] = knee_asymmetry
            
            max_asymmetry = self.stance_parameters['sanchin-dachi']['max_knee_asymmetry']
            if knee_asymmetry > max_asymmetry:
                feedback.append("Asimetría en rodillas - equilibra ambas piernas")
                score -= 15
        
        # 4. Alineación de rodillas (no colapso hacia adentro)
        left_alignment = self.calculate_knee_alignment(key_points, 'left')
        right_alignment = self.calculate_knee_alignment(key_points, 'right')
        
        if left_alignment is not None:
            metrics['left_knee_alignment'] = left_alignment
            max_deviation = self.stance_parameters['sanchin-dachi']['max_knee_deviation']
            if left_alignment > max_deviation:
                feedback.append("Rodilla izquierda colapsa hacia adentro")
                score -= 20
        
        if right_alignment is not None:
            metrics['right_knee_alignment'] = right_alignment
            max_deviation = self.stance_parameters['sanchin-dachi']['max_knee_deviation']
            if right_alignment > max_deviation:
                feedback.append("Rodilla derecha colapsa hacia adentro")
                score -= 20
        
        # 5. Postura general
        posture_score = self.evaluate_general_posture(key_points)
        if posture_score < 0.8:
            feedback.append("Mejorar postura general - mantén espalda recta")
            score -= 10
        
        # Calcular score final
        metrics['score'] = max(0, score)
        metrics['feedback'] = feedback
        metrics['grade'] = self.get_grade(metrics['score'])
        
        return metrics
    
    def analyze_zenkutsu_dachi(self, landmarks) -> Dict:
        """Análisis específico de Zenkutsu-dachi"""
        metrics = {}
        feedback = []
        score = 100
        
        key_points = self.extract_key_points(landmarks)
        if not key_points:
            return {'score': 0, 'feedback': ['No se detectaron puntos clave suficientes']}

        # Determinar pierna delantera y trasera
        front_leg_side = self.get_front_leg(key_points)
        back_leg_side = 'right' if front_leg_side == 'left' else 'left'

        # 1. Largo del stance
        stance_length = self._calculate_distance(key_points['left_ankle'], key_points['right_ankle'])
        shoulder_width = self._calculate_distance(key_points['left_shoulder'], key_points['right_shoulder'])
        
        if shoulder_width > 0:
            length_ratio = stance_length / shoulder_width
            metrics['stance_length_ratio'] = length_ratio
            
            ideal_range = self.stance_parameters['zenkutsu-dachi']['stance_width_ratio']
            if length_ratio < ideal_range[0]:
                feedback.append("Stance muy corto - da un paso más largo")
                score -= 20
            elif length_ratio > ideal_range[1]:
                feedback.append("Stance muy largo - acorta el paso")
                score -= 15

        # 2. Ángulos de rodillas
        front_knee_angle = self.calculate_knee_angle(key_points, front_leg_side)
        back_knee_angle = self.calculate_knee_angle(key_points, back_leg_side)

        if front_knee_angle:
            metrics['front_knee_angle'] = front_knee_angle
            ideal_range = self.stance_parameters['zenkutsu-dachi']['front_knee_angle']
            if front_knee_angle < ideal_range[0]:
                feedback.append("Rodilla frontal muy flexionada")
                score -= 15
            elif front_knee_angle > ideal_range[1]:
                feedback.append("Rodilla frontal poco flexionada")
                score -= 15

        if back_knee_angle:
            metrics['back_knee_angle'] = back_knee_angle
            ideal_range = self.stance_parameters['zenkutsu-dachi']['back_knee_angle']
            if back_knee_angle < ideal_range[0]:
                feedback.append("Pierna trasera flexionada - estírala")
                score -= 20

        # 3. Postura
        posture_score = self.evaluate_general_posture(key_points)
        if posture_score < 0.8:
            feedback.append("Mejora la postura - espalda recta, hombros relajados")
            score -= 10

        metrics['score'] = max(0, score)
        metrics['feedback'] = feedback
        metrics['grade'] = self.get_grade(metrics['score'])
        
        return metrics
    
    def analyze_shiko_dachi(self, landmarks) -> Dict:
        """Análisis específico de Shiko-dachi"""
        metrics = {}
        feedback = []
        score = 100
        
        key_points = self.extract_key_points(landmarks)
        if not key_points:
            return {'score': 0, 'feedback': ['No se detectaron puntos clave suficientes']}

        # 1. Ancho de stance
        stance_width = self.calculate_stance_width(key_points)
        shoulder_width = self._calculate_distance(key_points['left_shoulder'], key_points['right_shoulder'])
        
        if shoulder_width > 0:
            width_ratio = stance_width / shoulder_width
            metrics['stance_width_ratio'] = width_ratio
            
            ideal_range = self.stance_parameters['shiko-dachi']['stance_width_ratio']
            if width_ratio < ideal_range[0]:
                feedback.append("Stance muy estrecho - separa más los pies")
                score -= 20
            elif width_ratio > ideal_range[1]:
                feedback.append("Stance muy ancho - acerca un poco los pies")
                score -= 15

        # 2. Ángulos de rodillas
        left_knee_angle = self.calculate_knee_angle(key_points, 'left')
        right_knee_angle = self.calculate_knee_angle(key_points, 'right')
        
        if left_knee_angle and right_knee_angle:
            metrics['left_knee_angle'] = left_knee_angle
            metrics['right_knee_angle'] = right_knee_angle
            
            ideal_range = self.stance_parameters['shiko-dachi']['knee_angle_range']
            
            avg_knee_angle = (left_knee_angle + right_knee_angle) / 2
            if avg_knee_angle < ideal_range[0]:
                feedback.append("Estás bajando demasiado")
                score -= 10
            elif avg_knee_angle > ideal_range[1]:
                feedback.append("Baja más la cadera, flexiona más las rodillas")
                score -= 20

            knee_asymmetry = abs(left_knee_angle - right_knee_angle)
            if knee_asymmetry > self.stance_parameters['shiko-dachi']['max_knee_asymmetry']:
                feedback.append("Asimetría en rodillas, equilibra el peso")
                score -= 15

        # 3. Ángulo de los pies
        left_foot_angle = self.calculate_foot_turnout_angle(key_points, 'left')
        right_foot_angle = self.calculate_foot_turnout_angle(key_points, 'right')

        if left_foot_angle is not None:
            metrics['left_foot_angle'] = left_foot_angle
            ideal_angle_range = self.stance_parameters['shiko-dachi']['foot_angle']
            if not (ideal_angle_range[0] <= left_foot_angle <= ideal_angle_range[1]):
                feedback.append("Ajusta el ángulo del pie izquierdo (apunta a 45°)")
                score -= 10

        if right_foot_angle is not None:
            metrics['right_foot_angle'] = right_foot_angle
            ideal_angle_range = self.stance_parameters['shiko-dachi']['foot_angle']
            if not (ideal_angle_range[0] <= right_foot_angle <= ideal_angle_range[1]):
                feedback.append("Ajusta el ángulo del pie derecho (apunta a 45°)")
                score -= 10

        metrics['score'] = max(0, score)
        metrics['feedback'] = feedback
        metrics['grade'] = self.get_grade(metrics['score'])
        
        return metrics
    
    def analyze_neko_ashi_dachi(self, landmarks) -> Dict:
        """Análisis específico de Neko-ashi-dachi"""
        metrics = {}
        feedback = []
        score = 100
        
        key_points = self.extract_key_points(landmarks)
        if not key_points:
            return {'score': 0, 'feedback': ['No se detectaron puntos clave suficientes']}

        front_leg_side = self.get_front_leg(key_points)
        back_leg_side = 'right' if front_leg_side == 'left' else 'left'

        # 1. Largo del stance
        stance_length = self._calculate_distance(key_points['left_ankle'], key_points['right_ankle'])
        shoulder_width = self._calculate_distance(key_points['left_shoulder'], key_points['right_shoulder'])
        
        if shoulder_width > 0:
            length_ratio = stance_length / shoulder_width
            metrics['stance_length_ratio'] = length_ratio
            
            ideal_range = self.stance_parameters['neko-ashi-dachi']['stance_width_ratio']
            if length_ratio > ideal_range[1]:
                feedback.append("Stance muy largo, acerca el pie frontal")
                score -= 15

        # 2. Ángulos de rodillas
        front_knee_angle = self.calculate_knee_angle(key_points, front_leg_side)
        back_knee_angle = self.calculate_knee_angle(key_points, back_leg_side)

        if front_knee_angle:
            metrics['front_knee_angle'] = front_knee_angle
            ideal_range = self.stance_parameters['neko-ashi-dachi']['front_knee_angle']
            if not (ideal_range[0] <= front_knee_angle <= ideal_range[1]):
                feedback.append("Revisa la flexión de la rodilla frontal")
                score -= 10

        if back_knee_angle:
            metrics['back_knee_angle'] = back_knee_angle
            ideal_range = self.stance_parameters['neko-ashi-dachi']['back_knee_angle']
            if back_knee_angle < ideal_range[0]:
                feedback.append("Rodilla trasera muy flexionada")
                score -= 15
            elif back_knee_angle > ideal_range[1]:
                feedback.append("Flexiona más la rodilla trasera (baja la cadera)")
                score -= 20

        # 3. Distribución de peso (aproximación)
        hip_center = (np.array(key_points['left_hip']) + np.array(key_points['right_hip'])) / 2
        back_hip = np.array(key_points[f'{back_leg_side}_hip'])
        
        weight_dist_proxy = abs(hip_center[0] - back_hip[0])
        if weight_dist_proxy > 0.1:
            feedback.append("Lleva el peso a la pierna trasera")
            score -= 25

        metrics['score'] = max(0, score)
        metrics['feedback'] = feedback
        metrics['grade'] = self.get_grade(metrics['score'])
        
        return metrics
    
    def extract_key_points(self, landmarks) -> Optional[Dict]:
        """Extrae puntos clave de los landmarks"""
        try:
            key_points = {
                'left_shoulder': [landmarks[11].x, landmarks[11].y, landmarks[11].z],
                'right_shoulder': [landmarks[12].x, landmarks[12].y, landmarks[12].z],
                'left_hip': [landmarks[23].x, landmarks[23].y, landmarks[23].z],
                'right_hip': [landmarks[24].x, landmarks[24].y, landmarks[24].z],
                'left_knee': [landmarks[25].x, landmarks[25].y, landmarks[25].z],
                'right_knee': [landmarks[26].x, landmarks[26].y, landmarks[26].z],
                'left_ankle': [landmarks[27].x, landmarks[27].y, landmarks[27].z],
                'right_ankle': [landmarks[28].x, landmarks[28].y, landmarks[28].z],
                'left_foot_index': [landmarks[31].x, landmarks[31].y, landmarks[31].z],
                'right_foot_index': [landmarks[32].x, landmarks[32].y, landmarks[32].z],
            }
            return key_points
        except (IndexError, AttributeError):
            return None
    
    def calculate_stance_width(self, key_points: Dict) -> float:
        """Calcula el ancho del stance"""
        return self._calculate_distance(key_points['left_ankle'], key_points['right_ankle'])
    
    def _calculate_distance(self, p1: List[float], p2: List[float]) -> float:
        """Calcula la distancia euclidiana 3D entre dos puntos."""
        return np.linalg.norm(np.array(p1) - np.array(p2))

    def calculate_knee_angle(self, key_points: Dict, side: str) -> Optional[float]:
        """Calcula el ángulo de la rodilla"""
        try:
            if side == 'left':
                hip = key_points['left_hip']
                knee = key_points['left_knee']
                ankle = key_points['left_ankle']
            else:
                hip = key_points['right_hip']
                knee = key_points['right_knee']
                ankle = key_points['right_ankle']
            
            return self.calculate_angle(hip, knee, ankle)
        except KeyError:
            return None
    
    def calculate_knee_alignment(self, key_points: Dict, side: str) -> Optional[float]:
        """Calcula la desviación de alineación de la rodilla"""
        try:
            if side == 'left':
                knee = key_points['left_knee']
                ankle = key_points['left_ankle']
            else:
                knee = key_points['right_knee']
                ankle = key_points['right_ankle']
            
            # Calcular desviación horizontal (colapso hacia adentro)
            return abs(knee[0] - ankle[0])
        except KeyError:
            return None

    def get_front_leg(self, key_points: Dict) -> str:
        """Determina qué pierna está al frente basado en la coordenada Z del tobillo."""
        try:
            if key_points['left_ankle'][2] < key_points['right_ankle'][2]:
                return 'left'
            else:
                return 'right'
        except (KeyError, IndexError):
            return 'left' # Fallback

    def calculate_foot_turnout_angle(self, key_points: Dict, side: str) -> Optional[float]:
        """Calcula el ángulo de apertura del pie en el plano del suelo (XZ)."""
        try:
            hip_line = np.array(key_points['right_hip']) - np.array(key_points['left_hip'])
            hip_line_xz = np.array([hip_line[0], hip_line[2]])
            
            # Vector perpendicular a la línea de la cadera, apunta hacia adelante
            sagittal_dir_xz = np.array([-hip_line_xz[1], hip_line_xz[0]])

            foot_line = np.array(key_points[f'{side}_foot_index']) - np.array(key_points[f'{side}_ankle'])
            foot_line_xz = np.array([foot_line[0], foot_line[2]])

            angle = self.calculate_angle_2d(foot_line_xz, sagittal_dir_xz)
            
            # Queremos el ángulo de apertura, que debería ser < 90
            return angle if angle < 90 else 180 - angle

        except (KeyError, ZeroDivisionError, IndexError):
            return None
    
    def calculate_angle(self, point1: List[float], point2: List[float], point3: List[float]) -> float:
        """Calcula el ángulo entre tres puntos"""
        a = np.array(point1)
        b = np.array(point2)  # punto vértice
        c = np.array(point3)
        
        ba = a - b
        bc = c - b
        
        cosine_angle = np.dot(ba, bc) / (np.linalg.norm(ba) * np.linalg.norm(bc))
        cosine_angle = np.clip(cosine_angle, -1.0, 1.0)
        
        angle = np.arccos(cosine_angle)
        return np.degrees(angle)

    def calculate_angle_2d(self, v1: np.ndarray, v2: np.ndarray) -> float:
        """Calcula el ángulo entre dos vectores 2D."""
        v1_u = v1 / np.linalg.norm(v1)
        v2_u = v2 / np.linalg.norm(v2)
        dot_product = np.dot(v1_u, v2_u)
        angle = np.arccos(np.clip(dot_product, -1.0, 1.0))
        return np.degrees(angle)
    
    def evaluate_general_posture(self, key_points: Dict) -> float:
        """Evalúa la postura general (0-1)"""
        try:
            # Evaluar alineación vertical del torso
            left_shoulder = key_points['left_shoulder']
            right_shoulder = key_points['right_shoulder']
            left_hip = key_points['left_hip']
            right_hip = key_points['right_hip']
            
            # Centro de hombros y caderas
            shoulder_center = [(left_shoulder[0] + right_shoulder[0]) / 2,
                             (left_shoulder[1] + right_shoulder[1]) / 2]
            hip_center = [(left_hip[0] + right_hip[0]) / 2,
                         (left_hip[1] + right_hip[1]) / 2]
            
            # Calcular desviación de la vertical
            horizontal_deviation = abs(shoulder_center[0] - hip_center[0])
            
            # Score basado en desviación (menos desviación = mejor score)
            max_acceptable_deviation = 0.1  # 10% del ancho del frame
            score = max(0, 1 - (horizontal_deviation / max_acceptable_deviation))
            
            return score
        except (KeyError, ZeroDivisionError):
            return 0.5  # Score neutral si no se puede calcular
    
    def get_grade(self, score: float) -> str:
        """Convierte score numérico a calificación"""
        if score >= 90:
            return "Excelente"
        elif score >= 80:
            return "Muy Bueno"
        elif score >= 70:
            return "Bueno"
        elif score >= 60:
            return "Regular"
        else:
            return "Necesita Trabajo"
    
    def get_stance_info(self, stance_name: str) -> Optional[Dict]:
        """Obtiene información de un stance"""
        return self.stance_parameters.get(stance_name)
    
    def get_available_stances(self) -> List[str]:
        """Obtiene lista de stances disponibles"""
        return list(self.stance_parameters.keys())
