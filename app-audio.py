import os
import yt_dlp
import mimetypes
import threading
import time
import uuid
from flask import Flask, render_template, request, send_file, jsonify, after_this_request
from mutagen.mp4 import MP4

app = Flask(__name__)

progreso_global = {} # Diccionario global para almacenar el progreso de las descargas

# -------------------------------------------------------------------------------------------------------------------------------- #

def obtener_info(url: str) -> dict: # Funcion para obtener la informacion del video
    ydl_opts = {"quiet": True, "noplaylist": True} # Define las opciones de configuración (silencio y sin playlists).
    with yt_dlp.YoutubeDL(ydl_opts) as ydl: # Crea una instancia del descargador con esas opciones.
        info = ydl.extract_info(url, download=False) # Obtiene los metadatos del video sin descargarlo.

    return {
        "title": info.get("title", "cancion"), # Obtiene el titulo del URl
        "duration": info.get("duration", 0), # Duracion
        "thumbnail": info.get("thumbnail", ""), # Miniatura
        "uploader": info.get("uploader", "Desconocido"), # Canal de quien subio el video
    }

# -------------------------------------------------------------------------------------------------------------------------------- #

def limpiar_archivo(filepath: str, delay: int = 5): # Funcion que borra un archivo con un retrado de 5 segundos
    def _remove(path):
        time.sleep(delay) # Espera 5 seg en delay
        try: os.remove(path); print(f"\n[✔] Eliminado: {path}\n") # Intenta eliminar el archivo, en caso de ser exitoso mostrar el primer mensaje
        except Exception as e: print(f"[✘] No se pudo eliminar {path}: {e}") # Del caso contrario mostrar 
    threading.Thread(target=_remove, args=(filepath,), daemon=True).start() # En caso de fallar mostrar detalladamente el error

# -------------------------------------------------------------------------------------------------------------------------------- #

# Define la función, recibe URL, ID de tarea y carpeta destino
def descargar_audio_con_progreso(url: str, task_id: str, carpeta="temp") -> tuple[str, dict]:
    os.makedirs(carpeta, exist_ok=True) # Crea una carpeta, en caso que no exista crearla
    output_path = os.path.join(carpeta, "%(title)s.%(ext)s") # Ruta de salida con nombre según título y extensión

    def progreso_hook(d): # Funcion que actualiza el proceso de descarga
        if d['status'] == 'downloading': # Si el estado de descarga es "Downloanding"
            porcentaje = 0 # Inicializador en 0
            if d.get('total_bytes'): # Verificacion del tamanio total
                porcentaje = d['downloaded_bytes'] / d['total_bytes'] * 100 # Calcular % 

            progreso_global[task_id] = { # Guarda el proceso e la variable global
                "porcentaje": round(porcentaje, 4), # % en 4 decimales
                "descargado": d.get('downloaded_bytes', 0), # Bytes descargados
                "total": d.get('total_bytes', 0), # Tamanio
                "eta": d.get('eta', 0), # Tiempo estimado
                "speed": d.get('speed', 0) # Velocidad de descarga
            }

    ydl_opts = {
        "format": "bestaudio[ext=m4a]", # Descargar el mejor audio en formato m4a
        "outtmpl": output_path,
        "quiet": True, # No mostrar mensajes en consola
        "noplaylist": True,
        "progress_hooks": [progreso_hook], # Conectar la función de progreso
        "writethumbnail": True,  # Descargar miniatura
        "postprocessors": [
            {"key": "FFmpegMetadata", "add_metadata": True}, # Insertar metadatos con FFmpeg
            {"key": "EmbedThumbnail"},  # Incrustar la miniatura en el archivo
        ],
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)  # Descargar el video/audio y obtener su información
        filepath = ydl.prepare_filename(info) # Generar la ruta final del archivo descargado

    return filepath, info # Retorna la ruta del archivo y los metadatos del video

# -------------------------------------------------------------------------------------------------------------------------------- #

