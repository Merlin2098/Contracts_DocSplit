"""
Procesador de secciones de PDFs para contratos.
Ubicación: core/contratos/processor.py

Extrae secciones individuales de PDFs basándose en rangos detectados.
"""

import os
import fitz  # PyMuPDF
import re


def extraer_seccion(ruta_pdf_origen, inicio, fin, ruta_salida):
    """
    Extrae un rango de páginas de un PDF usando PyMuPDF.
    
    Args:
        ruta_pdf_origen (str): Ruta del PDF fuente
        inicio (int): Página de inicio (1-indexed)
        fin (int): Página de fin (1-indexed, inclusive)
        ruta_salida (str): Ruta donde guardar el PDF extraído
    
    Raises:
        Exception: Si hay error en la extracción
    """
    try:
        with fitz.open(ruta_pdf_origen) as pdf:
            nuevo_pdf = fitz.open()
            total_paginas = len(pdf)
            
            # Convertir a 0-indexed y validar rangos
            inicio_idx = max(inicio - 1, 0)
            fin_idx = min(fin, total_paginas)
            
            # Extraer páginas
            for i in range(inicio_idx, fin_idx):
                nuevo_pdf.insert_pdf(pdf, from_page=i, to_page=i)
            
            # Guardar y cerrar
            nuevo_pdf.save(ruta_salida)
            nuevo_pdf.close()
    
    except Exception as e:
        raise Exception(f"Error al extraer sección: {str(e)}")


def sanitizar_nombre_archivo(nombre):
    """
    Limpia un nombre de archivo removiendo caracteres no válidos en Windows.
    
    Args:
        nombre (str): Nombre a sanitizar
    
    Returns:
        str: Nombre sanitizado
    """
    # Caracteres no válidos en Windows
    caracteres_invalidos = r'[<>:"/\\|?*]'
    nombre_limpio = re.sub(caracteres_invalidos, '', nombre)
    
    # Truncar si es muy largo (max 200 caracteres)
    if len(nombre_limpio) > 200:
        nombre_limpio = nombre_limpio[:200]
    
    return nombre_limpio.strip()


def generar_nombre_seccion(nombre_seccion, fecha_contrato, nombre_trabajador):
    """
    Genera el nombre de archivo para una sección extraída.
    
    Formato: {nombre_seccion}-{fecha_contrato}-{nombre_trabajador}.pdf
    
    Args:
        nombre_seccion (str): Nombre de la sección
        fecha_contrato (str): Fecha del contrato (ej: "11.2025")
        nombre_trabajador (str): Nombre del trabajador (sin extensión .pdf)
    
    Returns:
        str: Nombre de archivo sanitizado
    """
    nombre_base = f"{nombre_seccion}-{fecha_contrato}-{nombre_trabajador}.pdf"
    return sanitizar_nombre_archivo(nombre_base)


def obtener_carpeta_trabajador_unica(carpeta_base, nombre_trabajador):
    """
    Crea carpeta para un trabajador, manejando duplicados con sufijos.
    
    Si la carpeta existe, agrega sufijo (2), (3), etc.
    
    Args:
        carpeta_base (str): Carpeta padre donde crear la subcarpeta
        nombre_trabajador (str): Nombre del trabajador
    
    Returns:
        str: Ruta completa de la carpeta creada
    """
    nombre_sanitizado = sanitizar_nombre_archivo(nombre_trabajador)
    carpeta_destino = os.path.join(carpeta_base, nombre_sanitizado)
    
    # Si no existe, crear y retornar
    if not os.path.exists(carpeta_destino):
        os.makedirs(carpeta_destino)
        return carpeta_destino
    
    # Buscar primer sufijo disponible
    contador = 2
    while True:
        carpeta_con_sufijo = os.path.join(carpeta_base, f"{nombre_sanitizado} ({contador})")
        if not os.path.exists(carpeta_con_sufijo):
            os.makedirs(carpeta_con_sufijo)
            return carpeta_con_sufijo
        contador += 1


def procesar_pdf_individual(ruta_pdf, nombre_archivo, info_secciones, carpeta_destino_trabajador):
    """
    Procesa todas las secciones de un PDF individual.
    
    Args:
        ruta_pdf (str): Ruta completa al PDF fuente
        nombre_archivo (str): Nombre del archivo PDF (con extensión)
        info_secciones (dict): Información del JSON (secciones y fecha_contrato)
        carpeta_destino_trabajador (str): Carpeta donde guardar las secciones
    
    Returns:
        tuple: (exitos, errores, detalles)
            - exitos (int): Número de secciones extraídas exitosamente
            - errores (int): Número de errores
            - detalles (list): Lista de tuplas (nombre_seccion, estado, mensaje)
    """
    exitos = 0
    errores = 0
    detalles = []
    
    fecha_contrato = info_secciones.get('fecha_contrato')
    secciones = info_secciones.get('secciones', {})
    
    # Obtener nombre del trabajador (sin extensión .pdf)
    nombre_trabajador = os.path.splitext(nombre_archivo)[0]
    
    # Procesar cada sección
    for nombre_seccion, rango in secciones.items():
        # Skip secciones no detectadas (null)
        if rango is None:
            detalles.append((nombre_seccion, 'omitido', 'No detectado'))
            continue
        
        try:
            # Generar nombre de archivo de salida
            nombre_salida = generar_nombre_seccion(
                nombre_seccion, 
                fecha_contrato, 
                nombre_trabajador
            )
            ruta_salida = os.path.join(carpeta_destino_trabajador, nombre_salida)
            
            # Extraer sección
            extraer_seccion(
                ruta_pdf, 
                rango['inicio'], 
                rango['fin'], 
                ruta_salida
            )
            
            exitos += 1
            detalles.append((nombre_seccion, 'exito', nombre_salida))
        
        except Exception as e:
            errores += 1
            detalles.append((nombre_seccion, 'error', str(e)))
    
    return exitos, errores, detalles


def validar_json_diagnostico(datos_json):
    """
    Valida la estructura del JSON de diagnóstico.
    
    Args:
        datos_json (dict): Diccionario cargado del JSON
    
    Returns:
        tuple: (es_valido, mensaje_error)
    """
    if not isinstance(datos_json, dict):
        return False, "JSON no es un diccionario válido"
    
    if len(datos_json) == 0:
        return False, "JSON está vacío"
    
    # Validar estructura de al menos un archivo
    for nombre_archivo, info in datos_json.items():
        if not isinstance(info, dict):
            return False, f"Información de {nombre_archivo} no es un diccionario"
        
        if 'secciones' not in info:
            return False, f"Falta clave 'secciones' en {nombre_archivo}"
        
        if 'fecha_contrato' not in info:
            return False, f"Falta clave 'fecha_contrato' en {nombre_archivo}"
        
        # Validar al menos una sección
        break
    
    return True, ""


def calcular_total_secciones(datos_json):
    """
    Calcula el total de secciones válidas (no null) a extraer.
    
    Args:
        datos_json (dict): Diccionario del JSON de diagnóstico
    
    Returns:
        int: Total de secciones a procesar
    """
    total = 0
    
    for info in datos_json.values():
        secciones = info.get('secciones', {})
        # Contar solo secciones con rango válido (no null)
        total += sum(1 for rango in secciones.values() if rango is not None)
    
    return total