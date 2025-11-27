import sys
from pathlib import Path
from PyQt5.QtWidgets import QApplication
from gui.main_window import MainWindow

def main():
    print("[DEBUG] Iniciando aplicación...")

    app = QApplication(sys.argv)
    print("[DEBUG] QApplication creada")

    # Detectar carpeta base
    base_path = Path(__file__).parent / "gui"
    print(f"[DEBUG] Ejecutando desde desarrollo: base_path={base_path}")

    # Crear ventana principal
    window = MainWindow()
    window.show()
    print("[DEBUG] MainWindow mostrada")

    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
