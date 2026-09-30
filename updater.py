import os
import sys
import time
import urllib.request
import subprocess
import json


def obtener_url_descarga(url):
    partes = url.rstrip("/").split("/")

    if len(partes) < 7:
        raise Exception("URL de actualización inválida")

    repo = f"{partes[3]}/{partes[4]}"
    tag = partes[6]
    nombre = partes[7] if len(partes) > 7 else ""

    api_url = (
        f"https://api.github.com/repos/{repo}/releases/tags/{tag}"
    )

    req = urllib.request.Request(
        api_url,
        headers={
            "User-Agent": "Downlader-Music-Youtube"
        }
    )

    with urllib.request.urlopen(req, timeout=15) as respuesta:
        datos = respuesta.read().decode("utf-8")

    release = json.loads(datos)

    for asset in release.get("assets", []):
        if asset.get("name") == nombre:
            return asset.get("browser_download_url")

    raise Exception(
        f"No se encontró el archivo {nombre} en la Release {tag}"
    )


def actualizar(url, exe_actual):

    carpeta = os.path.dirname(exe_actual)

    exe_nuevo = os.path.join(
        carpeta,
        "actualizacion_nueva.exe"
    )

    try:

        url_descarga = obtener_url_descarga(url)

        urllib.request.urlretrieve(
            url_descarga,
            exe_nuevo
        )

        # Esperar a que la aplicación principal cierre.
        while True:

            try:

                os.replace(
                    exe_nuevo,
                    exe_actual
                )

                break

            except PermissionError:

                time.sleep(1)

        subprocess.Popen(
            [exe_actual],
            cwd=carpeta
        )

    except Exception as error:

        print(
            f"Error al actualizar: {error}"
        )

        if os.path.exists(exe_nuevo):

            try:
                os.remove(exe_nuevo)

            except:
                pass


if __name__ == "__main__":

    if len(sys.argv) < 3:
        sys.exit(1)

    url = sys.argv[1]
    exe_actual = sys.argv[2]

    actualizar(
        url,
        exe_actual
    )