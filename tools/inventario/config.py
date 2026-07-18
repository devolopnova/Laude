from pathlib import Path

# Carpeta raíz del proyecto Guía Regalos
ROOT_DIR = Path(__file__).resolve().parents[2]

# Carpetas que no queremos analizar
EXCLUDED_DIRS = {
    ".git",
    ".claude",
    "node_modules",
    "tools",
    ".next",
}

# Extensiones de archivos que queremos encontrar
HTML_EXTENSIONS = {
    ".html",
    ".htm"
}

# Carpeta donde se guardará el inventario
INVENTARIO_DIR = ROOT_DIR / "inventario"