"""
Módulo para dividir PDFs de renovaciones en secciones individuales.
Ubicación: core/renovaciones/divider.py

Contiene la lógica de negocio para extraer secciones de PDFs basándose
en los rangos de páginas detectados.
"""

import os
import fitz
from typing import Dict, Tuple, List


def extraer_seccion_pdf(ruta_pdf: str, paginas: Dict, ruta_salida: str) -> None:
    """
    Extrae un rango de páginas de un PDF usando PyMuPDF.
    
    Args:
        ruta_pdf: Ruta del PDF original
        paginas: Dict con {"inicio": 1, "fin": 6} (base-1, desde JSON)
        ruta_salida: Ruta donde guardar el PDF extraído
        
    Raises:
        FileNotFoundError: Si el PDF de origen no existe
        ValueError: Si los rangos de páginas son inválidos
    """
    if not os.path.exists(ruta_pdf):
        raise FileNotFoundError(f"PDF no encontrado: {ruta_pdf}")
    
    if not paginas or "inicio" not in paginas or "fin" not in paginas:
        raise ValueError("El diccionario de páginas debe contener 'inicio' y 'fin'")
    
    with fitz.open(ruta_pdf) as pdf:
        nuevo_pdf = fitz.open()
        total_paginas = len(pdf)
        
        # Convertir de base-1 (JSON) a base-0 (PyMuPDF)
        inicio = max(paginas["inicio"] - 1, 0)
        fin = min(paginas["fin"], total_paginas)
        
        # Validar rango
        if inicio >= total_paginas:
            raise ValueError(f"Página de inicio {paginas['inicio']} excede total de páginas {total_paginas}")
        
        if inicio >= fin:
            raise ValueError(f"Rango inválido: inicio={paginas['inicio']}, fin={paginas['fin']}")
        
        # Copiar páginas
        for i in range(inicio, fin):
            nuevo_pdf.insert_pdf(pdf, from_page=i, to_page=i)
        
        # Guardar PDF extraído
        nuevo_pdf.save(ruta_salida)
        nuevo_pdf.close()


def procesar_pdf_renovacion(
    ruta_pdf: str,
    info_secciones: Dict,
    carpeta_destino: str,
    nombre_trabajador: str
) -> Tuple[int, int, List[Tuple[str, str, str]]]:
    """
    Procesa un PDF de renovación extrayendo todas sus secciones.
    
    Args:
        ruta_pdf: Ruta del PDF original
        info_secciones: Dict con información del JSON (total_paginas, fecha_contrato, secciones)
        carpeta_destino: Carpeta donde guardar las secciones extraídas
        nombre_trabajador: Nombre del trabajador para nombrar archivos
        
    Returns:
        Tuple con:
        - exitosos: Número de secciones extraídas correctamente
        - errores: Número de secciones con error
        - detalles: Lista de tuplas (nombre_seccion, estado, mensaje)
    """
    exitosos = 0
    errores = 0
    detalles = []
    
    fecha_contrato = info_secciones.get('fecha_contrato', 'sin_fecha')
    secciones = info_secciones.get('secciones', {})
    
    # Crear carpeta de destino si no existe
    os.makedirs(carpeta_destino, exist_ok=True)
    
    # Procesar cada sección
    for nombre_seccion, rango in secciones.items():
        # Verificar si la sección fue detectada
        if not rango or rango is None:
            detalles.append((
                nombre_seccion,
                'omitido',
                'No detectada en el documento'
            ))
            continue
        
        try:
            # Formato: {seccion}-{fecha}-{nombre_trabajador}.pdf
            nombre_salida = f"{nombre_seccion}-{fecha_contrato}-{nombre_trabajador}.pdf"
            ruta_salida = os.path.join(carpeta_destino, nombre_salida)
            
            # Extraer sección
            extraer_seccion_pdf(ruta_pdf, rango, ruta_salida)
            
            exitosos += 1
            detalles.append((
                nombre_seccion,
                'exito',
                f"páginas {rango['inicio']}-{rango['fin']} → {nombre_salida}"
            ))
            
        except Exception as e:
            errores += 1
            detalles.append((
                nombre_seccion,
                'error',
                str(e)
            ))
    
    return exitosos, errores, detalles


def validar_json_renovaciones(datos_json: Dict) -> Tuple[bool, str]:
    """
    Valida que el JSON de diagnóstico tenga la estructura esperada.
    
    Args:
        datos_json: Diccionario cargado del JSON
        
    Returns:
        Tuple con (es_valido, mensaje_error)
    """
    if not isinstance(datos_json, dict):
        return False, "El JSON debe ser un diccionario"
    
    if len(datos_json) == 0:
        return False, "El JSON está vacío"
    
    # Validar estructura de cada archivo
    for nombre_archivo, info in datos_json.items():
        if not isinstance(info, dict):
            return False, f"Información inválida para {nombre_archivo}"
        
        campos_requeridos = ['total_paginas', 'fecha_contrato', 'secciones']
        for campo in campos_requeridos:
            if campo not in info:
                return False, f"Falta campo '{campo}' en {nombre_archivo}"
        
        # Validar que secciones sea un diccionario
        if not isinstance(info['secciones'], dict):
            return False, f"Campo 'secciones' inválido en {nombre_archivo}"
    
    return True, ""


def calcular_total_secciones_renovaciones(datos_json: Dict) -> int:
    """
    Calcula el total de secciones a procesar (solo las detectadas).
    
    Args:
        datos_json: Diccionario cargado del JSON
        
    Returns:
        Total de secciones detectadas (no None)
    """
    total = 0
    
    for nombre_archivo, info in datos_json.items():
        secciones = info.get('secciones', {})
        for nombre_seccion, rango in secciones.items():
            if rango is not None:
                total += 1
    
    return total