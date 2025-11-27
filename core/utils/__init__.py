"""
Paquete de utilidades compartidas.
"""

from .file_utils import (
    extraer_nombre_trabajador,
    crear_carpeta_salida,
    obtener_carpeta_destino,
    limpiar_nombres_archivos,
    validar_carpeta_entrada,
    obtener_nombre_sin_extension
)

from .logger import (
    escribir_log,
    crear_log_header,
    crear_log_footer,
    log_separador,
    log_seccion,
    inicializar_log,
    generar_nombre_log_con_timestamp,
    format_duration,
    obtener_directorio_logs
)

__all__ = [
    'extraer_nombre_trabajador',
    'crear_carpeta_salida',
    'obtener_carpeta_destino',
    'limpiar_nombres_archivos',
    'validar_carpeta_entrada',
    'obtener_nombre_sin_extension',
    'escribir_log',
    'crear_log_header',
    'crear_log_footer',
    'log_separador',
    'log_seccion',
    'inicializar_log',
    'generar_nombre_log_con_timestamp',
    'format_duration',
    'obtener_directorio_logs'
]