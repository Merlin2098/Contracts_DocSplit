"""
Controller para el workflow de Contratos.
Maneja los 3 pasos: Normalizar, Diagnosticar, Procesar.
"""

import os
import time
from core.contratos.normalizer import (
    normalizar_nombre_pdf,
    generar_nombre_unico,
    validar_archivos_pdf
)
from core.contratos.section_detector import SectionDetector
from core.contratos.json_generator import JSONGenerator
from core.utils.file_utils import validar_carpeta_entrada
from core.utils.logger import (
    escribir_log,
    crear_log_header,
    generar_nombre_log_con_timestamp,
    format_duration,
    obtener_directorio_logs
)


def normalizar_contratos(carpeta_entrada, progress_callback=None, log_gui_callback=None):
    """
    Normaliza los nombres de archivos PDF en la carpeta.
    Paso 1 del workflow de Contratos.
    
    Proceso:
    1. Valida carpeta de entrada
    2. Para cada PDF:
       - Extrae nombre entre guiones
       - Genera nombre único si hay conflicto
       - Renombra archivo
    3. Genera log con timestamp
    4. Mide tiempo de ejecución
    
    Args:
        carpeta_entrada (str): Ruta de la carpeta con PDFs
        progress_callback (callable): Función callback para actualizar progreso
                                     Firma: callback(current, total, message, percentage)
        log_gui_callback (callable): Función callback para logs de interfaz
                                     Firma: callback(mensaje, tipo)
    
    Returns:
        dict: Resultado del procesamiento con estructura:
              {
                  'exitoso': bool,
                  'mensaje': str,
                  'archivos_normalizados': int,
                  'archivos_sin_cambios': int,
                  'total': int,
                  'duracion': str,
                  'ruta_log': str
              }
    """
    # Iniciar medición de tiempo
    tiempo_inicio = time.time()
    
    # --- 1. Validación inicial ---
    es_valida, mensaje, archivos_pdf = validar_carpeta_entrada(carpeta_entrada)
    
    if not es_valida:
        return {
            'exitoso': False,
            'mensaje': mensaje,
            'archivos_normalizados': 0,
            'archivos_sin_cambios': 0,
            'total': 0,
            'duracion': '0s',
            'ruta_log': None
        }
    
    # --- 2. Inicializar variables ---
    total_archivos = len(archivos_pdf)
    normalizados = 0
    sin_cambios = 0
    
    # Generar nombre de log con timestamp en carpeta centralizada
    logs_dir = obtener_directorio_logs("contratos")
    ruta_log = generar_nombre_log_con_timestamp("normalizacion", logs_dir)
    
    # --- 3. Inicializar log ---
    crear_log_header(ruta_log, "NORMALIZACIÓN DE NOMBRES - CONTRATOS")
    escribir_log(ruta_log, f"Carpeta: {carpeta_entrada}")
    escribir_log(ruta_log, f"Total de archivos: {total_archivos}\n")
    
    # Log GUI inicial
    if log_gui_callback:
        log_gui_callback(f"📂 Carpeta seleccionada: {carpeta_entrada}", "info")
        log_gui_callback(f"📊 Total de archivos: {total_archivos}", "info")
        log_gui_callback("", "info")
    
    # --- 4. Procesar cada PDF ---
    for idx, archivo in enumerate(archivos_pdf, 1):
        try:
            # Actualizar progreso
            if progress_callback:
                progress = int((idx / total_archivos) * 100)
                progress_callback(idx, total_archivos, f"Normalizando: {archivo}", progress)
            
            # Normalizar nombre
            nombre_normalizado, fue_modificado = normalizar_nombre_pdf(archivo)
            
            if not fue_modificado:
                # No requiere cambios
                escribir_log(ruta_log, f"[{idx}/{total_archivos}] ⏭️ {archivo} → Sin cambios")
                if log_gui_callback:
                    log_gui_callback(f"⏭️ Archivo {idx}: Sin cambios necesarios", "info")
                sin_cambios += 1
                continue
            
            # Generar nombre único para evitar sobrescribir
            nombre_base = os.path.splitext(nombre_normalizado)[0]
            extension = os.path.splitext(nombre_normalizado)[1]
            nombre_final = generar_nombre_unico(carpeta_entrada, nombre_base, extension)
            
            # Renombrar archivo
            ruta_original = os.path.join(carpeta_entrada, archivo)
            ruta_nueva = os.path.join(carpeta_entrada, nombre_final)
            
            os.rename(ruta_original, ruta_nueva)
            
            # Log
            escribir_log(ruta_log, f"[{idx}/{total_archivos}] ✅ {archivo} → {nombre_final}")
            if log_gui_callback:
                log_gui_callback(f"✅ Archivo {idx}: Normalizado correctamente", "success")
            
            normalizados += 1
            
        except Exception as e:
            escribir_log(ruta_log, f"[{idx}/{total_archivos}] ❌ ERROR en {archivo}: {str(e)}")
            if log_gui_callback:
                log_gui_callback(f"❌ Archivo {idx}: Error al normalizar", "error")
    
    # --- 5. Calcular duración ---
    tiempo_fin = time.time()
    duracion_segundos = tiempo_fin - tiempo_inicio
    duracion_formateada = format_duration(duracion_segundos)
    
    # --- 6. Finalizar log ---
    escribir_log(ruta_log, "")
    escribir_log(ruta_log, "="*50)
    escribir_log(ruta_log, "RESUMEN FINAL")
    escribir_log(ruta_log, "="*50)
    escribir_log(ruta_log, f"⏱️ Tiempo total: {duracion_formateada}")
    escribir_log(ruta_log, f"✅ Archivos normalizados: {normalizados}")
    escribir_log(ruta_log, f"⏭️ Archivos sin cambios: {sin_cambios}")
    escribir_log(ruta_log, f"📊 Total procesados: {total_archivos}")
    escribir_log(ruta_log, "="*50)
    
    # Log GUI final
    if log_gui_callback:
        log_gui_callback("", "info")
        log_gui_callback("="*50, "info")
        log_gui_callback("✅ NORMALIZACIÓN COMPLETADA", "success")
        log_gui_callback("="*50, "info")
        log_gui_callback(f"⏱️ Tiempo total: {duracion_formateada}", "info")
        log_gui_callback(f"✅ Archivos normalizados: {normalizados}", "success")
        log_gui_callback(f"⏭️ Archivos sin cambios: {sin_cambios}", "info")
        log_gui_callback(f"📊 Total procesados: {total_archivos}", "info")
    
    # Actualizar progreso final
    if progress_callback:
        progress_callback(total_archivos, total_archivos, "Normalización completada", 100)
    
    # --- 7. Retornar resultado ---
    return {
        'exitoso': True,
        'mensaje': f'Normalización completada: {normalizados} archivos renombrados',
        'archivos_normalizados': normalizados,
        'archivos_sin_cambios': sin_cambios,
        'total': total_archivos,
        'duracion': duracion_formateada,
        'ruta_log': ruta_log
    }


