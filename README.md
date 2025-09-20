# 🎵 YouTube Music Downloader Web App

## 📄 Descripción
Aplicación web para descargar el audio de videos de YouTube de manera sencilla y con feedback en tiempo real. Permite obtener información del video, renombrar el archivo antes de la descarga y visualizar el progreso mediante una barra dinámica.

---

## ⚙️ Características
- Vista previa del video: título, duración, autor y miniatura.  
- Renombrado de archivos antes de la descarga.  
- Barra de progreso y estado de descarga en tiempo real.  
- Descarga automática de audio en formato `.m4a`.  
- Manejo de errores y alertas para enlaces inválidos o fallos de descarga.

---

## 🛠 Requisitos
- **Python:** 3.11.9  
- **Librerías Python:**  
  - Flask  
  - yt-dlp  
  - mutagen  
  - requests  

Instalación de dependencias, clonación del repositorio y ejecución:

```bash
# Instalar dependencias
pip install Flask yt-dlp mutagen requests

# Clonar el repositorio
git clone https://github.com/EdgardSk8/Descargador-de-Canciones-de-Youtube.git
cd Descargador-de-Canciones-de-Youtube

# Ejecutar la aplicación
python app.py
