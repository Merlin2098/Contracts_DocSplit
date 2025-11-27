from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
    QLabel, QFrame, QProgressBar
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QFont
from gui.widgets.file_selector import FileSelector
from gui.widgets.log_viewer import LogViewer
from controllers.renovaciones_controller import (
    procesar_renovaciones,
    diagnosticar_renovaciones
)


class ProcessThread(QThread):
    """Thread para ejecutar el procesamiento completo sin bloquear la UI."""
    
    progress_updated = pyqtSignal(int, int, str, int)  # current, total, message, percentage
    log_message = pyqtSignal(str, str)  # mensaje, tipo
    process_finished = pyqtSignal(dict)  # resultado
    
    def __init__(self, carpeta_entrada):
        super().__init__()
        self.carpeta_entrada = carpeta_entrada
    
    def run(self):
        """Ejecuta el procesamiento completo en segundo plano."""
        def progress_callback(current, total, message, percentage):
            self.progress_updated.emit(current, total, message, percentage)
        
        def log_gui_callback(mensaje, tipo):
            self.log_message.emit(mensaje, tipo)
        
        resultado = procesar_renovaciones(
            self.carpeta_entrada, 
            progress_callback,
            log_gui_callback
        )
        self.process_finished.emit(resultado)


class DiagnosticThread(QThread):
    """Thread para ejecutar solo el diagnóstico (genera JSONs)."""
    
    progress_updated = pyqtSignal(int, int, str, int)  # current, total, message, percentage
    log_message = pyqtSignal(str, str)  # mensaje, tipo
    process_finished = pyqtSignal(dict)  # resultado
    
    def __init__(self, carpeta_entrada):
        super().__init__()
        self.carpeta_entrada = carpeta_entrada
    
    def run(self):
        """Ejecuta el diagnóstico en segundo plano."""
        def progress_callback(current, total, message, percentage):
            self.progress_updated.emit(current, total, message, percentage)
        
        def log_gui_callback(mensaje, tipo):
            self.log_message.emit(mensaje, tipo)
        
        resultado = diagnosticar_renovaciones(
            self.carpeta_entrada, 
            progress_callback,
            log_gui_callback
        )
        self.process_finished.emit(resultado)


