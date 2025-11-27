import sys
import winsound
from PyQt5.QtWidgets import (
    QMainWindow, QApplication, QTabWidget,
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton
)
from PyQt5.QtCore import pyqtSignal, Qt
from PyQt5.QtGui import QIcon
from pathlib import Path

from gui.themes.theme_manager import ThemeManager
from gui.tab_renovaciones import TabRenovaciones
from gui.tab_contratos import TabContratos


class MainWindow(QMainWindow):
    theme_changed = pyqtSignal()

    def __init__(self):
        super().__init__()

        print("[DEBUG] Inicializando MainWindow...")

        # Definir base path
        self.base_path = Path(__file__).parent.resolve()
        print(f"[DEBUG] Ejecutando desde: base_path={self.base_path}")

        # Theme Manager
        self.theme_manager = ThemeManager(self.base_path / "themes")
        print(f"[DEBUG] ThemeManager inicializado con path: {self.base_path / 'themes'}")

        # Botón de tema
        self.theme_button = QPushButton(self.theme_manager.get_theme_icon())
        self.theme_button.setFixedSize(40, 25)
        self.theme_button.setCursor(Qt.PointingHandCursor)
        self.theme_button.clicked.connect(self._on_theme_button_clicked)

        # Tabs
        self.tabs = QTabWidget()
        self.tabs.currentChanged.connect(self._on_tab_changed)

        # Crear tabs
        self.tab_renovaciones = TabRenovaciones(self)
        self.tab_contratos = TabContratos(self)

        self.tabs.addTab(self.tab_renovaciones, "Renovaciones")
        self.tabs.addTab(self.tab_contratos, "Contratos")

        # Layout principal con botón de tema arriba
        container_widget = QWidget()
        container_layout = QVBoxLayout(container_widget)
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.setSpacing(0)

        # Layout superior para botón
        top_layout = QHBoxLayout()
        top_layout.setContentsMargins(5, 5, 5, 5)
        top_layout.addStretch()
        top_layout.addWidget(self.theme_button, alignment=Qt.AlignRight)

        container_layout.addLayout(top_layout)
        container_layout.addWidget(self.tabs)
        self.setCentralWidget(container_widget)

        # Aplicar tema inicial
        self._apply_theme()
        self.theme_changed.emit()

        self.setWindowTitle("Gestión de Renovaciones y Contratos")
        icon_path = self.base_path / "resources" / "app.ico"
        self.setWindowIcon(QIcon(str(icon_path)))

        # Reproducir sonido de inicio
        self._play_startup_sound()

    def _play_startup_sound(self):
        """Reproduce el sonido de inicio del sistema."""
        try:
            winsound.MessageBeep(winsound.MB_ICONASTERISK)
            print("[DEBUG] Sonido de inicio reproducido")
        except Exception as e:
            print(f"[WARNING] No se pudo reproducir sonido de inicio: {e}")

    def _play_tab_change_sound(self):
        """Reproduce el sonido de cambio de tab."""
        try:
            winsound.MessageBeep(winsound.MB_ICONQUESTION)
            print("[DEBUG] Sonido de cambio de tab reproducido")
        except Exception as e:
            print(f"[WARNING] No se pudo reproducir sonido de cambio de tab: {e}")

    def play_button_sound(self):
        """Reproduce el sonido de clic de botón. Método público para que los tabs lo usen."""
        try:
            winsound.MessageBeep(winsound.MB_ICONEXCLAMATION)
            print("[DEBUG] Sonido de botón reproducido")
        except Exception as e:
            print(f"[WARNING] No se pudo reproducir sonido de botón: {e}")

    def _on_theme_button_clicked(self):
        """Alternar tema y actualizar icono y tabs."""
        new_theme = self.theme_manager.toggle_theme()
        print(f"[DEBUG] Tema cambiado a: {new_theme}")
        self.theme_button.setText(self.theme_manager.get_theme_icon())
        
        # Aplicar tema y notificar a los tabs
        self._apply_theme()
        self.theme_changed.emit()

    def _on_tab_changed(self, index):
        """Reproducir sonido al cambiar de tab."""
        self._play_tab_change_sound()
        print(f"[DEBUG] Cambio a tab {index}")

    def _apply_theme(self):
        """Aplica el stylesheet del tema actual a la ventana principal."""
        theme = self.theme_manager.get_theme()
        colors = theme.get("colors", {})
        components = theme.get("components", {})

        # ---- COLORES BASE ----
        text_colors = colors.get("text", {})
        primary_text = text_colors.get("primary", "#E2E8F0")

        # ---- COLORES DE BOTONES (desde el JSON del tema) ----
        button_colors = components.get("button", {})
        button_bg = button_colors.get("background", colors.get("primary", "#38BDF8"))
        button_text = button_colors.get("text", text_colors.get("primary", "#FFFFFF"))
        button_hover = button_colors.get("hover", colors.get("accent", "#0EA5E9"))
        button_pressed = colors.get("primary", "#0284C7")

        # Ajuste de seguridad: evita fondo y texto del mismo color
        if button_bg.lower() == button_text.lower():
            button_text = "#FFFFFF" if button_bg.startswith("#0") or button_bg.startswith("#1") else "#000000"

        # ---- STYLESHEET COMPLETO ----
        stylesheet = f"""
            QMainWindow {{
                background-color: {colors.get('background', '#1E293B')};
            }}
            
            QWidget {{
                background-color: {colors.get('background', '#1E293B')};
                color: {primary_text};
                font-family: "Segoe UI", Arial, sans-serif;
            }}
            
            QTabWidget::pane {{
                border: 1px solid {colors.get('border', '#334155')};
                background-color: {colors.get('surface', colors.get('background', '#1E293B'))};
            }}
            
            QTabBar::tab {{
                background-color: {colors.get('surface', '#0F172A')};
                color: {primary_text};
                padding: 8px 16px;
                border: 1px solid {colors.get('border', '#334155')};
                border-bottom: none;
            }}
            
            QTabBar::tab:selected {{
                background-color: {colors.get('primary', '#3B82F6')};
                color: white;
            }}
            
            QTabBar::tab:hover {{
                background-color: {button_hover};
            }}
            
            QPushButton {{
                background-color: {button_bg};
                color: {button_text};
                border: none;
                border-radius: 5px;
                padding: 8px 16px;
                font-weight: bold;
            }}
            
            QPushButton:hover {{
                background-color: {button_hover};
            }}
            
            QPushButton:pressed {{
                background-color: {button_pressed};
            }}
            
            QPushButton:disabled {{
                background-color: {colors.get('border', '#475569')};
                color: {text_colors.get('muted', '#64748B')};
            }}
            
            QLabel {{
                color: {primary_text};
                background-color: transparent;
            }}
            
            QLineEdit, QTextEdit {{
                background-color: {components.get('input', {}).get('background', '#0F172A')};
                color: {primary_text};
                border: 1px solid {colors.get('border', '#334155')};
                border-radius: 4px;
                padding: 6px;
            }}
            
            QLineEdit:focus, QTextEdit:focus {{
                border: 2px solid {colors.get('primary', '#3B82F6')};
            }}
            
            QFrame[frameShape="4"] {{  /* HLine */
                background-color: {colors.get('border', '#334155')};
                max-height: 1px;
            }}
            
            QScrollBar:vertical {{
                background-color: {colors.get('surface', '#0F172A')};
                width: 12px;
                border-radius: 6px;
            }}
            
            QScrollBar::handle:vertical {{
                background-color: {colors.get('border', '#334155')};
                border-radius: 6px;
                min-height: 20px;
            }}
            
            QScrollBar::handle:vertical:hover {{
                background-color: {button_hover};
            }}
            
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                height: 0px;
            }}
        """

        self.setStyleSheet(stylesheet)
        print(f"[DEBUG] Stylesheet aplicado para tema: {self.theme_manager.current_theme}")


    def get_theme_colors(self):
        """Obtiene colores del tema actual."""
        return self.theme_manager.get_theme().get("colors", {})

    def update_footer(self, message: str):
        """Actualizar mensajes en footer."""
        print(f"[DEBUG] Footer actualizado: {message}")