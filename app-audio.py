import os
import yt_dlp
import mimetypes
import threading
import time
import uuid
from flask import Flask, render_template, request, send_file, jsonify, after_this_request

app = Flask(__name__)

# Diccionario global para almacenar el progreso de las descargas
progreso_global = {}

# ------------------------------------------------------------------------------#
# Funciones de yt_dlp
# ------------------------------------------------------------------------------#

def obtener_info(url: str) -> dict:
    """Obtiene información básica del video sin descargarlo."""
    ydl_opts = {"quiet": True, "noplaylist": True}
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)

    return {
        "title": info.get("title", "cancion"),
        "duration": info.get("duration", 0),
        "thumbnail": info.get("thumbnail", ""),
        "uploader": info.get("uploader", "Desconocido"),
    }


def limpiar_archivo(filepath: str, delay: int = 5):
    """Elimina un archivo después de un delay en un hilo separado."""
    def _remove(path):
        time.sleep(delay)
        try:
            os.remove(path)
            print(f"[✔] Eliminado: {path}")
        except Exception as e:
            print(f"[✘] No se pudo eliminar {path}: {e}")

    threading.Thread(target=_remove, args=(filepath,), daemon=True).start()


def descargar_audio_con_progreso(url: str, task_id: str, carpeta="temp") -> tuple[str, dict]:
    """Descarga audio y actualiza progreso en tiempo real usando progreso_global."""
    os.makedirs(carpeta, exist_ok=True)
    output_path = os.path.join(carpeta, "%(title)s.%(ext)s")

    def progreso_hook(d):
        if d['status'] == 'downloading':
            porcentaje = 0
            if d.get('total_bytes'):
                porcentaje = d['downloaded_bytes'] / d['total_bytes'] * 100
            progreso_global[task_id] = {
                "porcentaje": round(porcentaje, 2),
                "descargado": d.get('downloaded_bytes', 0),
                "total": d.get('total_bytes', 0),
                "eta": d.get('eta', 0),
                "speed": d.get('speed', 0)
            }

    ydl_opts = {
        "format": "bestaudio[ext=m4a]",
        "outtmpl": output_path,
        "quiet": True,
        "noplaylist": True,
        "progress_hooks": [progreso_hook],
        "writethumbnail": True,
        "postprocessors": [
            {"key": "FFmpegMetadata", "add_metadata": True},
            {"key": "EmbedThumbnail"},
        ],
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        filepath = ydl.prepare_filename(info)

    return filepath, info


# ------------------------------------------------------------------------------#
# Función de hilo para descarga
# ------------------------------------------------------------------------------#

def _descarga_thread(url, custom_title, task_id):
    """Ejecuta la descarga en background y actualiza progreso_global al finalizar."""
    try:
        filepath, info = descargar_audio_con_progreso(url, task_id)
        progreso_global[task_id]["done"] = True
        progreso_global[task_id]["filepath"] = filepath
        progreso_global[task_id]["custom_title"] = custom_title or info.get("title", "cancion")
    except Exception as e:
        progreso_global[task_id]["error"] = str(e)


# ------------------------------------------------------------------------------#
# Rutas Flask
# ------------------------------------------------------------------------------#

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/informacion", methods=["POST"])
def informacion():
    data = request.get_json()
    url = data.get("url")
    if not url:
        return jsonify({"error": "No se proporcionó un enlace"}), 400
    try:
        return jsonify(obtener_info(url))
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/descargar", methods=["POST"])
def descargar():
    """Inicia la descarga en background y retorna un task_id para el progreso."""
    data = request.get_json()
    url = data.get("url")
    custom_title = data.get("custom_title")

    if not url:
        return jsonify({"error": "No se proporcionó un enlace"}), 400

    task_id = str(uuid.uuid4())  # ID único para rastrear progreso
    progreso_global[task_id] = {"porcentaje": 0, "done": False}

    # Iniciar hilo de descarga
    threading.Thread(target=_descarga_thread, args=(url, custom_title, task_id), daemon=True).start()
    return jsonify({"task_id": task_id}), 200


@app.route("/progreso/<task_id>")
def progreso(task_id):
    """Retorna el progreso actual de una descarga."""
    data = progreso_global.get(task_id)
    if not data:
        return jsonify({"error": "ID no encontrado"}), 404
    return jsonify(data)


@app.route("/download_file/<task_id>")
def download_file(task_id):
    """Envia el archivo descargado una vez que esté listo."""
    data = progreso_global.get(task_id)
    if not data or "filepath" not in data:
        return "Archivo no disponible", 404

    filepath = data["filepath"]
    filename = data["custom_title"] + ".m4a"

    @after_this_request
    def _remove_file(response):
        limpiar_archivo(filepath)
        return response

    mime_type, _ = mimetypes.guess_type(filepath)
    return send_file(filepath, as_attachment=True, download_name=filename, mimetype=mime_type or "audio/mp4")


# -----------------------#
# Run
# -----------------------#

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
