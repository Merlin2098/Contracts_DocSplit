"""
Controlador para el módulo de Contratos.
Ubicación: controllers/contratos_controller.py

Orquesta las tres fases del workflow:
1. Normalizar: Renombra PDFs según nombre del trabajador
2. Diagnosticar: Detecta las 12 secciones y genera JSON consolidado
3. Procesar: Extrae secciones individuales basándose en el JSON
"""

import os
import json
from datetime import datetime
from core.contratos.normalizer import normalizar_nombre_pdf, generar_nombre_unico
from core.contratos.section_detector import SectionDetector
from core.contratos.json_generator import JSONGenerator
from core.contratos.processor import (
    procesar_pdf_individual,
    obtener_carpeta_trabajador_unica,
    validar_json_diagnostico,
    calcular_total_secciones
)
from core.utils.logger import (
    obtener_directorio_logs,
    generar_nombre_log_con_timestamp,
    escribir_log,
    crear_log_header,
    format_duration
)


def normalizar_contratos(carpeta_entrada, progress_callback=None, log_gui_callback=None):
    """
    Fase 1: Normaliza los nombres de los PDFs de contratos.
    
    Args:
        carpeta_entrada (str): Ruta de la carpeta con los PDFs
        progress_callback (callable): Función para reportar progreso
            Firma: progress_callback(current, total, message, percentage)
        log_gui_callback (callable): Función para enviar logs a la GUI
            Firma: log_gui_callback(mensaje, tipo)
    
    Returns:
        dict: {
            'exitoso': bool,
            'mensaje': str,
            'archivos_normalizados': int,
            'ruta_log': str,
            'duracion': str
        }
    """
    inicio = datetime.now()
    
    # Inicializar logger usando la estructura correcta
    carpeta_logs = obtener_directorio_logs("contratos", crear=True)
    ruta_log = generar_nombre_log_con_timestamp("normalizacion", carpeta_logs)
    crear_log_header(ruta_log, "NORMALIZACIÓN DE CONTRATOS")
    
    try:
        escribir_log(ruta_log, "="*80)
        escribir_log(ruta_log, "INICIO DE NORMALIZACIÓN DE CONTRATOS")
        escribir_log(ruta_log, "="*80)
        escribir_log(ruta_log, f"Carpeta de entrada: {carpeta_entrada}")
        
        # Verificar que la carpeta existe
        if not os.path.isdir(carpeta_entrada):
            mensaje = f"La carpeta no existe: {carpeta_entrada}"
            escribir_log(ruta_log, f"ERROR: {mensaje}")
            if log_gui_callback:
                log_gui_callback(f"❌ {mensaje}", "error")
            
            return {
                'exitoso': False,
                'mensaje': mensaje,
                'archivos_normalizados': 0,
                'ruta_log': ruta_log,
                'duracion': '0s'
            }
        
        # Listar PDFs
        archivos = [f for f in os.listdir(carpeta_entrada) if f.lower().endswith('.pdf')]
        total_archivos = len(archivos)
        
        escribir_log(ruta_log, f"PDFs detectados: {total_archivos}")
        
        if log_gui_callback:
            log_gui_callback(f"📁 Carpeta: {carpeta_entrada}", "info")
            log_gui_callback(f"📄 PDFs encontrados: {total_archivos}", "info")
            log_gui_callback("", "info")
        
        if total_archivos == 0:
            mensaje = "No se encontraron archivos PDF en la carpeta"
            escribir_log(ruta_log, f"WARNING: {mensaje}")
            if log_gui_callback:
                log_gui_callback(f"⚠️ {mensaje}", "warning")
            
            return {
                'exitoso': False,
                'mensaje': mensaje,
                'archivos_normalizados': 0,
                'ruta_log': ruta_log,
                'duracion': '0s'
            }
        
        # Inicializar contadores
        archivos_normalizados = 0
        
        # Procesar cada PDF
        for idx, archivo in enumerate(archivos, 1):
            ruta_completa = os.path.join(carpeta_entrada, archivo)
            
            # Actualizar progreso
            porcentaje = int((idx / total_archivos) * 100)
            if progress_callback:
                progress_callback(idx, total_archivos, f"Procesando: {archivo}", porcentaje)
            
            escribir_log(ruta_log, f"\n--- Procesando [{idx}/{total_archivos}]: {archivo} ---")
            
            try:
                # Normalizar nombre
                nombre_normalizado, fue_modificado = normalizar_nombre_pdf(archivo)
                
                if fue_modificado:
                    # Generar nombre único si ya existe
                    nombre_sin_ext = os.path.splitext(nombre_normalizado)[0]
                    nombre_final = generar_nombre_unico(carpeta_entrada, nombre_sin_ext, ".pdf")
                    ruta_nueva = os.path.join(carpeta_entrada, nombre_final)
                    
                    # Renombrar archivo
                    os.rename(ruta_completa, ruta_nueva)
                    archivos_normalizados += 1
                    
                    escribir_log(ruta_log, f"✅ Normalizado: {archivo} → {nombre_final}")
                    
                    if log_gui_callback:
                        log_gui_callback(
                            f"✅ [{idx}/{total_archivos}] Renombrado: {archivo} → {nombre_final}", 
                            "success"
                        )
                else:
                    escribir_log(ruta_log, f"✅ Ya normalizado: {archivo}")
                    if log_gui_callback:
                        log_gui_callback(
                            f"✅ [{idx}/{total_archivos}] Ya normalizado: {archivo}", 
                            "info"
                        )
            
            except Exception as e:
                escribir_log(ruta_log, f"❌ Error procesando {archivo}: {str(e)}")
                if log_gui_callback:
                    log_gui_callback(
                        f"❌ [{idx}/{total_archivos}] Error en {archivo}: {str(e)}", 
                        "error"
                    )
        
        # Finalizar
        fin = datetime.now()
        duracion = fin - inicio
        duracion_str = format_duration(duracion.total_seconds())
        
        escribir_log(ruta_log, "\n" + "="*80)
        escribir_log(ruta_log, "RESUMEN DE NORMALIZACIÓN")
        escribir_log(ruta_log, "="*80)
        escribir_log(ruta_log, f"Archivos procesados: {total_archivos}")
        escribir_log(ruta_log, f"Archivos normalizados: {archivos_normalizados}")
        escribir_log(ruta_log, f"Duración: {duracion_str}")
        escribir_log(ruta_log, f"Fin: {fin.strftime('%Y-%m-%d %H:%M:%S')}")
        
        if log_gui_callback:
            log_gui_callback("", "info")
            log_gui_callback(f"✅ Normalización completada: {archivos_normalizados}/{total_archivos} archivos", "success")
        
        return {
            'exitoso': True,
            'mensaje': f'Normalización exitosa: {archivos_normalizados}/{total_archivos} archivos',
            'archivos_normalizados': archivos_normalizados,
            'ruta_log': ruta_log,
            'duracion': duracion_str
        }
    
    except Exception as e:
        escribir_log(ruta_log, f"Error crítico en normalización: {str(e)}")
        if log_gui_callback:
            log_gui_callback(f"❌ Error crítico: {str(e)}", "error")
        
        return {
            'exitoso': False,
            'mensaje': f'Error crítico: {str(e)}',
            'archivos_normalizados': 0,
            'ruta_log': ruta_log,
            'duracion': '0s'
        }


