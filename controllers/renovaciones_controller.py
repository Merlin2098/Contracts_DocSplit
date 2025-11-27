"""
Controller para el workflow de Renovaciones (actualizado).
Implementa workflow en 2 pasos:
  1. DIAGNÓSTICO: Detecta secciones y genera diagnostico_rangos.json
  2. PROCESAMIENTO: Lee JSON y extrae PDFs individuales

Sistema de logs dual:
  - interfaz.log: Resumen para GUI
  - proceso.log: Detalles técnicos completos
"""

import os
import time
import json
import fitz
from pathlib import Path
from typing import Callable, Optional
from core.renovaciones.section_detector import SectionDetector
from core.renovaciones.json_generator import JSONGenerator
from core.utils.file_utils import (
    validar_carpeta_entrada,
    limpiar_nombres_archivos
)
from core.utils.logger import (
    escribir_log,
    crear_log_header,
    log_seccion,
    generar_nombre_log_con_timestamp,
    format_duration,
    obtener_directorio_logs
)


def procesar_renovaciones(
    carpeta_entrada: str,
    progress_callback: Optional[Callable] = None,
    log_gui_callback: Optional[Callable] = None
) -> dict:
    """
    Procesa PDFs de renovaciones usando diagnostico_rangos.json.
    Lee el JSON consolidado y extrae las secciones de cada PDF.
    
    Args:
        carpeta_entrada: Ruta de la carpeta con PDFs y diagnostico_rangos.json
        progress_callback: callback(current, total, message, percentage)
        log_gui_callback: callback(mensaje, tipo)
    
    Returns:
        dict: Resultado del procesamiento con estructura:
        {
            'exitoso': bool,
            'mensaje': str,
            'archivos_procesados': int,
            'archivos_con_error': int,
            'total': int,
            'secciones_extraidas': int,
            'duracion': str,
            'ruta_log_interfaz': str,
            'ruta_log_proceso': str,
            'carpeta_salida': str
        }
    """
    tiempo_inicio = time.time()
    
    # --- 1. Validar que existe diagnostico_rangos.json ---
    ruta_json = os.path.join(carpeta_entrada, "diagnostico_rangos.json")
    
    if not os.path.isfile(ruta_json):
        return {
            'exitoso': False,
            'mensaje': 'No se encontró diagnostico_rangos.json en la carpeta. Ejecuta primero el diagnóstico.',
            'archivos_procesados': 0,
            'archivos_con_error': 0,
            'total': 0,
            'secciones_extraidas': 0,
            'duracion': '0s',
            'ruta_log_interfaz': None,
            'ruta_log_proceso': None,
            'carpeta_salida': None
        }
    
    # --- 2. Cargar JSON ---
    try:
        with open(ruta_json, 'r', encoding='utf-8') as f:
            datos_rangos = json.load(f)
    except Exception as e:
        return {
            'exitoso': False,
            'mensaje': f'Error al cargar JSON: {str(e)}',
            'archivos_procesados': 0,
            'archivos_con_error': 0,
            'total': 0,
            'secciones_extraidas': 0,
            'duracion': '0s',
            'ruta_log_interfaz': None,
            'ruta_log_proceso': None,
            'carpeta_salida': None
        }
    
    # --- 3. Inicializar variables ---
    archivos_en_json = list(datos_rangos.keys())
    total_archivos = len(archivos_en_json)
    exitosos = 0
    fallidos = 0
    total_secciones_extraidas = 0
    
    carpeta_salida = os.path.join(carpeta_entrada, "pdfs_extraidos")
    os.makedirs(carpeta_salida, exist_ok=True)
    
    # Generar logs con timestamp
    logs_dir = obtener_directorio_logs("renovaciones")
    ruta_log_interfaz = generar_nombre_log_con_timestamp("interfaz", logs_dir)
    ruta_log_proceso = generar_nombre_log_con_timestamp("proceso", logs_dir)
    
    # --- 4. Inicializar logs ---
    crear_log_header(ruta_log_interfaz, "PROCESAMIENTO DE RENOVACIONES - INTERFAZ")
    escribir_log(ruta_log_interfaz, f"Carpeta seleccionada: {carpeta_entrada}")
    escribir_log(ruta_log_interfaz, f"Total de archivos en JSON: {total_archivos}\n")
    
    crear_log_header(ruta_log_proceso, "PROCESAMIENTO DE RENOVACIONES - TÉCNICO")
    escribir_log(ruta_log_proceso, f"Carpeta: {carpeta_entrada}")
    escribir_log(ruta_log_proceso, f"JSON: {ruta_json}")
    escribir_log(ruta_log_proceso, f"Total archivos: {total_archivos}\n")
    
    if log_gui_callback:
        log_gui_callback(f"📂 Carpeta seleccionada: {carpeta_entrada}", "info")
        log_gui_callback(f"📄 JSON cargado: diagnostico_rangos.json", "info")
        log_gui_callback(f"📊 Total de archivos: {total_archivos}", "info")
        log_gui_callback("", "info")
    
    # --- 5. Procesar cada PDF del JSON ---
    for idx, archivo in enumerate(archivos_en_json, 1):
        try:
            # Actualizar progreso
            if progress_callback:
                progress = int((idx / total_archivos) * 100)
                progress_callback(idx, total_archivos, f"Procesando: {archivo}", progress)
            
            ruta_pdf = os.path.join(carpeta_entrada, archivo)
            
            # Verificar que el PDF existe
            if not os.path.isfile(ruta_pdf):
                escribir_log(ruta_log_proceso, f"⚠️ PDF no encontrado: {archivo}")
                escribir_log(ruta_log_interfaz, f"❌ Archivo {idx}: PDF no encontrado")
                if log_gui_callback:
                    log_gui_callback(f"❌ Archivo {idx}: PDF no encontrado - {archivo}", "error")
                fallidos += 1
                continue
            
            # Log de interfaz
            escribir_log(ruta_log_interfaz, f"⏳ Procesando archivo {idx}/{total_archivos}: {archivo}")
            if log_gui_callback:
                log_gui_callback(f"⏳ Procesando archivo {idx}/{total_archivos}: {archivo}", "info")
            
            # Log técnico
            log_seccion(ruta_log_proceso, f"ARCHIVO {idx}/{total_archivos}: {archivo}")
            
            # Obtener info del JSON
            info = datos_rangos[archivo]
            fecha_contrato = info.get("fecha_contrato", "sin_fecha")
            secciones = info.get("secciones", {})
            
            escribir_log(ruta_log_proceso, f"Fecha contrato: {fecha_contrato}")
            escribir_log(ruta_log_proceso, f"Secciones detectadas: {len(secciones)}")
            
            # Crear carpeta individual para este PDF
            nombre_base = os.path.splitext(archivo)[0]
            carpeta_pdf = os.path.join(carpeta_salida, nombre_base)
            os.makedirs(carpeta_pdf, exist_ok=True)
            
            escribir_log(ruta_log_proceso, f"Carpeta destino: {carpeta_pdf}")
            
            # Extraer nombre del trabajador para nombres cortos
            # Buscar patrón: " - NOMBRE - " o similar
            partes = nombre_base.split(' - ')
            if len(partes) >= 2:
                nombre_trabajador = partes[1].strip()
            else:
                nombre_trabajador = nombre_base[:50]  # Truncar si no hay patrón
            
            # Extraer cada sección
            secciones_extraidas = 0
            
            for nombre_seccion, rango in secciones.items():
                if not rango:
                    escribir_log(ruta_log_proceso, f"  ⚠️ {nombre_seccion}: No detectada (null)")
                    continue
                
                try:
                    # Formato: {seccion}-{fecha}-{nombre_trabajador}.pdf
                    nombre_salida = f"{nombre_seccion}-{fecha_contrato}-{nombre_trabajador}.pdf"
                    ruta_salida = os.path.join(carpeta_pdf, nombre_salida)
                    
                    # Extraer páginas
                    extraer_paginas_pdf(ruta_pdf, rango, ruta_salida)
                    
                    escribir_log(
                        ruta_log_proceso,
                        f"  ✅ {nombre_seccion}: páginas {rango['inicio']}-{rango['fin']} → {nombre_salida}"
                    )
                    
                    secciones_extraidas += 1
                    total_secciones_extraidas += 1
                    
                except Exception as e:
                    escribir_log(
                        ruta_log_proceso,
                        f"  ❌ Error extrayendo {nombre_seccion}: {str(e)}"
                    )
            
            escribir_log(ruta_log_proceso, f"Total extraído: {secciones_extraidas} secciones")
            escribir_log(ruta_log_proceso, "✅ Procesamiento exitoso\n")
            
            escribir_log(ruta_log_interfaz, f"✅ Archivo {idx} procesado: {secciones_extraidas} secciones extraídas")
            if log_gui_callback:
                log_gui_callback(f"✅ Archivo {idx} procesado: {secciones_extraidas} secciones extraídas", "success")
            
            exitosos += 1
            
        except Exception as e:
            escribir_log(ruta_log_proceso, f"❌ ERROR: {str(e)}\n")
            escribir_log(ruta_log_interfaz, f"❌ Archivo {idx}: Error - {str(e)}")
            
            if log_gui_callback:
                log_gui_callback(f"❌ Archivo {idx}: Error procesando", "error")
            
            fallidos += 1
    
    # --- 6. Limpieza de nombres ---
    escribir_log(ruta_log_proceso, "="*90)
    escribir_log(ruta_log_proceso, "LIMPIANDO NOMBRES DE ARCHIVOS Y CARPETAS...")
    limpiar_nombres_archivos(carpeta_entrada)
    escribir_log(ruta_log_proceso, "✅ Limpieza completada (underscores → espacios)\n")
    
    if log_gui_callback:
        log_gui_callback("", "info")
        log_gui_callback("✅ Limpieza de nombres completada", "success")
    
    # --- 7. Calcular duración ---
    tiempo_fin = time.time()
    duracion_segundos = tiempo_fin - tiempo_inicio
    duracion_formateada = format_duration(duracion_segundos)
    
    # --- 8. Finalizar logs ---
    escribir_log(ruta_log_interfaz, "")
    escribir_log(ruta_log_interfaz, "="*50)
    escribir_log(ruta_log_interfaz, "RESUMEN FINAL")
    escribir_log(ruta_log_interfaz, "="*50)
    escribir_log(ruta_log_interfaz, f"⏱️ Tiempo total: {duracion_formateada}")
    escribir_log(ruta_log_interfaz, f"📊 Archivos procesados: {exitosos}/{total_archivos}")
    escribir_log(ruta_log_interfaz, f"✅ Exitosos: {exitosos}")
    escribir_log(ruta_log_interfaz, f"❌ Con error: {fallidos}")
    escribir_log(ruta_log_interfaz, f"📑 Secciones extraídas: {total_secciones_extraidas}")
    escribir_log(ruta_log_interfaz, "="*50)
    
    escribir_log(ruta_log_proceso, "="*90)
    escribir_log(ruta_log_proceso, "RESUMEN FINAL")
    escribir_log(ruta_log_proceso, f"Fecha finalización: {time.strftime('%d/%m/%Y %H:%M:%S')}")
    escribir_log(ruta_log_proceso, f"Duración: {duracion_formateada}")
    escribir_log(ruta_log_proceso, f"Exitosos: {exitosos}")
    escribir_log(ruta_log_proceso, f"Errores: {fallidos}")
    escribir_log(ruta_log_proceso, f"Secciones extraídas: {total_secciones_extraidas}")
    escribir_log(ruta_log_proceso, "="*90)
    
    if log_gui_callback:
        log_gui_callback("", "info")
        log_gui_callback("="*50, "info")
        log_gui_callback("✅ PROCESAMIENTO COMPLETADO", "success")
        log_gui_callback("="*50, "info")
        log_gui_callback(f"⏱️ Tiempo total: {duracion_formateada}", "info")
        log_gui_callback(f"📊 Archivos procesados: {exitosos}/{total_archivos}", "info")
        log_gui_callback(f"✅ Exitosos: {exitosos}", "success")
        if fallidos > 0:
            log_gui_callback(f"❌ Con error: {fallidos}", "warning")
        log_gui_callback(f"📑 Secciones extraídas: {total_secciones_extraidas}", "info")
    
    if progress_callback:
        progress_callback(total_archivos, total_archivos, "Proceso completado", 100)
    
    # --- 9. Retornar resultado ---
    return {
        'exitoso': True,
        'mensaje': f'Procesamiento completado: {exitosos} exitosos, {fallidos} con errores',
        'archivos_procesados': exitosos,
        'archivos_con_error': fallidos,
        'total': total_archivos,
        'secciones_extraidas': total_secciones_extraidas,
        'duracion': duracion_formateada,
        'ruta_log_interfaz': ruta_log_interfaz,
        'ruta_log_proceso': ruta_log_proceso,
        'carpeta_salida': carpeta_salida
    }


