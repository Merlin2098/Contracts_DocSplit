"""
Utilidades para manejo de archivos y carpetas.
Módulo compartido entre workflows de Renovaciones y Contratos.
"""

import os
import re


def extraer_nombre_trabajador(nombre_archivo):
    """
    Extrae el texto entre los guiones "-" del nombre del archivo.
    Usado principalmente en workflow de Renovaciones.
    
    Args:
        nombre_archivo (str): Nombre del archivo PDF
        
    Returns:
        str: Nombre del trabajador formateado con underscores
        
    Example:
        >>> extraer_nombre_trabajador("Renovacion de Contrato - Anthony Arenas (2).pdf")
        'Anthony_Arenas'
    """
    partes = re.findall(r"-\s*(.*?)\s*(?:\(|-|\Z)", nombre_archivo)
    if partes:
        nombre = partes[0]
        nombre = re.sub(r'[^A-Za-zÁÉÍÓÚÜÑáéíóúüñ\s]', '', nombre)
        nombre = "_".join(nombre.strip().split())
        return nombre
    else:
        return "Desconocido"


def crear_carpeta_salida(base_dir, trabajador):
    """
    Crea la estructura de carpetas de salida para Renovaciones.
    Estructura: /salida/{trabajador}
    
    Args:
        base_dir (str): Directorio base donde crear la carpeta salida
        trabajador (str): Nombre del trabajador para crear subcarpeta
        
    Returns:
        str: Ruta completa de la carpeta del trabajador
        
    Example:
        >>> crear_carpeta_salida("/data/pdfs", "Juan_Perez")
        '/data/pdfs/salida/Juan_Perez'
    """
    salida_base = os.path.join(base_dir, "salida")
    os.makedirs(salida_base, exist_ok=True)

    carpeta_trabajador = os.path.join(salida_base, trabajador)
    os.makedirs(carpeta_trabajador, exist_ok=True)

    return carpeta_trabajador


def obtener_carpeta_destino(carpeta_general, nombre_archivo):
    """
    Crea carpeta específica para un PDF dentro de la carpeta general de salida.
    Usado en workflow de Contratos.
    Estructura: {carpeta_general}/{nombre_base_archivo}/
    
    Args:
        carpeta_general (str): Carpeta base de salida
        nombre_archivo (str): Nombre del archivo PDF (con extensión)
        
    Returns:
        str: Ruta completa de la carpeta individual
        
    Example:
        >>> obtener_carpeta_destino("/data/pdfs_extraidos", "PEREZ_JUAN.pdf")
        '/data/pdfs_extraidos/PEREZ_JUAN'
    """
    nombre_base = os.path.splitext(nombre_archivo)[0]
    carpeta_individual = os.path.join(carpeta_general, nombre_base)
    os.makedirs(carpeta_individual, exist_ok=True)
    return carpeta_individual


def limpiar_nombres_archivos(carpeta_base):
    """
    Recorre todas las carpetas dentro de 'salida' y reemplaza
    los '_' por espacios simples en nombres de archivos y carpetas.
    Usado en workflow de Renovaciones como paso final.
    
    Args:
        carpeta_base (str): Directorio base que contiene la carpeta 'salida'
        
    Example:
        >>> limpiar_nombres_archivos("/data/pdfs")
        # Renombra: "Juan_Perez.pdf" → "Juan Perez.pdf"
        # Renombra: "Anthony_Arenas/" → "Anthony Arenas/"
    """
    salida_path = os.path.join(carpeta_base, "salida")
    
    if not os.path.exists(salida_path):
        return
    
    for root, dirs, files in os.walk(salida_path, topdown=False):
        # Renombrar archivos
        for file in files:
            nuevo_nombre = file.replace("_", " ")
            if nuevo_nombre != file:
                ruta_original = os.path.join(root, file)
                ruta_nueva = os.path.join(root, nuevo_nombre)
                if not os.path.exists(ruta_nueva):
                    os.rename(ruta_original, ruta_nueva)
        
        # Renombrar carpetas
        for dir_name in dirs:
            nuevo_nombre = dir_name.replace("_", " ")
            if nuevo_nombre != dir_name:
                ruta_original = os.path.join(root, dir_name)
                ruta_nueva = os.path.join(root, nuevo_nombre)
                if not os.path.exists(ruta_nueva):
                    os.rename(ruta_original, ruta_nueva)


def validar_carpeta_entrada(ruta_carpeta):
    """
    Valida que la ruta sea una carpeta válida y contenga archivos PDF.
    
    Args:
        ruta_carpeta (str): Ruta a validar
        
    Returns:
        tuple: (es_valida: bool, mensaje: str, archivos_pdf: list)
        
    Example:
        >>> validar_carpeta_entrada("/data/pdfs")
        (True, "Carpeta válida", ["archivo1.pdf", "archivo2.pdf"])
    """
    if not os.path.isdir(ruta_carpeta):
        return False, "La ruta ingresada no es válida o no existe.", []
    
    archivos_pdf = [f for f in os.listdir(ruta_carpeta) if f.lower().endswith(".pdf")]
    
    if not archivos_pdf:
        return False, "La carpeta no contiene archivos PDF.", []
    
    return True, f"Se encontraron {len(archivos_pdf)} archivos PDF.", archivos_pdf


def obtener_nombre_sin_extension(nombre_archivo):
    """
    Obtiene el nombre del archivo sin la extensión.
    
    Args:
        nombre_archivo (str): Nombre del archivo con extensión
        
    Returns:
        str: Nombre sin extensión
        
    Example:
        >>> obtener_nombre_sin_extension("documento.pdf")
        'documento'
    """
    return os.path.splitext(nombre_archivo)[0]