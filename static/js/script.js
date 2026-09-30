document.addEventListener("DOMContentLoaded", () => {

const BtnBuscarCancion = document.querySelector(".Btn-Buscar-Cancion");
const BtnPegar = document.querySelector(".Btn-Pegar");
const input = document.querySelector("#youtube-url");

const loadingDiv = document.querySelector(".loading");
const previewDiv = document.querySelector("#Informacion-Cancion");

const titulo = document.querySelector(".Titulo-Cancion");
const informacion = document.querySelector(".Informacion-Cancion-p");
const imagen = document.querySelector(".Imagen-Caratula");

const renameInput = document.querySelector("#rename-title");
const btnDescargar = document.querySelector(".Btn-Descargar-Cancion");

const progressContainer =
    document.querySelector("#Contenedor-Barra-Progreso");

const progressBar =
    document.querySelector("#barra-progreso");

const textoProgreso =
    document.querySelector(".informacion-progreso");

const ImagenVacia = "/downloader.png";

let videoActual = null;

async function obtenerInfo(url) {

    try {

        const res = await fetch("/informacion", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({ url })
        });

        const data = await res.json();

        if (!res.ok) {
            throw data;
        }

        return data;

    } catch (err) {

        alert(
            "Error al obtener información: " +
            (err.error || err)
        );

        throw err;
    }
}

function mostrarPreview(videoInfo) {

    videoActual = videoInfo;

    const duration = videoInfo.duration || 0;
    const minutes = Math.floor(duration / 60);
    const seconds = duration % 60;

    const durationFormatted =
        `${minutes}:${seconds.toString().padStart(2, "0")}`;

    titulo.textContent = videoInfo.title;

    informacion.innerHTML = `
        <strong>Duración:</strong> ${durationFormatted}
        <span class="mx-1">·</span>
        <strong>Autor:</strong> ${videoInfo.uploader || "--"}
    `;

    imagen.src =
        videoInfo.thumbnail || ImagenVacia;

    imagen.onerror = () => {
        imagen.src = ImagenVacia;
    };

    renameInput.value =
        videoInfo.title.replace(/[<>:"/\\|?*]+/g, "");

    renameInput.disabled = false;
    btnDescargar.disabled = false;
}


async function iniciarDescarga(url, customTitle) {

    toggleLoading(true);

    try {

        const res = await fetch("/descargar", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                url,
                custom_title: customTitle
            })
        });

        const data = await res.json();

        if (!res.ok) {
            throw data;
        }

        const taskId = data.task_id;

        progressContainer.style.visibility = "visible";

        updateProgress(
            0,
            "Descargando... 0%"
        );

        const interval = setInterval(async () => {

            try {

                const progresoRes =
                    await fetch(`/progreso/${taskId}`);

                const progresoData =
                    await progresoRes.json();

                if (progresoData.error) {

                    clearInterval(interval);

                    alert(
                        "Error en la descarga: " +
                        progresoData.error
                    );

                    toggleLoading(false);
                    resetProgress();

                    return;
                }

                const porcentaje =
                    progresoData.porcentaje || 0;

                const texto = progresoData.done
                    ? "Completado ✔ (Revisa en tu carpeta de descargas)"
                    : `Descargando... ${porcentaje}%`;

                updateProgress(
                    porcentaje,
                    texto
                );

                if (progresoData.done) {

                    clearInterval(interval);

                    const a =
                        document.createElement("a");

                    // a.href =
                    //     `/download_file/${taskId}`;

                    // a.download =
                    //     progresoData.custom_title +
                    //     ".m4a";

                    document.body.appendChild(a);
                    a.click();
                    a.remove();

                    toggleLoading(false);
                }

            } catch (err) {

                clearInterval(interval);

                console.error(err);

                toggleLoading(false);
                resetProgress();
            }

        }, 500);

    } catch (err) {

        alert(
            "Error al iniciar descarga: " +
            (err.error || err)
        );

        toggleLoading(false);
        resetProgress();
    }
}

function toggleLoading(show) {

    loadingDiv.style.visibility =
        show ? "visible" : "hidden";
}

function updateProgress(porcentaje, texto) {

    progressBar.style.width =
        `${porcentaje}%`;

    textoProgreso.textContent =
        texto;
}

function resetProgress() {

    progressBar.style.width = "0%";

    textoProgreso.textContent = "";

    progressContainer.style.visibility =
        "hidden";
}

BtnBuscarCancion.addEventListener(
    "click",
    async () => {

        const url = input.value.trim();

        if (!url) {

            alert(
                "Por favor pega un enlace de YouTube."
            );

            return;
        }

        resetProgress();
        toggleLoading(true);

        try {

            const videoInfo =
                await obtenerInfo(url);

            mostrarPreview(videoInfo);

        } catch (err) {

            console.error(err);

        } finally {

            toggleLoading(false);
        }
    }
);

BtnPegar.addEventListener(
    "click",
    async () => {

        try {

            const text =
                await navigator.clipboard.readText();

            if (text) {

                input.value =
                    text.trim();

            } else {

                alert(
                    "El portapapeles está vacío."
                );
            }

        } catch (err) {

            alert(
                "No se pudo acceder al portapapeles."
            );

            console.error(err);
        }
    }
);

btnDescargar.addEventListener(
    "click",
    () => {

        if (!videoActual) {
            return;
        }

        const customTitle =
            renameInput.value.trim() ||
            videoActual.title;

        iniciarDescarga(
            input.value.trim(),
            customTitle
        );
    }
);

async function cargarVersion() {
    try {
        const respuesta = await fetch("/version");
        const datos = await respuesta.json();

        document.getElementById("version-app").textContent =
            `v${datos.version}`;

        return datos.version;

    } catch (error) {
        console.error("No se pudo obtener la versión:", error);
        return null;
    }
}

function compararVersiones(actual, nueva) {
    const versionActual = actual.split(".").map(Number);
    const versionNueva = nueva.split(".").map(Number);

    for (
        let i = 0;
        i < Math.max(versionActual.length, versionNueva.length);
        i++
    ) {
        const actualNumero = versionActual[i] || 0;
        const nuevaNumero = versionNueva[i] || 0;

        if (nuevaNumero > actualNumero) {
            return true;
        }

        if (nuevaNumero < actualNumero) {
            return false;
        }
    }

    return false;
}

async function comprobarActualizacion() {
    try {
        const respuesta = await fetch("/actualizacion");

        if (!respuesta.ok) {
            return;
        }

        const datos = await respuesta.json();
        const versionActual = await cargarVersion();

        if (!versionActual || !datos.version) {
            return;
        }

        if (compararVersiones(versionActual, datos.version)) {

            document.getElementById("version-nueva").textContent =
                `Versión ${datos.version}`;

            document.getElementById("mensaje-actualizacion").textContent =
                datos.mensaje || "Nueva versión disponible.";

            const modal = new bootstrap.Modal(
                document.getElementById("modalActualizacion")
            );

            modal.show();

document.getElementById("btn-actualizar").onclick = async () => {

    if (!datos.url) {
        return;
    }

    try {

        const respuesta = await fetch("/actualizar", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                url: datos.url
            })
        });

        const resultado = await respuesta.json();

        if (!respuesta.ok) {
            alert(
                resultado.error ||
                "No se pudo iniciar la actualización."
            );
        }

    } catch (error) {

        console.error(error);

        alert(
            "No se pudo iniciar la actualización."
        );
    }
};
        }

    } catch (error) {
        console.error(
            "No se pudo comprobar si existe una actualización:",
            error
        );
    }
}

cargarVersion();
comprobarActualizacion();
});