def diagnosticar_contratos(carpeta_entrada, progress_callback=None, log_gui_callback=None):
    """
    Fase 2: Diagnostica las secciones de los contratos y genera JSON consolidado.
    
    Args:
        carpeta_entrada (str): Ruta de la carpeta con los PDFs normalizados
        progress_callback (callable): Función para reportar progreso
        log_gui_callback (callable): Función para enviar logs a la GUI
    
    Returns:
        dict: {
            'exitoso': bool,
            'mensaje': str,
            'secciones_detectadas': int,
            'secciones_faltantes': int,
            'ruta_json': str,
            'ruta_log': str,
            'duracion': str
        }
    """
    inicio = datetime.now()
    
    # Inicializar logger usando la estructura correcta
    carpeta_logs = obtener_directorio_logs("contratos", crear=True)
    ruta_log = generar_nombre_log_con_timestamp("diagnostico", carpeta_logs)
    crear_log_header(ruta_log, "DIAGNÓSTICO DE CONTRATOS")
    
    try:
        escribir_log(ruta_log, "="*80)
        escribir_log(ruta_log, "INICIO DE DIAGNÓSTICO DE CONTRATOS")
        escribir_log(ruta_log, "="*80)
        escribir_log(ruta_log, f"Carpeta de entrada: {carpeta_entrada}")
        
        # Verificar carpeta
        if not os.path.isdir(carpeta_entrada):
            mensaje = f"La carpeta no existe: {carpeta_entrada}"
            escribir_log(ruta_log, f"ERROR: {mensaje}")
            if log_gui_callback:
                log_gui_callback(f"❌ {mensaje}", "error")
            
            return {
                'exitoso': False,
                'mensaje': mensaje,
                'secciones_detectadas': 0,
                'secciones_faltantes': 0,
                'ruta_json': '',
                'ruta_log': ruta_log,
                'duracion': '0s'
            }
        
        # Listar PDFs
        archivos = [f for f in os.listdir(carpeta_entrada) if f.lower().endswith('.pdf')]
        total_archivos = len(archivos)
        
        escribir_log(ruta_log, f"PDFs detectados: {total_archivos}")
        
        if log_gui_callback:
            log_gui_callback(f"📁 Carpeta: {carpeta_entrada}", "info")
            log_gui_callback(f"📄 PDFs encontrados: {total_archivos}", "info")
            log_gui_callback("", "info")
        
        if total_archivos == 0:
            mensaje = "No se encontraron archivos PDF en la carpeta"
            escribir_log(ruta_log, f"WARNING: {mensaje}")
            if log_gui_callback:
                log_gui_callback(f"⚠️ {mensaje}", "warning")
            
            return {
                'exitoso': False,
                'mensaje': mensaje,
                'secciones_detectadas': 0,
                'secciones_faltantes': 0,
                'ruta_json': '',
                'ruta_log': ruta_log,
                'duracion': '0s'
            }
        
        # Inicializar generador JSON
        json_gen = JSONGenerator()
        
        # Procesar cada PDF
        for idx, archivo in enumerate(archivos, 1):
            ruta_completa = os.path.join(carpeta_entrada, archivo)
            
            # Actualizar progreso
            porcentaje = int((idx / total_archivos) * 100)
            if progress_callback:
                progress_callback(idx, total_archivos, f"Diagnosticando: {archivo}", porcentaje)
            
            escribir_log(ruta_log, f"\n--- Diagnosticando [{idx}/{total_archivos}]: {archivo} ---")
            
            try:
                # Inicializar detector con la ruta del PDF
                detector = SectionDetector(ruta_completa)
                
                # Detectar secciones
                resultado = detector.detectar_todas_secciones()
                
                # Agregar al JSON consolidado
                json_gen.agregar_archivo(archivo, resultado)
                
                # Contar detecciones
                secciones = resultado.get('secciones', {})
                detectadas = sum(1 for r in secciones.values() if r is not None)
                faltantes = sum(1 for r in secciones.values() if r is None)
                
                escribir_log(ruta_log, f"Secciones detectadas: {detectadas}/12")
                escribir_log(ruta_log, f"Fecha contrato: {resultado.get('fecha_contrato', 'No detectada')}")
                
                if log_gui_callback:
                    log_gui_callback(
                        f"✅ [{idx}/{total_archivos}] {archivo}: {detectadas}/12 secciones detectadas",
                        "success" if detectadas >= 10 else "warning"
                    )
            
            except Exception as e:
                escribir_log(ruta_log, f"❌ Error diagnosticando {archivo}: {str(e)}")
                if log_gui_callback:
                    log_gui_callback(
                        f"❌ [{idx}/{total_archivos}] Error en {archivo}: {str(e)}",
                        "error"
                    )
        
        # Generar JSON consolidado
        ruta_json = os.path.join(carpeta_entrada, "diagnostico_rangos.json")
        json_gen.generar_json_consolidado(ruta_json)
        
        escribir_log(ruta_log, f"\n✅ JSON consolidado generado: {ruta_json}")
        
        # Obtener resumen
        resumen = json_gen.obtener_resumen()
        
        # Finalizar
        fin = datetime.now()
        duracion = fin - inicio
        duracion_str = format_duration(duracion.total_seconds())
        
        escribir_log(ruta_log, "\n" + "="*80)
        escribir_log(ruta_log, "RESUMEN DE DIAGNÓSTICO")
        escribir_log(ruta_log, "="*80)
        escribir_log(ruta_log, f"Archivos procesados: {resumen['total_archivos']}")
        escribir_log(ruta_log, f"Secciones detectadas: {resumen['total_secciones_detectadas']}")
        escribir_log(ruta_log, f"Secciones faltantes: {resumen['total_secciones_faltantes']}")
        escribir_log(ruta_log, f"Duración: {duracion_str}")
        escribir_log(ruta_log, f"Fin: {fin.strftime('%Y-%m-%d %H:%M:%S')}")
        
        if log_gui_callback:
            log_gui_callback("", "info")
            log_gui_callback(f"✅ Diagnóstico completado: {resumen['total_secciones_detectadas']} secciones detectadas", "success")
            log_gui_callback(f"📄 JSON generado: {ruta_json}", "info")
        
        return {
            'exitoso': True,
            'mensaje': f"Diagnóstico exitoso: {resumen['total_secciones_detectadas']} secciones detectadas",
            'secciones_detectadas': resumen['total_secciones_detectadas'],
            'secciones_faltantes': resumen['total_secciones_faltantes'],
            'ruta_json': ruta_json,
            'ruta_log': ruta_log,
            'duracion': duracion_str
        }
    
    except Exception as e:
        escribir_log(ruta_log, f"Error crítico en diagnóstico: {str(e)}")
        if log_gui_callback:
            log_gui_callback(f"❌ Error crítico: {str(e)}", "error")
        
        return {
            'exitoso': False,
            'mensaje': f'Error crítico: {str(e)}',
            'secciones_detectadas': 0,
            'secciones_faltantes': 0,
            'ruta_json': '',
            'ruta_log': ruta_log,
            'duracion': '0s'
        }


