from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
    QLabel, QFrame, QProgressBar
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QFont
from gui.widgets.file_selector import FileSelector
from gui.widgets.log_viewer import LogViewer
from controllers.contratos_controller import normalizar_contratos, diagnosticar_contratos


class NormalizeThread(QThread):
    """Thread para ejecutar la normalización sin bloquear la UI."""
    
    progress_updated = pyqtSignal(int, int, str, int)  # current, total, message, percentage
    log_message = pyqtSignal(str, str)  # mensaje, tipo
    process_finished = pyqtSignal(dict)  # resultado
    
    def __init__(self, carpeta_entrada):
        super().__init__()
        self.carpeta_entrada = carpeta_entrada
    
    def run(self):
        """Ejecuta la normalización en segundo plano."""
        def progress_callback(current, total, message, percentage):
            self.progress_updated.emit(current, total, message, percentage)
        
        def log_gui_callback(mensaje, tipo):
            self.log_message.emit(mensaje, tipo)
        
        resultado = normalizar_contratos(
            self.carpeta_entrada, 
            progress_callback,
            log_gui_callback
        )
        self.process_finished.emit(resultado)


class DiagnosticThread(QThread):
    """Thread para ejecutar el diagnóstico sin bloquear la UI."""
    
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
        
        resultado = diagnosticar_contratos(
            self.carpeta_entrada,
            progress_callback,
            log_gui_callback
        )
        self.process_finished.emit(resultado)