def extraer_paginas_pdf(ruta_pdf: str, paginas: dict, ruta_salida: str):
    """
    Extrae un rango de páginas de un PDF usando PyMuPDF.
    
    Args:
        ruta_pdf: Ruta del PDF original
        paginas: Dict con {"inicio": 1, "fin": 6} (base-1)
        ruta_salida: Ruta donde guardar el PDF extraído
    """
    with fitz.open(ruta_pdf) as pdf:
        nuevo_pdf = fitz.open()
        total_paginas = len(pdf)
        
        # Convertir de base-1 (JSON) a base-0 (PyMuPDF)
        inicio = max(paginas["inicio"] - 1, 0)
        fin = min(paginas["fin"], total_paginas)
        
        for i in range(inicio, fin):
            nuevo_pdf.insert_pdf(pdf, from_page=i, to_page=i)
        
        nuevo_pdf.save(ruta_salida)
        nuevo_pdf.close()


def diagnosticar_renovaciones(
    carpeta_entrada: str,
    progress_callback: Optional[Callable] = None,
    log_gui_callback: Optional[Callable] = None
) -> dict:
    """
    Genera UN SOLO JSON consolidado con estructura de todas las secciones detectadas.
    Similar a diagnostico_rangos.json del workflow de contratos.
    
    Args:
        carpeta_entrada: Ruta de la carpeta con PDFs
        progress_callback: callback(current, total, message, percentage)
        log_gui_callback: callback(mensaje, tipo)
    
    Returns:
        dict: Resultado con JSON consolidado generado
    """
    tiempo_inicio = time.time()
    
    # Validación
    es_valida, mensaje, archivos_pdf = validar_carpeta_entrada(carpeta_entrada)
    
    if not es_valida:
        return {
            'exitoso': False,
            'mensaje': mensaje,
            'json_generado': None,
            'total': 0
        }
    
    total_archivos = len(archivos_pdf)
    archivos_procesados = 0
    fallidos = 0
    
    section_detector = SectionDetector()
    json_generator = JSONGenerator()  # Instancia del generador consolidado
    
    if log_gui_callback:
        log_gui_callback(f"🔍 Modo diagnóstico: Generando JSON consolidado", "info")
        log_gui_callback(f"📂 Carpeta: {carpeta_entrada}", "info")
        log_gui_callback(f"📊 Total archivos: {total_archivos}", "info")
        log_gui_callback("", "info")
    
    for idx, archivo in enumerate(archivos_pdf, 1):
        try:
            if progress_callback:
                progress = int((idx / total_archivos) * 100)
                progress_callback(idx, total_archivos, f"Diagnosticando: {archivo}", progress)
            
            ruta_pdf = os.path.join(carpeta_entrada, archivo)
            
            if log_gui_callback:
                log_gui_callback(f"🔍 Analizando {idx}/{total_archivos}: {archivo}", "info")
            
            # Abrir PDF y extraer texto
            doc = fitz.open(ruta_pdf)
            texto_paginas = [pagina.get_text("text") for pagina in doc]
            
            # Detectar secciones
            resultado_deteccion = section_detector.detectar_todas_secciones(
                texto_paginas,
                log_callback=lambda msg: log_gui_callback(f"  {msg}", "info") if log_gui_callback else None
            )
            
            # Extraer fecha del contrato
            fecha_contrato = None
            for seccion in resultado_deteccion["secciones"]:
                if seccion["tipo_seccion"] in ["Contrato", "Auditoria"]:
                    fecha_contrato = seccion["metadata"].get("fecha_contrato")
                    if fecha_contrato:
                        break
            
            # Agregar archivo al JSON consolidado
            json_generator.agregar_archivo(
                nombre_archivo=archivo,
                resultado_deteccion=resultado_deteccion,
                fecha_contrato=fecha_contrato
            )
            
            archivos_procesados += 1
            doc.close()
            
            if log_gui_callback:
                total_secciones = len(resultado_deteccion["secciones"])
                log_gui_callback(
                    f"  ✅ Analizado: {total_secciones} secciones detectadas", 
                    "success"
                )
            
        except Exception as e:
            fallidos += 1
            if log_gui_callback:
                log_gui_callback(f"  ❌ Error: {str(e)}", "error")
    
    # Generar el JSON consolidado directamente en la carpeta de trabajo
    if log_gui_callback:
        log_gui_callback("", "info")
        log_gui_callback("📝 Generando JSON consolidado...", "info")
    
    ruta_json = json_generator.generar_json_consolidado(
        ruta_salida=Path(carpeta_entrada),
        nombre_json="diagnostico_rangos.json"
    )
    
    # Obtener resumen
    resumen = json_generator.obtener_resumen()
    
    duracion = format_duration(time.time() - tiempo_inicio)
    
    if log_gui_callback:
        log_gui_callback("", "info")
        log_gui_callback("="*50, "info")
        log_gui_callback("✅ DIAGNÓSTICO COMPLETADO", "success")
        log_gui_callback("="*50, "info")
        log_gui_callback(f"📄 JSON consolidado: {ruta_json.name}", "info")
        log_gui_callback(f"📊 Archivos procesados: {archivos_procesados}/{total_archivos}", "info")
        log_gui_callback(f"📑 Total páginas: {resumen['total_paginas']}", "info")
        log_gui_callback(f"📅 Fechas detectadas: {resumen['fechas_detectadas']}", "info")
        if resumen['fechas_no_detectadas'] > 0:
            log_gui_callback(
                f"⚠️ Fechas no detectadas: {resumen['fechas_no_detectadas']}", 
                "warning"
            )
        log_gui_callback(f"📂 Ubicación: {carpeta_entrada}", "info")
        log_gui_callback(f"⏱️ Tiempo: {duracion}", "info")
    
    if progress_callback:
        progress_callback(total_archivos, total_archivos, "Diagnóstico completado", 100)
    
    return {
        'exitoso': True,
        'mensaje': f'Diagnóstico completado: JSON consolidado con {archivos_procesados} archivos',
        'json_generado': str(ruta_json),
        'archivos_procesados': archivos_procesados,
        'total': total_archivos,
        'fallidos': fallidos,
        'carpeta_salida': carpeta_entrada,
        'duracion': duracion,
        'resumen': resumen
    }