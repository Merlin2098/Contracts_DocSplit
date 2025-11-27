"""
Widgets reutilizables para PDF Processor.

Este paquete contiene componentes de interfaz compartidos entre tabs.
"""

from .file_selector import FileSelector
from .log_viewer import LogViewer
from .progress_dialog import ProgressDialog

__all__ = ['FileSelector', 'LogViewer', 'ProgressDialog']