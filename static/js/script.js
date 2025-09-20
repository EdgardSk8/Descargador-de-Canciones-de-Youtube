document.addEventListener("DOMContentLoaded", () => {
    const BtnBuscarCancion = document.querySelector(".Btn-Buscar-Cancion");
    const BtnPegar = document.querySelector(".Btn-Pegar");
    const input = document.querySelector("#youtube-url");
    const previewDiv = document.getElementById("Informacion-Cancion");
    const loadingDiv = document.querySelector(".loading");
    const progressBar = document.getElementById("barra-progreso");
    const DivContenedorBarra = document.getElementById("Contenedor-Barra-Progreso");
    const TextoProgreso = document.querySelector(".informacion-progreso");

    // -----------------------------
    // Funciones
    // -----------------------------

    async function obtenerInfo(url) {
        try {
            const res = await fetch("/informacion", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ url })
            });
            if (!res.ok) throw await res.json();
            return await res.json();
        } catch (err) {
            alert("Error al obtener información: " + (err.error || err));
            throw err;
        }
    }

    function mostrarPreview(videoInfo) {
        const duration = videoInfo.duration || 0;
        const minutes = Math.floor(duration / 60);
        const seconds = duration % 60;
        const durationFormatted = `${minutes}:${seconds.toString().padStart(2,"0")}`;

        previewDiv.innerHTML = `
            <h3 class="Titulo-Cancion">${videoInfo.title}</h3>
            <p class="Informacion-Cancion-p">
                <strong>Duración:</strong> ${durationFormatted} | 
                <strong>Uploader:</strong> ${videoInfo.uploader}
            </p>
            ${videoInfo.thumbnail ? `<img src="${videoInfo.thumbnail}" class="Imagen-Caratula">` : ""}
            <div class="Contenedor-Renombrar">
                <label for="rename-title">Renombrar archivo:</label>
                <input type="text" id="rename-title" 
                    value="${videoInfo.title.replace(/[<>:"/\\|?*]+/g,'')}">
            </div>
            <button class="Btn-Descargar-Cancion">
                Descargar Canción 🎵
            </button>
        `;
        previewDiv.style.display = "block";

        // Un único listener aquí
        document.querySelector(".Btn-Descargar-Cancion").addEventListener("click", () => {
            const renameInput = document.querySelector("#rename-title");
            const customTitle = renameInput.value.trim() || videoInfo.title;
            iniciarDescarga(input.value.trim(), customTitle);
            toggleLoading(false);
            DivContenedorBarra.style.display = "block";
            TextoProgreso.style.display =  "block";
            updateProgress(0, "Descargando... 0%");
        });
    }

    async function iniciarDescarga(url, customTitle) {
        toggleLoading(true);
        try {
            const res = await fetch("/descargar", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ url, custom_title: customTitle })
            });
            const data = await res.json();
            if (!res.ok) throw data;

            const taskId = data.task_id;

            const interval = setInterval(async () => {
                const progresoRes = await fetch(`/progreso/${taskId}`);
                const progresoData = await progresoRes.json();

                if (progresoData.error) {
                    clearInterval(interval);
                    alert("Error en la descarga: " + progresoData.error);
                    toggleLoading(false);
                    resetProgress();
                    return;
                }

                const porcentaje = progresoData.porcentaje || 0;
                const texto = progresoData.done ? "Completado ✔" : `Descargando... ${porcentaje}%`;
                updateProgress(porcentaje, texto);

                if (progresoData.done) {
                    clearInterval(interval);
                    const a = document.createElement("a");
                    a.href = `/download_file/${taskId}`;
                    a.download = progresoData.custom_title + ".m4a";
                    document.body.appendChild(a);
                    a.click();
                    a.remove();

                    toggleLoading(false);
                    //resetProgress();
                }
            }, 500);

        } catch (err) {
            alert("Error al iniciar descarga: " + (err.error || err));
            toggleLoading(false);
            resetProgress();
        }
    }

    function toggleLoading(show) {
        loadingDiv.style.display = show ? "block" : "none";
    }

    function updateProgress(porcentaje, texto) {
        progressBar.style.width = `${porcentaje}%`;
        TextoProgreso.textContent = texto;
    }

    function resetProgress() {
        progressBar.style.width = "0%";
        TextoProgreso.textContent = "";
        DivContenedorBarra.style.display = "none";
    }

    // -----------------------------
    // Listeners
    // -----------------------------
    BtnBuscarCancion.addEventListener("click", async () => {
        const url = input.value.trim();
        if(!url) { alert("Por favor pega un enlace de YouTube."); return; }
        previewDiv.innerHTML = '';
        resetProgress();

        try {
            toggleLoading(true);
            const videoInfo = await obtenerInfo(url);
            mostrarPreview(videoInfo);
        } catch (err) {
            console.error(err);
        } finally {
            toggleLoading(false);
        }
    });

    BtnPegar.addEventListener("click", async () => {
        try {
            const text = await navigator.clipboard.readText();
            if(text) input.value = text.trim();
            else alert("El portapapeles está vacío.");
        } catch(err) {
            alert("No se pudo acceder al portapapeles.");
            console.error(err);
        }
    });
});
