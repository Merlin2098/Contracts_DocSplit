"""
Sistema de logging para ambos workflows.
Módulo compartido entre Renovaciones y Contratos.
"""

import os
from datetime import datetime
from pathlib import Path


def obtener_directorio_logs(workflow, crear=True):
    """
    Obtiene el directorio de logs para un workflow específico.
    Organizado por año-mes para mejor gestión.
    Estructura: logs/{workflow}/{YYYY-MM}/
    
    Args:
        workflow (str): "renovaciones" o "contratos"
        crear (bool): Si True, crea el directorio si no existe
        
    Returns:
        str: Ruta al directorio de logs
        
    Example:
        >>> obtener_directorio_logs("renovaciones")
        'C:/proyecto/logs/renovaciones/2025-11/'
    """
    # Directorio base del proyecto (3 niveles arriba desde logger.py)
    # logger.py está en: proyecto/core/utils/logger.py
    # Necesitamos llegar a: proyecto/
    base_dir = Path(__file__).parent.parent.parent
    
    # Subdirectorio por fecha (año-mes)
    fecha_dir = datetime.now().strftime("%Y-%m")
    
    # Ruta completa: proyecto/logs/{workflow}/{YYYY-MM}/
    logs_dir = base_dir / "logs" / workflow / fecha_dir
    
    if crear:
        logs_dir.mkdir(parents=True, exist_ok=True)
    
    return str(logs_dir)


def generar_nombre_log_con_timestamp(prefijo, carpeta_salida):
    """
    Genera un nombre de archivo de log con timestamp.
    Formato: prefijo_DD.MM.YYYY_HH.MM.SS.log
    
    Args:
        prefijo (str): Prefijo del archivo (ej: "interfaz", "proceso")
        carpeta_salida (str): Carpeta donde se guardará el log
        
    Returns:
        str: Ruta completa del archivo de log
        
    Example:
        >>> generar_nombre_log_con_timestamp("interfaz", "/data/salida")
        '/data/salida/interfaz_11.11.2025_20.30.45.log'
    """
    timestamp = datetime.now().strftime("%d.%m.%Y_%H.%M.%S")
    nombre_log = f"{prefijo}_{timestamp}.log"
    return os.path.join(carpeta_salida, nombre_log)


def format_duration(seconds):
    """
    Formatea una duración en segundos a formato legible.
    
    Args:
        seconds (float): Duración en segundos
        
    Returns:
        str: Duración formateada
        
    Examples:
        >>> format_duration(45)
        '45s'
        >>> format_duration(125)
        '2m 5s'
        >>> format_duration(3725)
        '1h 2m 5s'
    """
    seconds = int(seconds)
    
    if seconds < 60:
        return f"{seconds}s"
    elif seconds < 3600:
        minutos = seconds // 60
        segs = seconds % 60
        if segs > 0:
            return f"{minutos}m {segs}s"
        return f"{minutos}m"
    else:
        horas = seconds // 3600
        minutos = (seconds % 3600) // 60
        segs = seconds % 60
        
        partes = [f"{horas}h"]
        if minutos > 0:
            partes.append(f"{minutos}m")
        if segs > 0:
            partes.append(f"{segs}s")
        
        return " ".join(partes)


def escribir_log(ruta_log, mensaje):
    """
    Escribe una línea de texto en el archivo de log.
    
    Args:
        ruta_log (str): Ruta completa del archivo de log
        mensaje (str): Mensaje a escribir
        
    Example:
        >>> escribir_log("/data/log.txt", "Archivo procesado correctamente")
    """
    try:
        with open(ruta_log, "a", encoding="utf-8") as log:
            log.write(mensaje + "\n")
    except Exception as e:
        print(f"⚠️ Error al escribir en log: {str(e)}")


def crear_log_header(ruta_log, titulo):
    """
    Crea el encabezado inicial del archivo de log.
    Si el archivo ya existe, lo sobrescribe.
    
    Args:
        ruta_log (str): Ruta completa del archivo de log
        titulo (str): Título del proceso
        
    Example:
        >>> crear_log_header("/data/log.txt", "DIAGNÓSTICO DE CONTRATOS")
    """
    try:
        with open(ruta_log, "w", encoding="utf-8") as log:
            log.write("=" * 90 + "\n")
            log.write(f"{titulo}\n")
            log.write(f"Fecha de ejecución: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            log.write("=" * 90 + "\n\n")
    except Exception as e:
        print(f"⚠️ Error al crear header del log: {str(e)}")


def crear_log_footer(ruta_log, exitosos, fallidos):
    """
    Crea el pie del archivo de log con estadísticas finales.
    
    Args:
        ruta_log (str): Ruta completa del archivo de log
        exitosos (int): Cantidad de archivos procesados exitosamente
        fallidos (int): Cantidad de archivos con errores
        
    Example:
        >>> crear_log_footer("/data/log.txt", 10, 2)
    """
    try:
        with open(ruta_log, "a", encoding="utf-8") as log:
            log.write("\n" + "=" * 90 + "\n")
            log.write(f"RESUMEN FINAL\n")
            log.write(f"Fecha de finalización: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            log.write(f"Archivos procesados exitosamente: {exitosos}\n")
            log.write(f"Archivos con errores: {fallidos}\n")
            log.write(f"Total: {exitosos + fallidos}\n")
            log.write("=" * 90 + "\n")
    except Exception as e:
        print(f"⚠️ Error al crear footer del log: {str(e)}")


def log_separador(ruta_log):
    """
    Escribe una línea separadora en el log.
    
    Args:
        ruta_log (str): Ruta completa del archivo de log
    """
    escribir_log(ruta_log, "-" * 90)


def log_seccion(ruta_log, titulo):
    """
    Escribe un título de sección en el log.
    
    Args:
        ruta_log (str): Ruta completa del archivo de log
        titulo (str): Título de la sección
        
    Example:
        >>> log_seccion("/data/log.txt", "PROCESANDO ARCHIVO: contrato.pdf")
    """
    escribir_log(ruta_log, "")
    escribir_log(ruta_log, "=" * 90)
    escribir_log(ruta_log, titulo)
    escribir_log(ruta_log, "=" * 90)


def inicializar_log(ruta_log):
    """
    Elimina el archivo de log si existe, preparándolo para nueva ejecución.
    
    Args:
        ruta_log (str): Ruta completa del archivo de log
    """
    if os.path.exists(ruta_log):
        try:
            os.remove(ruta_log)
        except Exception as e:
            print(f"⚠️ Error al eliminar log anterior: {str(e)}")