class TabContratos(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.main_window = parent
        self.normalize_thread = None
        self.diagnostic_thread = None
        self._setup_ui()

        if self.main_window:
            self.main_window.theme_changed.connect(self._apply_theme)

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # Título
        title = QLabel("📋 Procesamiento de Contratos")
        title.setFont(QFont("Segoe UI", 14, QFont.Bold))
        layout.addWidget(title)

        # Descripción
        description = QLabel("Workflow en 3 pasos: Normalizar → Diagnosticar → Procesar")
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

        # Botones de procesamiento (3 pasos)
        button_layout = QHBoxLayout()
        button_layout.setSpacing(15)
        button_layout.addStretch()

        # Botón 1: Normalizar
        self.normalize_button = QPushButton("① Normalizar")
        self.normalize_button.setFixedSize(180, 50)
        self.normalize_button.setFont(QFont("Segoe UI", 11, QFont.Bold))
        self.normalize_button.setCursor(Qt.PointingHandCursor)
        self.normalize_button.clicked.connect(self._on_normalize_clicked)
        self.normalize_button.setToolTip(
            "Paso 1: Normaliza nombres de PDFs\n"
            "Extrae el nombre del trabajador y elimina duplicados"
        )
        button_layout.addWidget(self.normalize_button)

        # Botón 2: Diagnosticar (AHORA SIEMPRE HABILITADO)
        self.diagnose_button = QPushButton("② Diagnosticar")
        self.diagnose_button.setFixedSize(180, 50)
        self.diagnose_button.setFont(QFont("Segoe UI", 11, QFont.Bold))
        self.diagnose_button.setCursor(Qt.PointingHandCursor)
        self.diagnose_button.setEnabled(True)  # ✅ HABILITADO POR DEFECTO
        self.diagnose_button.clicked.connect(self._on_diagnose_clicked)
        self.diagnose_button.setToolTip(
            "Paso 2: Detecta las 12 secciones\n"
            "Genera diagnostico_rangos.json con los rangos detectados"
        )
        button_layout.addWidget(self.diagnose_button)

        # Botón 3: Procesar (deshabilitado hasta completar diagnóstico)
        self.process_button = QPushButton("③ Procesar")
        self.process_button.setFixedSize(180, 50)
        self.process_button.setFont(QFont("Segoe UI", 11, QFont.Bold))
        self.process_button.setCursor(Qt.PointingHandCursor)
        self.process_button.setEnabled(False)  # Habilitado después de diagnosticar
        self.process_button.clicked.connect(self._on_process_clicked)
        self.process_button.setToolTip(
            "Paso 3: Extrae las secciones\n"
            "Crea carpetas individuales con PDFs nombrados correctamente"
        )
        button_layout.addWidget(self.process_button)

        button_layout.addStretch()
        layout.addLayout(button_layout)

        # --- BARRA DE PROGRESO INTEGRADA ---
        self.progress_container = QWidget()
        self.progress_container.setVisible(False)  # Oculta por defecto
        progress_layout = QVBoxLayout(self.progress_container)
        progress_layout.setContentsMargins(0, 10, 0, 10)
        progress_layout.setSpacing(8)

        # Label de estado
        self.progress_label = QLabel("⏳ Preparando...")
        self.progress_label.setFont(QFont("Segoe UI", 10))
        self.progress_label.setAlignment(Qt.AlignLeft)
        progress_layout.addWidget(self.progress_label)

        # Barra de progreso
        self.progress_bar = QProgressBar()
        self.progress_bar.setMinimum(0)
        self.progress_bar.setMaximum(100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setFixedHeight(25)
        self.progress_bar.setFormat("%p% - %v/%m archivos")
        progress_layout.addWidget(self.progress_bar)

        # Estilo de la barra de progreso
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

        # Aplicar fondo del tab (sin tocar los botones)
        self.setStyleSheet(f"background-color: {colors.get('background', '#1E293B')};")

    def _play_button_sound(self):
        """Reproduce el sonido de clic de botón."""
        if self.main_window:
            self.main_window.play_button_sound()

    def _validate_folder(self):
        folder_path = self.file_selector.get_path()
        if not folder_path:
            self.log_viewer.add_log("⚠️ Error: Debe seleccionar una carpeta.", "warning")
            return None
        return folder_path

    def _on_normalize_clicked(self):
        """Handler del botón Normalizar (Paso 1)."""
        self._play_button_sound()
        
        folder_path = self._validate_folder()
        if not folder_path:
            return
        
        # Limpiar log anterior si el método existe
        if hasattr(self.log_viewer, 'clear_logs'):
            self.log_viewer.clear_logs()
        
        self.log_viewer.add_log("🔧 Paso 1: Normalizando nombres de archivos...", "info")
        self.log_viewer.add_log("", "info")
        
        # Deshabilitar botones durante procesamiento
        self.normalize_button.setEnabled(False)
        self.diagnose_button.setEnabled(False)
        self.process_button.setEnabled(False)
        
        # Mostrar y resetear barra de progreso
        self.progress_container.setVisible(True)
        self.progress_bar.setValue(0)
        self.progress_bar.setMaximum(100)
        self.progress_label.setText("⏳ Preparando normalización...")
        
        # Crear thread de normalización
        self.normalize_thread = NormalizeThread(folder_path)
        self.normalize_thread.progress_updated.connect(self._on_progress_updated)
        self.normalize_thread.log_message.connect(self._on_log_message)
        self.normalize_thread.process_finished.connect(self._on_normalize_finished)
        
        # Iniciar procesamiento
        self.normalize_thread.start()
    
    def _on_diagnose_clicked(self):
        """Handler del botón Diagnosticar (Paso 2)."""
        self._play_button_sound()
        
        folder_path = self._validate_folder()
        if not folder_path:
            return
        
        # Limpiar log anterior
        if hasattr(self.log_viewer, 'clear_logs'):
            self.log_viewer.clear_logs()
        
        self.log_viewer.add_log("🔍 Paso 2: Diagnosticando secciones...", "info")
        self.log_viewer.add_log("", "info")
        
        # Deshabilitar botones durante procesamiento
        self.normalize_button.setEnabled(False)
        self.diagnose_button.setEnabled(False)
        self.process_button.setEnabled(False)
        
        # Mostrar y resetear barra de progreso
        self.progress_container.setVisible(True)
        self.progress_bar.setValue(0)
        self.progress_bar.setMaximum(100)
        self.progress_label.setText("⏳ Preparando diagnóstico...")
        
        # Crear thread de diagnóstico
        self.diagnostic_thread = DiagnosticThread(folder_path)
        self.diagnostic_thread.progress_updated.connect(self._on_progress_updated)
        self.diagnostic_thread.log_message.connect(self._on_log_message)
        self.diagnostic_thread.process_finished.connect(self._on_diagnose_finished)
        
        # Iniciar procesamiento
        self.diagnostic_thread.start()
    
    def _on_process_clicked(self):
        """Handler del botón Procesar (Paso 3)."""
        self._play_button_sound()
        self.log_viewer.add_log("⏳ Paso 3: Procesamiento pendiente de implementación (Fase 5)", "warning")
    
    def _on_progress_updated(self, current, total, message, percentage):
        """Actualiza la barra de progreso integrada."""
        self.progress_bar.setMaximum(total)
        self.progress_bar.setValue(current)
        self.progress_label.setText(f"⏳ {message}")
    
    def _on_log_message(self, mensaje, tipo):
        """Recibe mensajes del controller y los muestra en el LogViewer."""
        self.log_viewer.add_log(mensaje, tipo)
    
    def _on_normalize_finished(self, resultado):
        """Maneja la finalización de la normalización."""
        # Habilitar botones
        self.normalize_button.setEnabled(True)
        self.diagnose_button.setEnabled(True)  # Siempre habilitado
        
        # Ocultar barra de progreso
        self.progress_container.setVisible(False)
        
        # Mostrar resultados adicionales en el log
        if resultado['exitoso']:
            self.log_viewer.add_log("", "info")
            self.log_viewer.add_log(f"📝 Log generado: {resultado['ruta_log']}", "info")
            
            # Actualizar footer
            if self.main_window:
                self.main_window.update_footer(
                    f"Contratos: {resultado['archivos_normalizados']} normalizados en {resultado['duracion']}"
                )
        else:
            self.log_viewer.add_log("", "info")
            self.log_viewer.add_log(f"❌ ERROR: {resultado['mensaje']}", "error")
        
        # Limpiar thread
        self.normalize_thread = None
    
    def _on_diagnose_finished(self, resultado):
        """Maneja la finalización del diagnóstico."""
        # Habilitar botones
        self.normalize_button.setEnabled(True)
        self.diagnose_button.setEnabled(True)
        
        # Si diagnóstico exitoso, habilitar procesamiento
        if resultado['exitoso']:
            self.process_button.setEnabled(True)
        
        # Ocultar barra de progreso
        self.progress_container.setVisible(False)
        
        # Mostrar resultados adicionales en el log
        if resultado['exitoso']:
            self.log_viewer.add_log("", "info")
            self.log_viewer.add_log(f"📝 Log generado: {resultado['ruta_log']}", "info")
            
            # Actualizar footer
            if self.main_window:
                self.main_window.update_footer(
                    f"Contratos: {resultado['secciones_detectadas']} secciones detectadas en {resultado['duracion']}"
                )
        else:
            self.log_viewer.add_log("", "info")
            self.log_viewer.add_log(f"❌ ERROR: {resultado.get('mensaje', 'Error desconocido')}", "error")
        
        # Limpiar thread
        self.diagnostic_thread = None