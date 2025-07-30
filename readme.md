# KOHAI - Karate Motion Analysis System

![Kohai Banner](https://img.shields.io/badge/Karate-Goju--Ryu-red) ![Python](https://img.shields.io/badge/Python-3.8+-blue) ![GTK4](https://img.shields.io/badge/UI-GTK4%2FAdwaita-green)

**Kohai** (後輩) es un sistema de análisis biomecánico para karate Goju-Ryu que utiliza computer vision y pose estimation para ayudar a practicantes a mejorar su técnica.

## ✨ Características

- 🧘 **Análisis de Stances**: Sanchin-dachi, Zenkutsu-dachi, Shiko-dachi, Neko-ashi-dachi
- 👊 **Técnicas Dinámicas**: Golpes, patadas, bloqueos
- 🥋 **Katas Completos**: Análisis secuencial de movimientos
- 📊 **Métricas en Tiempo Real**: Scoring, feedback instantáneo
- 🎯 **Sistema de Referencias**: Comparación con técnicas ideales
- 🧠 **Auto-learning**: Mejora automática con el uso

## 🚀 Inicio Rápido

### Requisitos del Sistema

- Python 3.8+
- Cámara web
- GTK4 y Adwaita (Linux)

### Instalación

```bash
# Clonar el repositorio
git clone https://github.com/tu-usuario/kohai
cd kohai

# Instalar dependencias
pip install -r requirements.txt

# En sistemas Linux, instalar GTK4 y dependencias
# Ubuntu/Debian:
sudo apt install python3-gi python3-gi-cairo gir1.2-gtk-4.0 gir1.2-adw-1

# Fedora:
sudo dnf install python3-gobject gtk4-devel libadwaita-devel

# Ejecutar la aplicación
python main.py
```

### Uso Básico

1. **Selecciona una categoría**: Stances, Golpes, Patadas, Bloqueos, o Katas
2. **Elige una técnica específica** del dropdown
3. **Colócate frente a la cámara** y ajusta tu posición
4. **Observa las métricas en tiempo real** en el panel lateral
5. **Captura o graba** tu técnica para análisis detallado


## 🛠️ Tecnologías

- **UI**: GTK4 + Adwaita (interfaz moderna y nativa)
- **Computer Vision**: OpenCV + MediaPipe
- **Análisis**: NumPy, SciPy
- **Formato de datos**: JSON, BVH (compatible con software 3D)

## 🎯 Roadmap

### Fase 1: Stances Básicos ✅
- [x] Interfaz GTK4 responsiva
- [x] Detección de pose en tiempo real
- [x] Sistema de referencias con overlay azul
- [x] Captura y guardado de poses

### Fase 2: Técnicas Dinámicas (En progreso)
- [ ] Análisis de golpes básicos
- [ ] Detección de velocidad y trayectoria
- [ ] Métricas de potencia

### Fase 3: Sistema Avanzado
- [ ] Auto-learning de técnicas
- [ ] Análisis de katas completos
- [ ] Exportación a formatos 3D

## 🤝 Contribuir

¡Las contribuciones son bienvenidas! 

## 📄 Licencia

Este proyecto está bajo la Licencia GPLv3 (o posterior). Ver `LICENSE` para más detalles.


*"La suavidad vence a la dureza, la tranquilidad vence al movimiento"*