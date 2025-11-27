from PyQt5.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QPushButton, 
    QLabel, QLineEdit, QFileDialog
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont


class FileSelector(QWidget):
    """Widget reutilizable para seleccionar archivos o carpetas."""
    
    def __init__(self, label_text="Seleccionar:", button_text="Examinar", 
                 mode="directory", file_filter="", parent=None):
        """
        Inicializa el selector de archivos.
        
        Args:
            label_text: Texto del label descriptivo
            button_text: Texto del botón de selección
            mode: "directory" para carpetas, "file" para archivos
            file_filter: Filtro de archivos (ej: "PDF Files (*.pdf)")
            parent: Widget padre
        """
        super().__init__(parent)
        self.mode = mode
        self.file_filter = file_filter
        self._setup_ui(label_text, button_text)
    
    def _setup_ui(self, label_text, button_text):
        """Configura la interfaz del selector."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)
        
        # Label descriptivo
        self.label = QLabel(label_text)
        self.label.setFont(QFont("Segoe UI", 10))
        layout.addWidget(self.label)
        
        # Layout horizontal para input y botón
        input_layout = QHBoxLayout()
        input_layout.setSpacing(10)
        
        # Campo de texto para mostrar ruta
        self.path_input = QLineEdit()
        self.path_input.setPlaceholderText("Ninguna carpeta seleccionada..." 
                                          if self.mode == "directory" 
                                          else "Ningún archivo seleccionado...")
        self.path_input.setReadOnly(True)
        self.path_input.setMinimumHeight(35)
        input_layout.addWidget(self.path_input, 1)
        
        # Botón de selección
        self.select_button = QPushButton(button_text)
        self.select_button.setFixedSize(120, 35)
        self.select_button.setCursor(Qt.PointingHandCursor)
        self.select_button.clicked.connect(self._on_select_clicked)
        input_layout.addWidget(self.select_button)
        
        layout.addLayout(input_layout)
    
    def _on_select_clicked(self):
        """Handler del botón de selección."""
        if self.mode == "directory":
            path = QFileDialog.getExistingDirectory(
                self,
                "Seleccionar Carpeta",
                "",
                QFileDialog.ShowDirsOnly | QFileDialog.DontResolveSymlinks
            )
        else:  # mode == "file"
            path, _ = QFileDialog.getOpenFileName(
                self,
                "Seleccionar Archivo",
                "",
                self.file_filter
            )
        
        if path:
            self.path_input.setText(path)
    
    def get_path(self):
        """
        Retorna la ruta seleccionada.
        
        Returns:
            str: Ruta del archivo o carpeta, o None si no hay selección
        """
        path = self.path_input.text()
        return path if path and path != self.path_input.placeholderText() else None
    
    def set_path(self, path):
        """
        Establece una ruta programáticamente.
        
        Args:
            path: Ruta a establecer
        """
        self.path_input.setText(path)
    
    def clear(self):
        """Limpia la selección actual."""
        self.path_input.clear()