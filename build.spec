# build.spec

from PyInstaller.utils.hooks import collect_all

datas = []
binaries = []
hiddenimports = []

# PyWebView
tmp = collect_all("webview")
datas += tmp[0]
binaries += tmp[1]
hiddenimports += tmp[2]

a = Analysis(
    ["launcher.py"],
    pathex=[],
    binaries=binaries,
    datas=datas + [
        ("templates", "templates"),
        ("static", "static"),
        ("cookies.txt", "."),
    ],
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name="DownLoader Music Youtube",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
)