def _descarga_thread(url, custom_title, task_id): # Funcion que maneja la descarga
    try:
        filepath, info = descargar_audio_con_progreso(url, task_id)  # Llama a la función de descarga y obtiene ruta e info del archivo

        # --- Extraer artista y título ---
        base_title = custom_title or info.get("title", "cancion")  # Usa el título personalizado o el del video (por defecto "cancion")
        if "-" in base_title:  # Si el título tiene un guion, lo separa en artista y nombre
            artist, title = [x.strip() for x in base_title.split("-", 1)]  # Divide en dos partes (artista - título)
        else: artist, title = "Desconocido", base_title  # Si no hay guion, asigna artista desconocido y usa todo como título

        print(f"\n[INFO] Archivo procesado:\n")  # Mensaje de información
        print(f"       Artista: {artist}")  # Muestra el artista detectado
        print(f"       Título : {title}")  # Muestra el título detectado
        print(f"       Nombre final: {base_title}\n")  # Muestra el nombre completo final

        # --- Escribir metadatos en el archivo ---

        try:
            audio = MP4(filepath)  # Abre el archivo descargado como un contenedor MP4
            audio["\xa9ART"] = [artist]   # Inserta el metadato de artista
            audio["\xa9nam"] = [title]    # Inserta el metadato de título
            audio.save()  # Guarda los cambios en el archivo

        except Exception as e: print(f"[✘] No se pudieron escribir metadatos: {e}")  # Si falla, muestra error de metadatos

        progreso_global[task_id]["done"] = True  # Marca la tarea como completada en el diccionario global
        progreso_global[task_id]["filepath"] = filepath  # Guarda la ruta del archivo en la tarea
        progreso_global[task_id]["custom_title"] = base_title  # Guarda el título final en la tarea

    except Exception as e: progreso_global[task_id]["error"] = str(e)  # Si ocurre cualquier error en el proceso, lo registra en la tarea

# -------------------------------------------------------------------------------------------------------------------------------- #

@app.route("/") # Define la ruta principal
def index(): return render_template("index.html") # Renderiza la vista Html

# -------------------------------------------------------------------------------------------------------------------------------- #

@app.route("/informacion", methods=["POST"]) # Definicion de EndPoint POST

def informacion():

    data = request.get_json() # Obtiene los datos enviados en formato JSON
    url = data.get("url") # Extrae el valor de "url" del JSON recibido

    if not url: return jsonify({"error": "No se proporcionó un enlace"}), 400 # Si no hay URL
    try: return jsonify(obtener_info(url)) # En caso de tener URL obtener su informacion y devolverla en formato json
    except Exception as e: return jsonify({"error": str(e)}), 500 # En caso de error en la funcion obtener_info

# -------------------------------------------------------------------------------------------------------------------------------- #

@app.route("/descargar", methods=["POST"]) # Definicion de EndPoint POST

def descargar():

    data = request.get_json() # Obtiene los datos enviados en formato JSON
    url = data.get("url") # Extrae el valor de "url" del JSON recibido
    custom_title = data.get("custom_title") # Extrae un título personalizado opcional

    if not url: return jsonify({"error": "No se proporcionó un enlace"}), 400 # En caso de no proporcionar URL

    task_id = str(uuid.uuid4())   # Genera un ID único (Para diferenciar de las demas descargas)
    progreso_global[task_id] = {"porcentaje": 0, "done": False} # Inicializa el progreso en el diccionario global en 0

    threading.Thread(target=_descarga_thread, args=(url, custom_title, task_id), daemon=True).start() # Iniciar hilo de descarga
    return jsonify({"task_id": task_id}), 200 # Devuelve el ID de la tarea al cliente con estado 200

# -------------------------------------------------------------------------------------------------------------------------------- #

@app.route("/progreso/<task_id>") # Definicion de ruta (<task_id> parametro dinamico)

def progreso(task_id):
    
    data = progreso_global.get(task_id) # Busca en el diccionario global la tarea por su ID

    if not data: return jsonify({"error": "ID no encontrado"}), 404 # Si no encuentra el ID devolver error
    return jsonify(data) # Si encuentra los datos devolver en progreso en formato JSON

# -------------------------------------------------------------------------------------------------------------------------------- #

@app.route("/download_file/<task_id>") # Definicion de ruta para descargar archivo final

def download_file(task_id):
    
    data = progreso_global.get(task_id) # Obtiene los datos de progreso de la tarea usando su ID

    if not data or "filepath" not in data: return "Archivo no disponible", 404 # Si no existe la tarea devolver error

    filepath = data["filepath"] # Ruta del archivo en el servidor
    filename = data["custom_title"] + ".m4a" # Nombre nuevo asignado

    @after_this_request # Decorador que ejecuta una función justo después de enviar la respuesta

    def _remove_file(response):  # Función interna para eliminar el archivo después de enviarlo
        limpiar_archivo(filepath)  # Llama a la función que borra el archivo en segundo plano
        return response # Devuelve respuesta

    mime_type, _ = mimetypes.guess_type(filepath)  # Detecta el tipo MIME del archivo según su extensión
    return send_file(filepath, as_attachment=True, download_name=filename, mimetype=mime_type or "audio/mp4") # Envía el archivo como descarga, con el nombre correcto y el tipo MIME adecuado
    # MIME = Extensiones de Correo de Internet Multipropósito
    # Se usa para decirle al navegador qué tipo de archivo está descargando, así puede manejarlo correctamente

# -----------------------#
# Run
# -----------------------#

if __name__ == "__main__": # Comprueba si este archivo se está ejecutando directamente
    app.run(host="0.0.0.0", port=5000, debug=True)  # host="0.0.0.0" → acepta conexiones desde cualquier IP
