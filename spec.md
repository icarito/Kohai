# KOHAI - Karate Motion Analysis System
## Especificación Técnica v1.1

### Resumen
Sistema de análisis biomecánico para karate Goju-Ryu usando pose estimation con cámara web/smartphone. Análisis completo de stances, técnicas dinámicas, bloqueos y katas.

### Técnicas Soportadas

#### Stances Estáticos
- **Sanchin-dachi** - Posición de tres conflictos (MVP)
- **Zenkutsu-dachi** - Posición adelantada
- **Shiko-dachi** - Posición del sumo/caballo ancho
- **Neko-ashi-dachi** - Posición del gato

#### Técnicas Dinámicas - Golpes de Puño
- **Seiken-zuki** - Puñetazo con nudillos frontales
- **Gyaku-zuki** - Puñetazo inverso
- **Uraken-uchi** - Golpe con dorso del puño
- **Shuto-uchi** - Golpe con canto de mano

#### Técnicas Dinámicas - Patadas
- **Mae-geri** - Patada frontal
- **Yoko-geri** - Patada lateral
- **Mawashi-geri** - Patada circular
- **Kansetsu-geri** - Patada a articulaciones

#### Bloqueos (Uke-waza)
- **Jodan-uke** - Bloqueo alto
- **Chudan-uke** - Bloqueo medio
- **Gedan-barai** - Barrido bajo
- **Shuto-uke** - Bloqueo con canto de mano

#### Katas
- **Sanchin** kata - Fundamental Goju-Ryu
- **Gekisai** - Katas básicos
- **Saifa, Seiyunchin, Seisan** - Katas intermedios

### UI Layout - GTK4/Adwaita