class TabRenovaciones(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.main_window = parent
        self.process_thread = None
        self.diagnostic_thread = None
        self._setup_ui()

        if self.main_window:
            self.main_window.theme_changed.connect(self._apply_theme)

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # Título
        title = QLabel("📄 Procesamiento de Renovaciones")
        title.setFont(QFont("Segoe UI", 14, QFont.Bold))
        layout.addWidget(title)

        # Descripción
        description = QLabel(
            "Detecta secciones, genera JSON de estructura y extrae PDFs individuales.\n"
            "Usa 'Diagnosticar' para revisar la detección sin extraer archivos."
        )
        description.setWordWrap(True)
        layout.addWidget(description)

        # Separador
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setFrameShadow(QFrame.Sunken)
        layout.addWidget(separator)

        # Selector de carpeta
        self.file_selector = FileSelector(
            label_text="Carpeta de entrada:", 
            button_text="📂", 
            mode="directory"
        )
        layout.addWidget(self.file_selector)

        # Botones de acción
        button_layout = QHBoxLayout()
        button_layout.setSpacing(15)
        button_layout.addStretch()

        # Botón Diagnosticar
        self.diagnostic_button = QPushButton("🔍 Diagnosticar")
        self.diagnostic_button.setFixedSize(200, 50)
        self.diagnostic_button.setFont(QFont("Segoe UI", 11, QFont.Bold))
        self.diagnostic_button.setCursor(Qt.PointingHandCursor)
        self.diagnostic_button.clicked.connect(self._on_diagnostic_clicked)
        self.diagnostic_button.setToolTip("Genera JSONs con estructura de secciones (no extrae PDFs)")
        button_layout.addWidget(self.diagnostic_button)

        # Botón Procesar
        self.process_button = QPushButton("✅ Procesar")
        self.process_button.setFixedSize(200, 50)
        self.process_button.setFont(QFont("Segoe UI", 11, QFont.Bold))
        self.process_button.setCursor(Qt.PointingHandCursor)
        self.process_button.clicked.connect(self._on_process_clicked)
        self.process_button.setToolTip("Proceso completo: Detecta, genera JSON y extrae PDFs")
        button_layout.addWidget(self.process_button)

        button_layout.addStretch()
        layout.addLayout(button_layout)

        # Barra de progreso integrada
        self.progress_container = QWidget()
        self.progress_container.setVisible(False)
        progress_layout = QVBoxLayout(self.progress_container)
        progress_layout.setContentsMargins(0, 10, 0, 10)
        progress_layout.setSpacing(8)

        self.progress_label = QLabel("⏳ Preparando procesamiento...")
        self.progress_label.setFont(QFont("Segoe UI", 10))
        self.progress_label.setAlignment(Qt.AlignLeft)
        progress_layout.addWidget(self.progress_label)

        self.progress_bar = QProgressBar()
        self.progress_bar.setMinimum(0)
        self.progress_bar.setMaximum(100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setFixedHeight(25)
        self.progress_bar.setFormat("%p% - %v/%m archivos")
        progress_layout.addWidget(self.progress_bar)

        self.progress_bar.setStyleSheet("""
            QProgressBar {
                background-color: #1E293B;
                border: 1px solid #334155;
                border-radius: 5px;
                text-align: center;
                color: #E2E8F0;
                font-weight: bold;
            }
            QProgressBar::chunk {
                background-color: #38BDF8;
                border-radius: 4px;
            }
        """)

        layout.addWidget(self.progress_container)

        # Separador antes del log
        separator2 = QFrame()
        separator2.setFrameShape(QFrame.HLine)
        separator2.setFrameShadow(QFrame.Sunken)
        layout.addWidget(separator2)

        # Log viewer
        log_label = QLabel("📋 Registro de Actividad:")
        log_label.setFont(QFont("Segoe UI", 10, QFont.Bold))
        layout.addWidget(log_label)

        self.log_viewer = LogViewer()
        layout.addWidget(self.log_viewer, 1)

        self.log_viewer.add_log("Sistema inicializado. Esperando selección de carpeta...", "info")

    def _apply_theme(self):
        """Aplica solo los estilos necesarios SIN sobrescribir los botones."""
        if not self.main_window:
            return
        colors = self.main_window.get_theme_colors()

        # Solo aplicar estilo al separador
        separator_style = f"background-color: {colors.get('border', '#ccc')};"
        for widget in self.findChildren(QFrame):
            if widget.frameShape() == QFrame.HLine:
                widget.setStyleSheet(separator_style)

        # Aplicar fondo del tab
        self.setStyleSheet(f"background-color: {colors.get('background', '#1E293B')};")

    def _play_button_sound(self):
        """Reproduce el sonido de clic de botón."""
        if self.main_window:
            self.main_window.play_button_sound()

    def _validate_folder(self):
        folder_path = self.file_selector.get_path()
        if not folder_path:
            self.log_viewer.add_log("⚠ Error: Debe seleccionar una carpeta.", "warning")
            return None
        return folder_path

    def _on_diagnostic_clicked(self):
        """Handler del botón Diagnosticar."""
        self._play_button_sound()
        
        folder_path = self._validate_folder()
        if not folder_path:
            return
        
        if hasattr(self.log_viewer, 'clear_logs'):
            self.log_viewer.clear_logs()
        
        self.log_viewer.add_log("🔍 Iniciando diagnóstico de renovaciones...", "info")
        self.log_viewer.add_log("", "info")
        
        # Deshabilitar botones durante procesamiento
        self.diagnostic_button.setEnabled(False)
        self.process_button.setEnabled(False)
        
        # Mostrar barra de progreso
        self.progress_container.setVisible(True)
        self.progress_bar.setValue(0)
        self.progress_bar.setMaximum(100)
        self.progress_label.setText("⏳ Diagnosticando...")
        
        # Crear thread de diagnóstico
        self.diagnostic_thread = DiagnosticThread(folder_path)
        self.diagnostic_thread.progress_updated.connect(self._on_progress_updated)
        self.diagnostic_thread.log_message.connect(self._on_log_message)
        self.diagnostic_thread.process_finished.connect(self._on_diagnostic_finished)
        
        # Iniciar diagnóstico
        self.diagnostic_thread.start()

    def _on_process_clicked(self):
        """Handler del botón Procesar."""
        self._play_button_sound()
        
        folder_path = self._validate_folder()
        if not folder_path:
            return
        
        if hasattr(self.log_viewer, 'clear_logs'):
            self.log_viewer.clear_logs()
        
        self.log_viewer.add_log("🚀 Iniciando procesamiento completo de renovaciones...", "info")
        self.log_viewer.add_log("", "info")
        
        # Deshabilitar botones durante procesamiento
        self.diagnostic_button.setEnabled(False)
        self.process_button.setEnabled(False)
        
        # Mostrar barra de progreso
        self.progress_container.setVisible(True)
        self.progress_bar.setValue(0)
        self.progress_bar.setMaximum(100)
        self.progress_label.setText("⏳ Preparando procesamiento...")
        
        # Crear thread de procesamiento
        self.process_thread = ProcessThread(folder_path)
        self.process_thread.progress_updated.connect(self._on_progress_updated)
        self.process_thread.log_message.connect(self._on_log_message)
        self.process_thread.process_finished.connect(self._on_process_finished)
        
        # Iniciar procesamiento
        self.process_thread.start()
    
    def _on_progress_updated(self, current, total, message, percentage):
        """Actualiza la barra de progreso integrada."""
        self.progress_bar.setMaximum(total)
        self.progress_bar.setValue(current)
        self.progress_label.setText(f"⏳ {message}")
    
    def _on_log_message(self, mensaje, tipo):
        """Recibe mensajes del controller y los muestra en el LogViewer."""
        self.log_viewer.add_log(mensaje, tipo)
    
    def _on_diagnostic_finished(self, resultado):
        """Maneja la finalización del diagnóstico."""
        # Habilitar botones nuevamente
        self.diagnostic_button.setEnabled(True)
        self.process_button.setEnabled(True)
        
        # Ocultar barra de progreso
        self.progress_container.setVisible(False)
        
        # Mostrar resultados
        if resultado['exitoso']:
            self.log_viewer.add_log("", "info")
            self.log_viewer.add_log(f"📄 JSON consolidado: {resultado.get('json_generado', 'diagnostico_rangos.json')}", "info")
            self.log_viewer.add_log(f"📂 Carpeta: {resultado['carpeta_salida']}", "info")
            
            if self.main_window:
                archivos = resultado.get('archivos_procesados', 0)
                self.main_window.update_footer(
                    f"Diagnóstico: JSON consolidado con {archivos} archivos en {resultado['duracion']}"
                )
        else:
            self.log_viewer.add_log("", "info")
            self.log_viewer.add_log(f"❌ ERROR: {resultado['mensaje']}", "error")
        
        # Limpiar thread
        self.diagnostic_thread = None
    
    def _on_process_finished(self, resultado):
        """Maneja la finalización del procesamiento completo."""
        # Habilitar botones nuevamente
        self.diagnostic_button.setEnabled(True)
        self.process_button.setEnabled(True)
        
        # Ocultar barra de progreso
        self.progress_container.setVisible(False)
        
        # Mostrar resultados
        if resultado['exitoso']:
            self.log_viewer.add_log("", "info")
            self.log_viewer.add_log(f"📂 Carpeta de salida: {resultado['carpeta_salida']}", "info")
            self.log_viewer.add_log(f"📄 Log de interfaz: {resultado['ruta_log_interfaz']}", "info")
            self.log_viewer.add_log(f"📄 Log técnico: {resultado['ruta_log_proceso']}", "info")
            
            if self.main_window:
                self.main_window.update_footer(
                    f"Renovaciones: {resultado['archivos_procesados']} procesados en {resultado['duracion']}"
                )
        else:
            self.log_viewer.add_log("", "info")
            self.log_viewer.add_log(f"❌ ERROR: {resultado['mensaje']}", "error")
        
        # Limpiar thread
        self.process_thread = None