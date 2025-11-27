"""
Módulo de normalización de nombres para contratos.
Ubicación: core/contratos/normalizer.py

Funciones principales:
- normalizar_nombre_pdf(): Extrae nombre entre guiones
- generar_nombre_unico(): Previene conflictos de nombres
- validar_archivos_pdf(): Valida lista de PDFs
"""

import os
import re


def normalizar_nombre_pdf(nombre_archivo):
    """
    Normaliza el nombre de un archivo PDF extrayendo el contenido entre guiones.
    
    Reglas:
    - Con 2+ guiones: Extrae la segunda parte (índice 1)
      Ejemplo: "2024-12-15-Juan_Perez.pdf" → "Juan_Perez.pdf"
    
    - Con 1 guion: Extrae la segunda parte (índice 1)
      Ejemplo: "Contrato-Maria_Lopez.pdf" → "Maria_Lopez.pdf"
    
    - Sin guiones: Mantiene el nombre original
      Ejemplo: "Pedro_Garcia.pdf" → "Pedro_Garcia.pdf"
    
    Args:
        nombre_archivo (str): Nombre del archivo PDF
    
    Returns:
        tuple: (nombre_normalizado, fue_modificado)
               - nombre_normalizado (str): Nuevo nombre del archivo
               - fue_modificado (bool): True si se modificó, False si no
    """
    if not nombre_archivo.lower().endswith('.pdf'):
        return nombre_archivo, False
    
    nombre_sin_ext = os.path.splitext(nombre_archivo)[0]
    extension = ".pdf"
    
    partes = [p.strip() for p in nombre_sin_ext.split('-') if p.strip()]
    
    if len(partes) >= 2:
        nombre_normalizado = partes[1] + extension
        return nombre_normalizado, True
    
    return nombre_archivo, False


def generar_nombre_unico(carpeta, nombre_base, extension):
    """
    Genera un nombre único para evitar sobrescribir archivos existentes.
    Agrega sufijos numéricos (1), (2), (3)... si el archivo ya existe.
    
    Args:
        carpeta (str): Ruta de la carpeta donde verificar
        nombre_base (str): Nombre base sin extensión
        extension (str): Extensión del archivo (ejemplo: ".pdf")
    
    Returns:
        str: Nombre de archivo único
    """
    nombre_propuesto = nombre_base + extension
    ruta_completa = os.path.join(carpeta, nombre_propuesto)
    
    if not os.path.exists(ruta_completa):
        return nombre_propuesto
    
    contador = 1
    while True:
        nombre_propuesto = f"{nombre_base} ({contador}){extension}"
        ruta_completa = os.path.join(carpeta, nombre_propuesto)
        
        if not os.path.exists(ruta_completa):
            return nombre_propuesto
        
        contador += 1


def validar_archivos_pdf(lista_archivos):
    """
    Valida que una lista de archivos sean PDFs válidos.
    
    Args:
        lista_archivos (list): Lista de nombres de archivos
    
    Returns:
        tuple: (archivos_validos, archivos_invalidos)
    """
    archivos_validos = []
    archivos_invalidos = []
    
    for archivo in lista_archivos:
        if archivo.lower().endswith('.pdf'):
            archivos_validos.append(archivo)
        else:
            archivos_invalidos.append(archivo)
    
    return archivos_validos, archivos_invalidos


def extraer_nombre_trabajador(nombre_archivo):
    """
    Extrae el nombre del trabajador desde un nombre de archivo normalizado.
    
    Args:
        nombre_archivo (str): Nombre del archivo (puede incluir extensión)
    
    Returns:
        str: Nombre del trabajador sin extensión
    """
    nombre_sin_ext = os.path.splitext(nombre_archivo)[0]
    return nombre_sin_ext


def validar_nombre_normalizado(nombre_archivo):
    """
    Valida que un nombre de archivo esté correctamente normalizado.
    Un nombre normalizado NO debe contener guiones.
    
    Args:
        nombre_archivo (str): Nombre del archivo a validar
    
    Returns:
        bool: True si está normalizado (sin guiones), False si contiene guiones
    """
    nombre_sin_ext = os.path.splitext(nombre_archivo)[0]
    return '-' not in nombre_sin_ext


def contar_archivos_por_normalizar(carpeta):
    """
    Cuenta cuántos archivos en una carpeta requieren normalización.
    
    Args:
        carpeta (str): Ruta de la carpeta a analizar
    
    Returns:
        dict: {
            'total': int,
            'requieren_normalizacion': int,
            'ya_normalizados': int
        }
    """
    if not os.path.isdir(carpeta):
        return {'total': 0, 'requieren_normalizacion': 0, 'ya_normalizados': 0}
    
    archivos_pdf = [f for f in os.listdir(carpeta) if f.lower().endswith('.pdf')]
    total = len(archivos_pdf)
    
    requieren_normalizacion = 0
    ya_normalizados = 0
    
    for archivo in archivos_pdf:
        nombre_normalizado, fue_modificado = normalizar_nombre_pdf(archivo)
        if fue_modificado:
            requieren_normalizacion += 1
        else:
            ya_normalizados += 1
    
    return {
        'total': total,
        'requieren_normalizacion': requieren_normalizacion,
        'ya_normalizados': ya_normalizados
    }