def diagnosticar_contratos(carpeta_entrada, progress_callback=None, log_gui_callback=None):
    """
    Detecta las 12 secciones en cada PDF y genera JSON consolidado.
    Paso 2 del workflow de Contratos.
    
    Proceso:
    1. Valida carpeta y lista PDFs normalizados
    2. Por cada PDF:
       - Instancia SectionDetector
       - Detecta 12 secciones + fecha + ancla
       - Acumula en JSONGenerator
       - Actualiza progreso y logs
    3. Genera diagnostico_rangos.json
    4. Genera logs (interfaz + técnico)
    
    Args:
        carpeta_entrada (str): Ruta de la carpeta con PDFs normalizados
        progress_callback (callable): Función callback para actualizar progreso
                                     Firma: callback(current, total, message, percentage)
        log_gui_callback (callable): Función callback para logs de interfaz
                                     Firma: callback(mensaje, tipo)
    
    Returns:
        dict: Resultado del procesamiento con estructura:
              {
                  'exitoso': bool,
                  'mensaje': str,
                  'total_archivos': int,
                  'secciones_detectadas': int,
                  'secciones_faltantes': int,
                  'json_generado': str,
                  'duracion': str,
                  'ruta_log': str
              }
    """
    # Iniciar medición de tiempo
    tiempo_inicio = time.time()
    
    # --- 1. Validación inicial ---
    es_valida, mensaje, archivos_pdf = validar_carpeta_entrada(carpeta_entrada)
    
    if not es_valida:
        return {
            'exitoso': False,
            'mensaje': mensaje,
            'total_archivos': 0,
            'secciones_detectadas': 0,
            'secciones_faltantes': 0,
            'json_generado': '',
            'duracion': '0s',
            'ruta_log': None
        }
    
    # --- 2. Inicializar variables ---
    total_archivos = len(archivos_pdf)
    
    # Generar nombre de log con timestamp
    logs_dir = obtener_directorio_logs("contratos")
    ruta_log = generar_nombre_log_con_timestamp("diagnostico", logs_dir)
    
    # --- 3. Inicializar log ---
    crear_log_header(ruta_log, "DIAGNÓSTICO DE SECCIONES - CONTRATOS")
    escribir_log(ruta_log, f"Carpeta: {carpeta_entrada}")
    escribir_log(ruta_log, f"Total de archivos: {total_archivos}\n")
    
    # Log GUI inicial
    if log_gui_callback:
        log_gui_callback(f"📂 Carpeta seleccionada: {carpeta_entrada}", "info")
        log_gui_callback(f"📊 Total de archivos: {total_archivos}", "info")
        log_gui_callback("", "info")
    
    # --- 4. Inicializar generador JSON ---
    json_gen = JSONGenerator()
    
    # --- 5. Procesar cada PDF ---
    for idx, archivo in enumerate(archivos_pdf, 1):
        try:
            ruta_pdf = os.path.join(carpeta_entrada, archivo)
            
            # Actualizar progreso
            if progress_callback:
                progress = int((idx / total_archivos) * 100)
                progress_callback(idx, total_archivos, f"Analizando: {archivo}", progress)
            
            # Log
            escribir_log(ruta_log, f"\n{'='*80}")
            escribir_log(ruta_log, f"[{idx}/{total_archivos}] 📄 Archivo: {archivo}")
            
            if log_gui_callback:
                log_gui_callback(f"\n🔍 Analizando: {archivo}", "info")
            
            # Detectar secciones
            detector = SectionDetector(ruta_pdf)
            info = detector.detectar_todas_secciones()
            
            # Agregar al JSON
            json_gen.agregar_archivo(archivo, info)
            
            # Contar secciones detectadas
            secciones_detectadas = sum(1 for s in info['secciones'].values() if s is not None)
            secciones_faltantes = 12 - secciones_detectadas
            
            # Logs detallados
            escribir_log(ruta_log, f"Total de páginas: {detector.total_paginas}")
            escribir_log(ruta_log, f"Fecha del contrato: {info['fecha_contrato'] or '❌ No detectada'}")
            escribir_log(ruta_log, f"Secciones detectadas: {secciones_detectadas}/12")
            escribir_log(ruta_log, "")
            
            # Log detallado de secciones
            for nombre_seccion, rango in info['secciones'].items():
                if rango is not None:
                    escribir_log(ruta_log, f"  ✅ {nombre_seccion:<60} Páginas {rango['inicio']}-{rango['fin']}")
                else:
                    escribir_log(ruta_log, f"  ❌ {nombre_seccion:<60} No detectado")
            
            # Log GUI resumido
            if log_gui_callback:
                estado = "success" if secciones_detectadas >= 10 else "warning"
                log_gui_callback(f"  ✅ Detectadas: {secciones_detectadas}/12 secciones", estado)
                
                if info['fecha_contrato']:
                    log_gui_callback(f"  📅 Fecha: {info['fecha_contrato']}", "info")
                else:
                    log_gui_callback(f"  ⚠️ Fecha no detectada", "warning")
                
            
        except Exception as e:
            escribir_log(ruta_log, f"[{idx}/{total_archivos}] ❌ ERROR en {archivo}: {str(e)}")
            if log_gui_callback:
                log_gui_callback(f"❌ Error en {archivo}: {str(e)}", "error")
    
    # --- 6. Generar JSON consolidado ---
    json_path = os.path.join(carpeta_entrada, "diagnostico_rangos.json")
    
    try:
        json_gen.generar_json_consolidado(json_path)
        escribir_log(ruta_log, f"\n✅ JSON generado: {json_path}")
        
        if log_gui_callback:
            log_gui_callback("", "info")
            log_gui_callback(f"✅ JSON generado: {json_path}", "success")
    except Exception as e:
        escribir_log(ruta_log, f"\n❌ ERROR al generar JSON: {str(e)}")
        if log_gui_callback:
            log_gui_callback(f"❌ Error al generar JSON: {str(e)}", "error")
        
        return {
            'exitoso': False,
            'mensaje': f'Error al generar JSON: {str(e)}',
            'total_archivos': total_archivos,
            'secciones_detectadas': 0,
            'secciones_faltantes': 0,
            'json_generado': '',
            'duracion': '0s',
            'ruta_log': ruta_log
        }
    
    # --- 7. Obtener resumen ---
    resumen = json_gen.obtener_resumen()
    
    # --- 8. Calcular duración ---
    tiempo_fin = time.time()
    duracion_segundos = tiempo_fin - tiempo_inicio
    duracion_formateada = format_duration(duracion_segundos)
    
    # --- 9. Finalizar log ---
    escribir_log(ruta_log, "")
    escribir_log(ruta_log, "="*80)
    escribir_log(ruta_log, "RESUMEN FINAL")
    escribir_log(ruta_log, "="*80)
    escribir_log(ruta_log, f"⏱️ Tiempo total: {duracion_formateada}")
    escribir_log(ruta_log, f"📊 Total de archivos: {resumen['total_archivos']}")
    escribir_log(ruta_log, f"✅ Secciones detectadas: {resumen['total_secciones_detectadas']}")
    escribir_log(ruta_log, f"❌ Secciones faltantes: {resumen['total_secciones_faltantes']}")
    escribir_log(ruta_log, f"📄 JSON generado: {json_path}")
    escribir_log(ruta_log, "="*80)
    
    # Estadísticas por sección
    escribir_log(ruta_log, "\nESTADÍSTICAS POR SECCIÓN:")
    escribir_log(ruta_log, "-"*80)
    for seccion, stats in resumen['estadisticas_por_seccion'].items():
        detectadas = stats['detectadas']
        faltantes = stats['faltantes']
        total = detectadas + faltantes
        porcentaje = (detectadas / total * 100) if total > 0 else 0
        escribir_log(ruta_log, f"  {seccion:<60} {detectadas}/{total} ({porcentaje:.1f}%)")
    
    # Log GUI final
    if log_gui_callback:
        log_gui_callback("", "info")
        log_gui_callback("="*50, "info")
        log_gui_callback("✅ DIAGNÓSTICO COMPLETADO", "success")
        log_gui_callback("="*50, "info")
        log_gui_callback(f"⏱️ Tiempo total: {duracion_formateada}", "info")
        log_gui_callback(f"📊 Archivos procesados: {resumen['total_archivos']}", "info")
        log_gui_callback(f"✅ Secciones detectadas: {resumen['total_secciones_detectadas']}", "success")
        log_gui_callback(f"❌ Secciones faltantes: {resumen['total_secciones_faltantes']}", "warning" if resumen['total_secciones_faltantes'] > 0 else "info")
    
    # Actualizar progreso final
    if progress_callback:
        progress_callback(total_archivos, total_archivos, "Diagnóstico completado", 100)
    
    # --- 10. Retornar resultado ---
    return {
        'exitoso': True,
        'mensaje': f'Diagnóstico completado: {resumen["total_secciones_detectadas"]} secciones detectadas',
        'total_archivos': resumen['total_archivos'],
        'secciones_detectadas': resumen['total_secciones_detectadas'],
        'secciones_faltantes': resumen['total_secciones_faltantes'],
        'json_generado': json_path,
        'duracion': duracion_formateada,
        'ruta_log': ruta_log
    }