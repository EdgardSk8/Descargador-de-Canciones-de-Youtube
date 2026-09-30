import threading
import time
import webview

from app import app


def iniciar_flask():
    app.run(
        host="127.0.0.1",
        port=5000,
        debug=False,
        use_reloader=False
    )


if __name__ == "__main__":
    threading.Thread(
        target=iniciar_flask,
        daemon=True
    ).start()

    time.sleep(1)

    webview.create_window(
        "Descargador de Música",
        "http://127.0.0.1:5000",
        width=900,
        height=600,
        resizable=True
    )

    webview.start()