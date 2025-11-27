from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QProgressBar
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont


class ProgressDialog(QDialog):
    """Diálogo modal para mostrar progreso de operaciones."""
    
    # Señal para cancelar operación
    cancelled = pyqtSignal()
    
    def __init__(self, title="Procesando", message="Por favor espere...", 
                 show_cancel=True, parent=None):
        """
        Inicializa el diálogo de progreso.
        
        Args:
            title: Título de la ventana
            message: Mensaje descriptivo
            show_cancel: Mostrar botón de cancelar
            parent: Widget padre
        """
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setModal(True)
        self.setFixedSize(450, 200)
        self.show_cancel = show_cancel
        self._setup_ui(message)
        
        # Flags de ventana
        self.setWindowFlags(
            Qt.Dialog | 
            Qt.CustomizeWindowHint | 
            Qt.WindowTitleHint
        )
    
    def _setup_ui(self, message):
        """Configura la interfaz del diálogo."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(20)
        
        # Mensaje principal
        self.message_label = QLabel(message)
        self.message_label.setFont(QFont("Segoe UI", 11))
        self.message_label.setWordWrap(True)
        self.message_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.message_label)
        
        # Barra de progreso
        self.progress_bar = QProgressBar()
        self.progress_bar.setMinimum(0)
        self.progress_bar.setMaximum(100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setFixedHeight(25)
        layout.addWidget(self.progress_bar)
        
        # Label de detalles (archivo actual, etc.)
        self.detail_label = QLabel("")
        self.detail_label.setFont(QFont("Segoe UI", 9))
        self.detail_label.setAlignment(Qt.AlignCenter)
        self.detail_label.setStyleSheet("color: #94A3B8;")
        layout.addWidget(self.detail_label)
        
        layout.addStretch()
        
        # Botón cancelar (opcional)
        if self.show_cancel:
            button_layout = QHBoxLayout()
            button_layout.addStretch()
            
            self.cancel_button = QPushButton("Cancelar")
            self.cancel_button.setFixedSize(100, 35)
            self.cancel_button.setCursor(Qt.PointingHandCursor)
            self.cancel_button.clicked.connect(self._on_cancel)
            button_layout.addWidget(self.cancel_button)
            
            button_layout.addStretch()
            layout.addLayout(button_layout)
        
        # Estilo del diálogo
        self.setStyleSheet("""
            QDialog {
                background-color: #1B2233;
            }
            QLabel {
                color: #E2E8F0;
            }
            QProgressBar {
                background-color: #1E293B;
                border: 1px solid #334155;
                border-radius: 5px;
                text-align: center;
                color: #E2E8F0;
            }
            QProgressBar::chunk {
                background-color: #38BDF8;
                border-radius: 4px;
            }
            QPushButton {
                background-color: #F43F5E;
                color: #FFFFFF;
                border: none;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #DC2626;
            }
        """)
    
    def update_progress(self, value: int, detail: str = ""):
        """
        Actualiza el progreso y detalle.
        
        Args:
            value: Valor de progreso (0-100)
            detail: Texto de detalle opcional
        """
        self.progress_bar.setValue(value)
        if detail:
            self.detail_label.setText(detail)
    
    def set_message(self, message: str):
        """
        Cambia el mensaje principal.
        
        Args:
            message: Nuevo mensaje
        """
        self.message_label.setText(message)
    
    def set_indeterminate(self, indeterminate: bool = True):
        """
        Cambia el modo de la barra de progreso.
        
        Args:
            indeterminate: True para progreso indeterminado
        """
        if indeterminate:
            self.progress_bar.setMaximum(0)  # Modo indeterminado
        else:
            self.progress_bar.setMaximum(100)
    
    def _on_cancel(self):
        """Handler del botón cancelar."""
        self.cancelled.emit()
        self.reject()
    
    def closeEvent(self, event):
        """Previene cierre accidental del diálogo."""
        if self.show_cancel:
            self._on_cancel()
        event.ignore()