```
┌─────────────────────────────────────────────────────────────┐
│ [File] [View] [Tools] [Help]                                │
├─────────────────────────────────────────────────────────────┤
│                                   │                         │
│        VIDEO FEED                 │    CONTROL PANEL        │
│     (70% width)                   │     (30% width)         │
│                                   │                         │
│  ┌─ Pose overlay + trayectorias ┐  │ ┌─ Categoría ────────┐ │
│  │                             │  │ │ ○ Stances          │ │
│  │   [Countdown overlay]       │  │ │ ○ Golpes           │ │
│  │   [Velocidad/Potencia HUD]  │  │ │ ○ Patadas          │ │
│  │                             │  │ │ ○ Bloqueos         │ │
│  └─────────────────────────────┘  │ │ ○ Katas            │ │
│                                   │ └───────────────────┘ │
│                                   │                       │
│                                   │ ┌─ Técnica ──────────┐ │
│                                   │ │ [Dropdown dinámico] │ │
│                                   │ │ ▼ Sanchin-dachi    │ │
│                                   │ └───────────────────┘ │
│                                   │                       │
│                                   │ ┌─ Grabación ────────┐ │
│                                   │ │ [📸 Capturar]      │ │
│                                   │ │ [🎥 Grabar]        │ │
│                                   │ │ [⏱️ Repetir]       │ │
│                                   │ │ Countdown: [3]s    │ │
│                                   │ │ Duración: [5]s     │ │
│                                   │ └───────────────────┘ │
│                                   │                       │
│                                   │ ┌─ Métricas Live ────┐ │
│                                   │ │ Velocidad: 2.1m/s  │ │
│                                   │ │ Potencia: ███░░    │ │
│                                   │ │ Precisión: 85%     │ │
│                                   │ │ Score: 78/100      │ │
│                                   │ └───────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

### Métricas por Tipo de Técnica

#### Stances (Estáticos)
- Distribución de peso
- Ángulos articulares
- Estabilidad/simetría
- Alineación corporal

#### Golpes de Puño
- **Velocidad pico** del puño
- **Aceleración** en impacto
- **Trayectoria** (rectilínea vs. circular)
- **Rotación de cadera** sincronizada
- **Retracción** de mano contraria

#### Patadas
- **Altura máxima** alcanzada
- **Velocidad angular** de pierna
- **Equilibrio** durante ejecución
- **Extensión** completa
- **Control** en retorno

#### Bloqueos
- **Timing** de interceptación
- **Ángulo de deflección**
- **Posición corporal** protegida
- **Preparación** para contraataque
- **Economía de movimiento**

#### Katas
- **Timing global** vs. estándar
- **Fluidez** entre técnicas
- **Consistencia** de stances
- **Precisión** de técnicas individuales
- **Ritmo respiratorio** (donde aplique)

### Análisis Específico - Sanchin-dachi (MVP)

#### Métricas Clave
1. **Ancho de stance**: 1.2-1.5x ancho de hombros
2. **Ángulos de rodillas**: 160-170° (ligeramente flexionadas)
3. **Simetría**: diferencia <10° entre rodillas izq/der
4. **Alineación vertical**: rodillas sobre tobillos (no colapso interno)
5. **Posición de cadera**: neutral, sin inclinación excesiva
6. **Tensión dinámica**: estabilidad ante presión externa (micro-movimientos)

#### Errores Comunes a Detectar
- Stance muy estrecho/ancho
- Rodillas colapsando hacia adentro
- Asimetría significativa izq/der
- Tensión excesiva (rigidez) vs. insuficiente
- Peso mal distribuido

### Formatos de Archivo
- **Configuración:** JSON
- **Métricas/Análisis:** JSON
- **Poses:** BVH + JSON metadata
- **Videos:** MP4
- **Referencias:** .kohai (ZIP con JSON + BVH + thumbnails)

### Plan de Implementación

#### Fase 1: UI Base + Stances (Semanas 1-2) ⬅️ ACTUAL
- [ ] Setup GTK4 con navegación por categorías
- [ ] Layout principal con paneles ajustables (Paned)
- [ ] Video feed básico con OpenCV
- [ ] Integración MediaPipe para pose detection
- [ ] Análisis de Sanchin-dachi (MVP)
- [ ] Sistema de scoring básico
- [ ] Controles de grabación simples

#### Fase 2: Técnicas Dinámicas Básicas (Semanas 3-4)
- [ ] Detección de movimiento (velocity tracking)
- [ ] Análisis de golpes básicos (gyaku-zuki, mae-geri)
- [ ] Métricas de velocidad y trayectoria
- [ ] HUD en tiempo real para técnicas dinámicas

#### Fase 3: Bloqueos + Técnicas Avanzadas (Semanas 5-6)
- [ ] Análisis de bloqueos básicos
- [ ] Técnicas de puño avanzadas
- [ ] Patadas complejas
- [ ] Sistema de comparación y referencias

#### Fase 4: Katas (Semanas 7-8)
- [ ] Análisis secuencial de movimientos
- [ ] Kata Sanchin completo
- [ ] Timeline de ejecución
- [ ] Auto-learning y refinamiento
- [ ] Exportación BVH para análisis 3D

### Dependencias Técnicas
```
# UI
gi (PyGObject) - GTK4 bindings
cairo - Graphics

# Computer Vision & ML
opencv-python - Video capture y processing
mediapipe - Pose estimation
numpy - Numerical operations
scipy - Signal analysis

# Visualization
matplotlib - Plots y gráficos
pillow - Image processing

# Future
scikit-learn - ML para auto-learning
```

### Estructura de Directorios
```
kohai/
├── main.py              # Entry point
├── ui/
│   ├── __init__.py
│   ├── main_window.py   # Ventana principal GTK4
│   ├── video_widget.py  # Widget de video con overlay
│   └── control_panel.py # Panel de controles
├── analysis/
│   ├── __init__.py
│   ├── pose_detector.py # MediaPipe wrapper
│   ├── stance_analyzer.py # Análisis de stances
│   └── metrics.py       # Cálculos de métricas
├── data/
│   ├── references/      # Poses/técnicas de referencia
│   └── sessions/        # Grabaciones de usuario
└── requirements.txt
```
