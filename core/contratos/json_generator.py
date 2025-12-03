"""
Generador de JSON consolidado para diagnóstico de contratos.
Ubicación: core/contratos/json_generator.py

Genera un archivo JSON único con los rangos detectados de todos los PDFs procesados.
"""

import json
import os


class JSONGenerator:
    """
    Generador de JSON consolidado para diagnóstico de contratos.
    
    Acumula información de múltiples PDFs y genera un archivo JSON único
    con la estructura de secciones detectadas.
    """
    
    def __init__(self):
        """Inicializa el generador con un diccionario vacío."""
        self.datos = {}
    
    def agregar_archivo(self, nombre_archivo, info):
        """
        Agrega información de un PDF al consolidado.
        
        Args:
            nombre_archivo (str): Nombre del archivo PDF
            info (dict): Información retornada por SectionDetector.detectar_todas_secciones()
                         Estructura esperada:
                         {
                             'secciones': {
                                 'Contrato de Trabajo': {'inicio': 1, 'fin': 15},
                                 ...
                             },
                             'fecha_contrato': str or None,
                             'fecha_origen': str ('sunat')
                         }
        """
        # Construir estructura para este archivo
        self.datos[nombre_archivo] = {
            'total_paginas': self._calcular_total_paginas(info['secciones']),
            'fecha_contrato': info.get('fecha_contrato'),
            'fecha_origen': info.get('fecha_origen', 'sunat'),
            'secciones': info['secciones']
        }
    
    def _calcular_total_paginas(self, secciones):
        """
        Calcula el total de páginas del PDF basándose en las secciones detectadas.
        
        Args:
            secciones (dict): Diccionario de secciones detectadas
        
        Returns:
            int: Número total de páginas (máximo fin encontrado)
        """
        max_pagina = 0
        
        for seccion, rango in secciones.items():
            if rango is not None and 'fin' in rango:
                if rango['fin'] > max_pagina:
                    max_pagina = rango['fin']
        
        return max_pagina if max_pagina > 0 else 0
    
    def generar_json_consolidado(self, ruta_salida):
        """
        Escribe el JSON consolidado en un archivo.
        
        Args:
            ruta_salida (str): Ruta completa donde guardar el archivo JSON
                              (ejemplo: "/carpeta/diagnostico_rangos.json")
        
        Raises:
            Exception: Si hay error al escribir el archivo
        """
        try:
            with open(ruta_salida, 'w', encoding='utf-8') as f:
                json.dump(self.datos, f, indent=2, ensure_ascii=False)
        except Exception as e:
            raise Exception(f"Error al generar JSON: {str(e)}")
    
    def obtener_resumen(self):
        """
        Genera un resumen estadístico del diagnóstico.
        
        Returns:
            dict: {
                'total_archivos': int,
                'total_secciones_detectadas': int,
                'total_secciones_faltantes': int,
                'archivos_con_errores': list,
                'estadisticas_por_seccion': dict,
                'fechas_desde_sunat': int
            }
        """
        total_archivos = len(self.datos)
        total_secciones_detectadas = 0
        total_secciones_faltantes = 0
        archivos_con_errores = []
        fechas_desde_sunat = 0
        
        # Estadísticas por sección (cuántas veces se detectó cada una)
        estadisticas_por_seccion = {}
        
        for archivo, info in self.datos.items():
            # Verificar si el archivo tiene error
            if 'error' in info:
                archivos_con_errores.append(archivo)
                continue
            
            # Contar si la fecha vino de SUNAT
            if info.get('fecha_origen') == 'sunat' and info.get('fecha_contrato'):
                fechas_desde_sunat += 1
            
            # Contar secciones
            secciones = info.get('secciones', {})
            
            for nombre_seccion, rango in secciones.items():
                # Inicializar contador si no existe
                if nombre_seccion not in estadisticas_por_seccion:
                    estadisticas_por_seccion[nombre_seccion] = {
                        'detectadas': 0,
                        'faltantes': 0
                    }
                
                # Contar si fue detectada o no
                if rango is not None:
                    total_secciones_detectadas += 1
                    estadisticas_por_seccion[nombre_seccion]['detectadas'] += 1
                else:
                    total_secciones_faltantes += 1
                    estadisticas_por_seccion[nombre_seccion]['faltantes'] += 1
        
        return {
            'total_archivos': total_archivos,
            'total_secciones_detectadas': total_secciones_detectadas,
            'total_secciones_faltantes': total_secciones_faltantes,
            'archivos_con_errores': archivos_con_errores,
            'estadisticas_por_seccion': estadisticas_por_seccion,
            'fechas_desde_sunat': fechas_desde_sunat
        }
    
    def obtener_archivos_incompletos(self, umbral_minimo=10):
        """
        Identifica archivos que tienen menos secciones detectadas que el umbral.
        
        Args:
            umbral_minimo (int): Número mínimo de secciones esperadas (default: 10)
        
        Returns:
            list: Lista de tuplas (nombre_archivo, secciones_detectadas)
        """
        archivos_incompletos = []
        
        for archivo, info in self.datos.items():
            if 'error' in info:
                continue
            
            secciones = info.get('secciones', {})
            secciones_detectadas = sum(1 for rango in secciones.values() if rango is not None)
            
            if secciones_detectadas < umbral_minimo:
                archivos_incompletos.append((archivo, secciones_detectadas))
        
        return archivos_incompletos
    
    def obtener_archivos_sin_fecha(self):
        """
        Identifica archivos donde no se detectó la fecha del contrato.
        
        Returns:
            list: Lista de nombres de archivos sin fecha
        """
        archivos_sin_fecha = []
        
        for archivo, info in self.datos.items():
            if 'error' in info:
                continue
            
            if not info.get('fecha_contrato'):
                archivos_sin_fecha.append(archivo)
        
        return archivos_sin_fecha
    
    def limpiar(self):
        """Limpia todos los datos acumulados."""
        self.datos = {}
    
    def tiene_datos(self):
        """
        Verifica si hay datos acumulados.
        
        Returns:
            bool: True si hay al menos un archivo agregado
        """
        return len(self.datos) > 0
    
    def obtener_total_archivos(self):
        """
        Retorna el número total de archivos acumulados.
        
        Returns:
            int: Número de archivos
        """
        return len(self.datos)
    
    def obtener_info_archivo(self, nombre_archivo):
        """
        Obtiene la información de un archivo específico.
        
        Args:
            nombre_archivo (str): Nombre del archivo a buscar
        
        Returns:
            dict or None: Información del archivo, o None si no existe
        """
        return self.datos.get(nombre_archivo)
    
    def generar_reporte_texto(self):
        """
        Genera un reporte en formato texto legible.
        
        Returns:
            str: Reporte formateado
        """
        lineas = []
        lineas.append("=" * 80)
        lineas.append("REPORTE DE DIAGNÓSTICO DE CONTRATOS")
        lineas.append("=" * 80)
        lineas.append("")
        
        resumen = self.obtener_resumen()
        
        lineas.append(f"Total de archivos procesados: {resumen['total_archivos']}")
        lineas.append(f"Secciones detectadas: {resumen['total_secciones_detectadas']}")
        lineas.append(f"Secciones faltantes: {resumen['total_secciones_faltantes']}")
        lineas.append(f"Fechas extraídas de SUNAT: {resumen['fechas_desde_sunat']}/{resumen['total_archivos']}")
        lineas.append("")
        
        # Estadísticas por sección
        lineas.append("DETECCIÓN POR SECCIÓN:")
        lineas.append("-" * 80)
        for seccion, stats in resumen['estadisticas_por_seccion'].items():
            detectadas = stats['detectadas']
            faltantes = stats['faltantes']
            total = detectadas + faltantes
            porcentaje = (detectadas / total * 100) if total > 0 else 0
            
            lineas.append(f"  {seccion:<60} {detectadas}/{total} ({porcentaje:.1f}%)")
        
        lineas.append("")
        
        # Archivos con problemas
        archivos_sin_fecha = self.obtener_archivos_sin_fecha()
        if archivos_sin_fecha:
            lineas.append("⚠️ ARCHIVOS SIN FECHA DETECTADA:")
            for archivo in archivos_sin_fecha:
                lineas.append(f"  - {archivo}")
            lineas.append("")
        
        archivos_incompletos = self.obtener_archivos_incompletos(10)
        if archivos_incompletos:
            lineas.append("⚠️ ARCHIVOS INCOMPLETOS (<10 secciones):")
            for archivo, num_secciones in archivos_incompletos:
                lineas.append(f"  - {archivo}: {num_secciones}/12 secciones")
            lineas.append("")
        
        if resumen['archivos_con_errores']:
            lineas.append("❌ ARCHIVOS CON ERRORES:")
            for archivo in resumen['archivos_con_errores']:
                lineas.append(f"  - {archivo}")
            lineas.append("")
        
        lineas.append("=" * 80)
        
        return "\n".join(lineas)