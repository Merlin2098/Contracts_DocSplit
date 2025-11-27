from PyQt5.QtWidgets import QWidget, QVBoxLayout, QTextEdit
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QTextCursor
from datetime import datetime


class LogViewer(QWidget):
    """Widget para visualizar logs con formato y colores."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
        self._log_colors = {
            "info": "#38BDF8",      # Azul
            "success": "#22C55E",   # Verde
            "warning": "#FBBF24",   # Amarillo
            "error": "#F43F5E"      # Rojo
        }
    
    def _setup_ui(self):
        """Configura la interfaz del visor de logs."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Área de texto para logs
        self.text_area = QTextEdit()
        self.text_area.setReadOnly(True)
        self.text_area.setFont(QFont("Consolas", 9))
        self.text_area.setMinimumHeight(200)
        
        # Estilo base del text area
        self.text_area.setStyleSheet("""
            QTextEdit {
                background-color: #1E293B;
                color: #E2E8F0;
                border: 1px solid #334155;
                border-radius: 5px;
                padding: 10px;
            }
        """)
        
        layout.addWidget(self.text_area)
    
    def add_log(self, message: str, log_type: str = "info"):
        """
        Agrega un mensaje al log con timestamp y color.
        
        Args:
            message: Mensaje a agregar
            log_type: Tipo de log ("info", "success", "warning", "error")
        """
        timestamp = datetime.now().strftime("%H:%M:%S")
        color = self._log_colors.get(log_type, self._log_colors["info"])
        
        # Formatear mensaje con HTML
        formatted_message = (
            f'<span style="color: #94A3B8;">[{timestamp}]</span> '
            f'<span style="color: {color};">{message}</span>'
        )
        
        # Agregar al final y hacer scroll automático
        self.text_area.append(formatted_message)
        self.text_area.moveCursor(QTextCursor.End)
    
    def clear_logs(self):
        """Limpia todos los logs."""
        self.text_area.clear()
    
    def get_logs(self):
        """
        Retorna todo el contenido de logs como texto plano.
        
        Returns:
            str: Contenido completo del log
        """
        return self.text_area.toPlainText()
    
    def save_logs(self, file_path: str):
        """
        Guarda los logs en un archivo de texto.
        
        Args:
            file_path: Ruta donde guardar el archivo
        """
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(self.get_logs())
            self.add_log(f"Logs guardados en: {file_path}", "success")
        except Exception as e:
            self.add_log(f"Error al guardar logs: {str(e)}", "error")