def procesar_contratos(carpeta_entrada, progress_callback=None, log_gui_callback=None):
    """
    Fase 3: Extrae secciones individuales basándose en el JSON de diagnóstico.
    
    Args:
        carpeta_entrada (str): Ruta de la carpeta con los PDFs y el JSON
        progress_callback (callable): Función para reportar progreso
            Firma: progress_callback(current, total, message, percentage)
        log_gui_callback (callable): Función para enviar logs a la GUI
            Firma: log_gui_callback(mensaje, tipo)
    
    Returns:
        dict: {
            'exitoso': bool,
            'mensaje': str,
            'secciones_extraidas': int,
            'secciones_omitidas': int,
            'errores': int,
            'ruta_salida': str,
            'ruta_log': str,
            'duracion': str
        }
    """
    inicio = datetime.now()
    
    # Inicializar logger usando la estructura correcta
    carpeta_logs = obtener_directorio_logs("contratos", crear=True)
    ruta_log = generar_nombre_log_con_timestamp("procesamiento", carpeta_logs)
    crear_log_header(ruta_log, "PROCESAMIENTO DE CONTRATOS")
    
    try:
        escribir_log(ruta_log, "="*80)
        escribir_log(ruta_log, "INICIO DE PROCESAMIENTO DE CONTRATOS")
        escribir_log(ruta_log, "="*80)
        escribir_log(ruta_log, f"Carpeta de entrada: {carpeta_entrada}")
        
        # Validar carpeta
        if not os.path.isdir(carpeta_entrada):
            mensaje = f"La carpeta no existe: {carpeta_entrada}"
            escribir_log(ruta_log, f"ERROR: {mensaje}")
            if log_gui_callback:
                log_gui_callback(f"❌ {mensaje}", "error")
            
            return {
                'exitoso': False,
                'mensaje': mensaje,
                'secciones_extraidas': 0,
                'secciones_omitidas': 0,
                'errores': 0,
                'ruta_salida': '',
                'ruta_log': ruta_log,
                'duracion': '0s'
            }
        
        # Validar existencia del JSON de diagnóstico
        ruta_json = os.path.join(carpeta_entrada, "diagnostico_rangos.json")
        if not os.path.exists(ruta_json):
            mensaje = "No se encontró el archivo 'diagnostico_rangos.json'. Ejecute primero el diagnóstico."
            escribir_log(ruta_log, f"ERROR: {mensaje}")
            if log_gui_callback:
                log_gui_callback(f"❌ {mensaje}", "error")
            
            return {
                'exitoso': False,
                'mensaje': mensaje,
                'secciones_extraidas': 0,
                'secciones_omitidas': 0,
                'errores': 0,
                'ruta_salida': '',
                'ruta_log': ruta_log,
                'duracion': '0s'
            }
        
        # Cargar JSON
        escribir_log(ruta_log, f"Cargando JSON: {ruta_json}")
        try:
            with open(ruta_json, 'r', encoding='utf-8') as f:
                datos_json = json.load(f)
        except json.JSONDecodeError as e:
            mensaje = f"Error al leer JSON: {str(e)}"
            escribir_log(ruta_log, f"ERROR: {mensaje}")
            if log_gui_callback:
                log_gui_callback(f"❌ {mensaje}", "error")
            
            return {
                'exitoso': False,
                'mensaje': mensaje,
                'secciones_extraidas': 0,
                'secciones_omitidas': 0,
                'errores': 0,
                'ruta_salida': '',
                'ruta_log': ruta_log,
                'duracion': '0s'
            }
        
        # Validar estructura del JSON
        es_valido, mensaje_error = validar_json_diagnostico(datos_json)
        if not es_valido:
            escribir_log(ruta_log, f"ERROR: JSON inválido: {mensaje_error}")
            if log_gui_callback:
                log_gui_callback(f"❌ JSON inválido: {mensaje_error}", "error")
            
            return {
                'exitoso': False,
                'mensaje': f'JSON inválido: {mensaje_error}',
                'secciones_extraidas': 0,
                'secciones_omitidas': 0,
                'errores': 0,
                'ruta_salida': '',
                'ruta_log': ruta_log,
                'duracion': '0s'
            }
        
        total_archivos = len(datos_json)
        escribir_log(ruta_log, f"PDFs a procesar: {total_archivos}")
        
        if log_gui_callback:
            log_gui_callback(f"📁 Carpeta: {carpeta_entrada}", "info")
            log_gui_callback(f"📄 PDFs a procesar: {total_archivos}", "info")
            log_gui_callback("", "info")
        
        # Crear carpeta de salida
        carpeta_salida = os.path.join(carpeta_entrada, "pdfs_extraidos")
        os.makedirs(carpeta_salida, exist_ok=True)
        escribir_log(ruta_log, f"Carpeta de salida: {carpeta_salida}")
        
        # Calcular total de secciones a procesar
        total_secciones = calcular_total_secciones(datos_json)
        escribir_log(ruta_log, f"Total de secciones a extraer: {total_secciones}")
        
        # Contadores
        secciones_extraidas = 0
        secciones_omitidas = 0
        errores = 0
        secciones_procesadas = 0
        
        # Procesar cada PDF
        for nombre_archivo, info_secciones in datos_json.items():
            ruta_pdf = os.path.join(carpeta_entrada, nombre_archivo)
            
            escribir_log(ruta_log, f"\n--- Procesando: {nombre_archivo} ---")
            
            # Validar que el PDF original existe
            if not os.path.exists(ruta_pdf):
                escribir_log(ruta_log, f"⚠️ PDF no encontrado: {nombre_archivo}")
                if log_gui_callback:
                    log_gui_callback(f"⚠️ PDF no encontrado: {nombre_archivo}", "warning")
                continue
            
            # Validar fecha de contrato
            fecha_contrato = info_secciones.get('fecha_contrato')
            if not fecha_contrato:
                escribir_log(ruta_log, f"⚠️ PDF sin fecha de contrato, se omite: {nombre_archivo}")
                if log_gui_callback:
                    log_gui_callback(f"⚠️ Omitido (sin fecha): {nombre_archivo}", "warning")
                continue
            
            # Crear carpeta individual para el trabajador
            nombre_trabajador = os.path.splitext(nombre_archivo)[0]
            carpeta_trabajador = obtener_carpeta_trabajador_unica(carpeta_salida, nombre_trabajador)
            escribir_log(ruta_log, f"Carpeta de trabajador: {carpeta_trabajador}")
            
            # Procesar todas las secciones del PDF
            exitos, errores_pdf, detalles = procesar_pdf_individual(
                ruta_pdf,
                nombre_archivo,
                info_secciones,
                carpeta_trabajador
            )
            
            # Actualizar contadores globales
            secciones_extraidas += exitos
            errores += errores_pdf
            
            # Log de detalles
            for nombre_seccion, estado, mensaje in detalles:
                if estado == 'exito':
                    escribir_log(ruta_log, f"  ✅ Extraído: {mensaje}")
                    secciones_procesadas += 1
                    
                    # Actualizar progreso
                    porcentaje = int((secciones_procesadas / total_secciones) * 100)
                    if progress_callback:
                        progress_callback(
                            secciones_procesadas,
                            total_secciones,
                            f"Extrayendo: {nombre_seccion} - {nombre_trabajador}",
                            porcentaje
                        )
                
                elif estado == 'omitido':
                    escribir_log(ruta_log, f"  ⏭️  Omitido: {nombre_seccion} ({mensaje})")
                    secciones_omitidas += 1
                
                elif estado == 'error':
                    escribir_log(ruta_log, f"  ❌ Error en {nombre_seccion}: {mensaje}")
                    secciones_procesadas += 1
                    
                    # Actualizar progreso incluso con error
                    porcentaje = int((secciones_procesadas / total_secciones) * 100)
                    if progress_callback:
                        progress_callback(
                            secciones_procesadas,
                            total_secciones,
                            f"Error en: {nombre_seccion} - {nombre_trabajador}",
                            porcentaje
                        )
            
            # Log GUI por archivo
            if log_gui_callback:
                if exitos > 0:
                    log_gui_callback(
                        f"✅ {nombre_archivo}: {exitos} secciones extraídas",
                        "success"
                    )
                if errores_pdf > 0:
                    log_gui_callback(
                        f"⚠️ {nombre_archivo}: {errores_pdf} errores",
                        "warning"
                    )
        
        # Finalizar
        fin = datetime.now()
        duracion = fin - inicio
        duracion_str = format_duration(duracion.total_seconds())
        
        escribir_log(ruta_log, "\n" + "="*80)
        escribir_log(ruta_log, "RESUMEN DE PROCESAMIENTO")
        escribir_log(ruta_log, "="*80)
        escribir_log(ruta_log, f"PDFs procesados: {total_archivos}")
        escribir_log(ruta_log, f"Secciones extraídas: {secciones_extraidas}")
        escribir_log(ruta_log, f"Secciones omitidas: {secciones_omitidas}")
        escribir_log(ruta_log, f"Errores: {errores}")
        escribir_log(ruta_log, f"Duración: {duracion_str}")
        escribir_log(ruta_log, f"Fin: {fin.strftime('%Y-%m-%d %H:%M:%S')}")
        
        if log_gui_callback:
            log_gui_callback("", "info")
            log_gui_callback(
                f"✅ Procesamiento completado: {secciones_extraidas} secciones extraídas",
                "success"
            )
            if errores > 0:
                log_gui_callback(f"⚠️ {errores} errores encontrados", "warning")
        
        return {
            'exitoso': True,
            'mensaje': f'Procesamiento exitoso: {secciones_extraidas} secciones extraídas',
            'secciones_extraidas': secciones_extraidas,
            'secciones_omitidas': secciones_omitidas,
            'errores': errores,
            'ruta_salida': carpeta_salida,
            'ruta_log': ruta_log,
            'duracion': duracion_str
        }
    
    except Exception as e:
        escribir_log(ruta_log, f"Error crítico en procesamiento: {str(e)}")
        if log_gui_callback:
            log_gui_callback(f"❌ Error crítico: {str(e)}", "error")
        
        return {
            'exitoso': False,
            'mensaje': f'Error crítico: {str(e)}',
            'secciones_extraidas': 0,
            'secciones_omitidas': 0,
            'errores': 0,
            'ruta_salida': '',
            'ruta_log': ruta_log,
            'duracion': '0s'
        }