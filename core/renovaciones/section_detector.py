"""
Detector de secciones para PDFs de Renovaciones.
Detecta 3 secciones:
  1. Contrato (Prórroga de Contrato)
  2. Guia de Peligros (tabla de peligros y riesgos)
  3. Auditoria (Informe de auditoría final / Final Audit Report)

Autor: Sistema de Procesamiento de Documentos
Versión: 1.7 - Extracción prioritaria de fecha en Cláusula Primera (Antecedentes)
"""

import re
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Callable
from core.utils.regex_renovaciones import (
    PatronesFecha,
    PatronesSecciones,
    buscar_patron_multiple,
    extraer_fecha_normalizada
)


class SectionDetector:
    """
    Detecta las 3 secciones en PDFs de renovaciones de contrato.
    Patrones actualizados según documentos reales.
    """
    
    # Patrones de detección actualizados
    PATRON_CONTRATO = r"(PR[OÓ]RROGA|RENOVACI[OÓ]N)\s+DE\s+CONTRATO"
    PATRON_GUIA_PELIGROS = r"PELIGROS\s+RIESGOS\s+EVENTO"
    PATRON_AUDITORIA = r"(Informe\s+de\s+auditor[ií]a\s+final|Final\s+Audit\s+Report)"
    
    # Patrones adicionales para delimitar fin de contrato
    PATRON_FIRMA_CONTRATO = r"En\s+señal\s+de\s+conformidad.*suscriben"
    PATRON_TITULO_GUIA = r"Gu[ií]a\s+de\s+tipos\s+de\s+peligros"
    
    # Patrón de fecha para PRÓRROGA (Cláusula Primera - fecha de finalización del contrato anterior)
    # Ahora acepta tanto "de" como "del" antes del año
    PATRON_FECHA_FINALIZACION_PRORROGA = r"hasta\s+el\s+(\d{1,2})\s+de\s+(\w+)\s+de(?:l)?\s+(\d{4})"
    
    # Patrón ESPECÍFICO para fecha en antecedentes (Cláusula Primera)
    PATRON_FECHA_ANTECEDENTES = r"prorrogado\s+sucesivamente\s+hasta\s+el\s+(\d{1,2})\s+de\s+(\w+)\s+de(?:l)?\s+(\d{4})"
    
    # Patrón de fecha para RENOVACIÓN (Cláusula Sexta - fecha de inicio del nuevo contrato)
    PATRON_FECHA_INICIO_RENOVACION = r"a\s+partir\s+del\s+(\d{1,2})\s+de[l]?\s+(\w+)\s+del\s+(\d{4})"
    
    # Mapa de meses en español
    MESES = {
        'enero': '01', 'febrero': '02', 'marzo': '03', 'abril': '04',
        'mayo': '05', 'junio': '06', 'julio': '07', 'agosto': '08',
        'setiembre': '09', 'septiembre': '09', 'octubre': '10',
        'noviembre': '11', 'diciembre': '12'
    }
    
    def __init__(self):
        """Inicializa el detector."""
        pass
    
    def detectar_todas_secciones(
        self,
        texto_paginas: List[str],
        log_callback: Optional[Callable] = None
    ) -> Dict:
        """
        Detecta todas las secciones en el PDF.
        
        Args:
            texto_paginas: Lista con el texto de cada página
            log_callback: Función opcional para registrar mensajes
        
        Returns:
            Dict con estructura:
            {
                "total_paginas": int,
                "secciones": [
                    {
                        "tipo_seccion": str,
                        "pagina_inicio": int (base-0) o None,
                        "pagina_fin": int (base-0) o None,
                        "metadata": {
                            "fecha_contrato": str o None
                        }
                    }
                ]
            }
        """
        total_paginas = len(texto_paginas)
        
        # Detectar las 3 secciones
        contrato = self._detectar_contrato(texto_paginas, log_callback)
        guia_peligros = self._detectar_guia_peligros(texto_paginas, log_callback)
        auditoria = self._detectar_auditoria(texto_paginas, log_callback)
        
        # VALIDACIÓN DE RANGOS: Evitar solapamientos
        contrato, guia_peligros, auditoria = self._validar_rangos_secciones(
            contrato, guia_peligros, auditoria, log_callback
        )
        
        # Construir resultado
        resultado = {
            "total_paginas": total_paginas,
            "secciones": [
                {
                    "tipo_seccion": "Renovación de contrato de trabajo",
                    "pagina_inicio": contrato["inicio"],
                    "pagina_fin": contrato["fin"],
                    "metadata": {
                        "fecha_contrato": contrato["fecha"]
                    }
                },
                {
                    "tipo_seccion": "Guia de Peligros",
                    "pagina_inicio": guia_peligros["inicio"],
                    "pagina_fin": guia_peligros["fin"],
                    "metadata": {
                        "fecha_contrato": None
                    }
                },
                {
                    "tipo_seccion": "Renovación auditoria",
                    "pagina_inicio": auditoria["inicio"],
                    "pagina_fin": auditoria["fin"],
                    "metadata": {
                        "fecha_contrato": None  # Ya no se usa fecha de auditoría
                    }
                }
            ]
        }
        
        return resultado
    
    def _validar_rangos_secciones(
        self,
        contrato: Dict,
        guia_peligros: Dict,
        auditoria: Dict,
        log_callback: Optional[Callable] = None
    ) -> tuple:
        """
        Valida que no haya solapamientos entre secciones.
        Prioridad: Contrato > Guía de Peligros > Auditoría
        
        Args:
            contrato: Dict con inicio, fin, fecha
            guia_peligros: Dict con inicio, fin, fecha
            auditoria: Dict con inicio, fin, fecha
            log_callback: Función opcional para registrar mensajes
        
        Returns:
            tuple: (contrato, guia_peligros, auditoria) con rangos ajustados
        """
        ajustes_realizados = []
        
        # VALIDACIÓN 1: Guía de Peligros vs Contrato
        if (contrato["inicio"] is not None and contrato["fin"] is not None and
            guia_peligros["inicio"] is not None):
            
            # Solo ajustar si hay verdadero solapamiento:
            # Guía debe estar DENTRO del rango del Contrato, no solo antes de su fin
            if (guia_peligros["inicio"] >= contrato["inicio"] and 
                guia_peligros["inicio"] <= contrato["fin"]):
                nuevo_inicio = contrato["fin"] + 1
                ajustes_realizados.append(
                    f"Guía de Peligros: inicio ajustado de página {guia_peligros['inicio'] + 1} "
                    f"a página {nuevo_inicio + 1} (evitar solapamiento con Contrato)"
                )
                guia_peligros["inicio"] = nuevo_inicio
        
        # VALIDACIÓN 2: Auditoría vs Guía de Peligros
        if (guia_peligros["inicio"] is not None and guia_peligros["fin"] is not None and
            auditoria["inicio"] is not None):
            
            # Solo ajustar si hay verdadero solapamiento:
            # Auditoría debe estar DENTRO del rango de Guía, no solo antes de su fin
            if (auditoria["inicio"] >= guia_peligros["inicio"] and 
                auditoria["inicio"] <= guia_peligros["fin"]):
                nuevo_inicio = guia_peligros["fin"] + 1
                ajustes_realizados.append(
                    f"Auditoría: inicio ajustado de página {auditoria['inicio'] + 1} "
                    f"a página {nuevo_inicio + 1} (evitar solapamiento con Guía de Peligros)"
                )
                auditoria["inicio"] = nuevo_inicio
        
        # VALIDACIÓN 3: Auditoría vs Contrato (si no hay Guía de Peligros)
        if (contrato["inicio"] is not None and contrato["fin"] is not None and
            auditoria["inicio"] is not None and
            guia_peligros["inicio"] is None):
            
            # Solo ajustar si hay verdadero solapamiento:
            # Auditoría debe estar DENTRO del rango de Contrato, no solo antes de su fin
            if (auditoria["inicio"] >= contrato["inicio"] and 
                auditoria["inicio"] <= contrato["fin"]):
                nuevo_inicio = contrato["fin"] + 1
                ajustes_realizados.append(
                    f"Auditoría: inicio ajustado de página {auditoria['inicio'] + 1} "
                    f"a página {nuevo_inicio + 1} (evitar solapamiento con Contrato)"
                )
                auditoria["inicio"] = nuevo_inicio
        
        # Registrar ajustes en el log
        if ajustes_realizados and log_callback:
            log_callback("⚠️ VALIDACIÓN DE RANGOS:")
            for ajuste in ajustes_realizados:
                log_callback(f"  • {ajuste}")
        
        return contrato, guia_peligros, auditoria
    
    def _detectar_contrato(
        self,
        texto_paginas: List[str],
        log_callback: Optional[Callable] = None
    ) -> Dict:
        """
        Detecta la sección de Contrato (Prórroga o Renovación).
        ASUME que el contrato SIEMPRE empieza en la página 1 (índice 0).
        
        CAMBIO CLAVE: Busca primero la fecha en la Cláusula Primera (Antecedentes)
        antes de buscar en cualquier otra parte del documento.
        
        Returns:
            Dict: {"inicio": int o None, "fin": int o None, "fecha": str o None}
        """
        # INICIO: Siempre es la primera página
        pagina_inicio = 0
        tipo_documento = None
        fecha_contrato = None
        
        if log_callback:
            log_callback(f"✓ Contrato detectado en página 1 (inicio asumido)")
        
        # Obtener texto de la primera página para determinar tipo
        texto_primera_pag = texto_paginas[pagina_inicio]
        
        # Determinar tipo de documento
        if re.search(r"PR[OÓ]RROGA", texto_primera_pag, re.IGNORECASE):
            tipo_documento = 'PRORROGA'
            if log_callback:
                log_callback(f"  Tipo detectado: PRÓRROGA")
        elif re.search(r"RENOVACI[OÓ]N", texto_primera_pag, re.IGNORECASE):
            tipo_documento = 'RENOVACION'
            if log_callback:
                log_callback(f"  Tipo detectado: RENOVACIÓN")
        else:
            # Si no se detecta tipo específico, asumir RENOVACION por defecto
            tipo_documento = 'RENOVACION'
            if log_callback:
                log_callback(f"  Tipo por defecto: RENOVACIÓN (no se detectó PRÓRROGA)")
        
        # EXTRAER FECHA - NUEVA LÓGICA PRIORITARIA
        fecha_contrato = self._extraer_fecha_contrato_prioritaria(
            texto_paginas, tipo_documento, log_callback
        )
        
        # Detectar página final
        pagina_fin = None
        
        # OPCIÓN A (PRIORITARIA): Buscar firma de contrato
        patron_firma = re.compile(self.PATRON_FIRMA_CONTRATO, re.IGNORECASE)
        
        for idx in range(pagina_inicio + 1, len(texto_paginas)):
            if patron_firma.search(texto_paginas[idx]):
                pagina_fin = idx
                if log_callback:
                    log_callback(f"  Fin detectado por firma en página {idx + 1}")
                break
        
        # OPCIÓN B: Si no hay firma, buscar título de Guía
        if pagina_fin is None:
            patron_titulo_guia = re.compile(self.PATRON_TITULO_GUIA, re.IGNORECASE)
            
            for idx in range(pagina_inicio + 1, len(texto_paginas)):
                if patron_titulo_guia.search(texto_paginas[idx]):
                    pagina_fin = idx - 1
                    if log_callback:
                        log_callback(f"  Fin detectado por título de Guía en página {idx + 1}")
                    break
        
        # OPCIÓN C: Fallback - buscar tabla de peligros
        if pagina_fin is None:
            patron_guia = re.compile(self.PATRON_GUIA_PELIGROS, re.IGNORECASE)
            
            for idx in range(pagina_inicio + 1, len(texto_paginas)):
                if patron_guia.search(texto_paginas[idx]):
                    pagina_fin = idx - 1
                    if log_callback:
                        log_callback(f"  Fin detectado por tabla de peligros en página {idx + 1}")
                    break
        
        # OPCIÓN D: Si no encuentra siguiente sección, buscar Auditoría
        if pagina_fin is None:
            patron_auditoria = re.compile(self.PATRON_AUDITORIA, re.IGNORECASE)
            for idx in range(pagina_inicio + 1, len(texto_paginas)):
                if patron_auditoria.search(texto_paginas[idx]):
                    pagina_fin = idx - 1
                    if log_callback:
                        log_callback(f"  Fin detectado por Auditoría en página {idx + 1}")
                    break
        
        # Último recurso: va hasta el final
        if pagina_fin is None:
            pagina_fin = len(texto_paginas) - 1
            if log_callback:
                log_callback(f"  Fin por defecto: última página")
        
        return {
            "inicio": pagina_inicio,
            "fin": pagina_fin,
            "fecha": fecha_contrato
        }
    
    def _extraer_fecha_contrato_prioritaria(
        self,
        texto_paginas: List[str],
        tipo_documento: str,
        log_callback: Optional[Callable] = None
    ) -> Optional[str]:
        """
        Extrae la fecha del contrato con prioridad a la Cláusula Primera.
        
        NUEVA LÓGICA:
        1. Primero buscar fecha ESPECÍFICA en Cláusula Primera (Antecedentes)
        2. Si no encuentra, buscar fecha general en primeras páginas
        3. Aplicar suma de 1 día si es PRÓRROGA
        4. Convertir a formato MM.YYYY
        
        Args:
            texto_paginas: Lista de texto por página
            tipo_documento: 'PRORROGA' o 'RENOVACION'
            log_callback: Función opcional para logging
        
        Returns:
            Fecha en formato MM.YYYY o None
        """
        # Configurar según tipo de documento
        if tipo_documento == 'PRORROGA':
            sumar_dias = 1
            patrones_a_probar = [
                PatronesFecha.FECHA_ANTECEDENTES_PRORROGA,  # Primero antecedentes
                PatronesFecha.FECHA_FINALIZACION_PRORROGA   # Luego general
            ]
        else:  # RENOVACION
            sumar_dias = 0
            patrones_a_probar = [PatronesFecha.FECHA_INICIO_RENOVACION]
        
        # ESTRATEGIA 1: Buscar primero en Cláusula Primera (Antecedentes)
        fecha_extraida = self._buscar_fecha_en_antecedentes(
            texto_paginas, patrones_a_probar, sumar_dias, log_callback
        )
        
        if fecha_extraida:
            return fecha_extraida
        
        # ESTRATEGIA 2: Búsqueda general en primeras 3 páginas
        return self._buscar_fecha_general(
            texto_paginas, patrones_a_probar, sumar_dias, log_callback
        )
    
    def _buscar_fecha_en_antecedentes(
        self,
        texto_paginas: List[str],
        patrones: List[str],
        sumar_dias: int,
        log_callback: Optional[Callable] = None
    ) -> Optional[str]:
        """
        Busca fecha específicamente en la Cláusula Primera (Antecedentes).
        
        Args:
            texto_paginas: Lista de texto por página
            patrones: Lista de patrones regex a probar
            sumar_dias: Días a sumar (1 para PRÓRROGA, 0 para RENOVACIÓN)
            log_callback: Función opcional para logging
        
        Returns:
            Fecha en formato MM.YYYY o None
        """
        patron_antecedentes = re.compile(PatronesSecciones.CLAUSULA_ANTECEDENTES, re.IGNORECASE)
        
        # Buscar Cláusula Primera en las primeras 3 páginas
        for idx in range(min(3, len(texto_paginas))):
            texto = texto_paginas[idx]
            
            if patron_antecedentes.search(texto):
                # Encontrada Cláusula Primera, buscar fecha dentro de esta página
                for patron in patrones:
                    match = re.search(patron, texto, re.IGNORECASE)
                    if match:
                        return self._procesar_match_fecha(match, sumar_dias, log_callback, idx + 1)
                
                # Si no encuentra en esta página, buscar en páginas siguientes (máximo 2)
                for offset in range(1, min(3, len(texto_paginas) - idx)):
                    texto_siguiente = texto_paginas[idx + offset]
                    for patron in patrones:
                        match = re.search(patron, texto_siguiente, re.IGNORECASE)
                        if match:
                            return self._procesar_match_fecha(match, sumar_dias, log_callback, idx + offset + 1)
        
        return None
    
    def _buscar_fecha_general(
        self,
        texto_paginas: List[str],
        patrones: List[str],
        sumar_dias: int,
        log_callback: Optional[Callable] = None
    ) -> Optional[str]:
        """
        Búsqueda general de fecha en primeras páginas (fallback).
        
        Args:
            texto_paginas: Lista de texto por página
            patrones: Lista de patrones regex a probar
            sumar_dias: Días a sumar (1 para PRÓRROGA, 0 para RENOVACIÓN)
            log_callback: Función opcional para logging
        
        Returns:
            Fecha en formato MM.YYYY o None
        """
        # Buscar en las primeras 3 páginas
        for offset in range(min(3, len(texto_paginas))):
            texto = texto_paginas[offset]
            
            for patron in patrones:
                match = re.search(patron, texto, re.IGNORECASE)
                if match:
                    return self._procesar_match_fecha(match, sumar_dias, log_callback, offset + 1)
        
        return None
    
    def _procesar_match_fecha(
        self,
        match: re.Match,
        sumar_dias: int,
        log_callback: Optional[Callable] = None,
        num_pagina: int = None
    ) -> Optional[str]:
        """
        Procesa un match de fecha y lo convierte a formato MM.YYYY.
        
        Args:
            match: Objeto match de regex
            sumar_dias: Días a sumar a la fecha
            log_callback: Función opcional para logging
            num_pagina: Número de página donde se encontró (para logging)
        
        Returns:
            Fecha en formato MM.YYYY o None
        """
        dia = int(match.group(1))
        mes_texto = match.group(2).lower()
        anio = int(match.group(3))
        
        # Convertir mes a número
        mes_num = self.MESES.get(mes_texto)
        if not mes_num:
            if log_callback:
                log_callback(f"  ⚠️ Mes '{mes_texto}' no reconocido")
            return None
        
        try:
            # Crear fecha
            fecha_obj = datetime(anio, int(mes_num), dia)
            
            # Aplicar ajuste solo si es PRÓRROGA
            if sumar_dias > 0:
                fecha_original = fecha_obj.strftime('%d/%m/%Y')
                fecha_obj += timedelta(days=sumar_dias)
                
                if log_callback:
                    log_callback(f"  Fecha original: {fecha_original} + {sumar_dias} día(s)")
            
            fecha_formateada = f"{fecha_obj.strftime('%m')}.{fecha_obj.year}"
            
            if log_callback:
                fuente = f"página {num_pagina}" if num_pagina else "documento"
                log_callback(f"  Fecha extraída: {fecha_formateada} ({fuente})")
            
            return fecha_formateada
            
        except ValueError as e:
            if log_callback:
                log_callback(f"  ⚠️ Error procesando fecha: {e}")
            return None
    
    def _detectar_guia_peligros(
        self,
        texto_paginas: List[str],
        log_callback: Optional[Callable] = None
    ) -> Dict:
        """
        Detecta la sección de Guía de Peligros.
        Usa detección dual: primero tabla de peligros, luego título como fallback.
        
        IMPORTANTE: Prioriza la TABLA sobre el TÍTULO para evitar detecciones prematuras
        cuando el título aparece al final de la sección de Contrato.
        
        Returns:
            Dict: {"inicio": int o None, "fin": int o None, "fecha": str o None}
        """
        pagina_inicio = None
        
        # OPCIÓN A (PRIORITARIA): Buscar por tabla de peligros
        patron_tabla = re.compile(self.PATRON_GUIA_PELIGROS, re.IGNORECASE)
        
        for idx, texto in enumerate(texto_paginas):
            if patron_tabla.search(texto):
                pagina_inicio = idx
                
                if log_callback:
                    log_callback(f"✓ Guía de Peligros detectada en página {idx + 1} (por tabla)")
                
                break
        
        # OPCIÓN B (FALLBACK): Si no encuentra tabla, buscar por título de Guía
        if pagina_inicio is None:
            patron_titulo_guia = re.compile(self.PATRON_TITULO_GUIA, re.IGNORECASE)
            
            for idx, texto in enumerate(texto_paginas):
                if patron_titulo_guia.search(texto):
                    # VALIDACIÓN: Asegurarse que no es una mención prematura
                    # Solo aceptar si NO hay tabla en páginas posteriores cercanas
                    hay_tabla_posterior = False
                    
                    for j in range(idx + 1, min(idx + 3, len(texto_paginas))):
                        if patron_tabla.search(texto_paginas[j]):
                            hay_tabla_posterior = True
                            break
                    
                    # Si hay tabla posterior, esperar a detectarla
                    if hay_tabla_posterior:
                        continue
                    
                    pagina_inicio = idx
                    
                    if log_callback:
                        log_callback(f"✓ Guía de Peligros detectada en página {idx + 1} (por título)")
                    
                    break
        
        # Si se detectó inicio, buscar fin (siguiente sección o final del documento)
        pagina_fin = None
        if pagina_inicio is not None:
            # Buscar inicio de Auditoría como límite
            patron_auditoria = re.compile(self.PATRON_AUDITORIA, re.IGNORECASE)
            
            for idx in range(pagina_inicio + 1, len(texto_paginas)):
                if patron_auditoria.search(texto_paginas[idx]):
                    pagina_fin = idx - 1  # Termina justo antes de Auditoría
                    break
            
            # Si no se encuentra siguiente sección, va hasta el final
            if pagina_fin is None:
                pagina_fin = len(texto_paginas) - 1
        
        return {
            "inicio": pagina_inicio,
            "fin": pagina_fin,
            "fecha": None
        }
    
    def _detectar_auditoria(
        self,
        texto_paginas: List[str],
        log_callback: Optional[Callable] = None
    ) -> Dict:
        """
        Detecta la sección de Auditoría.
        
        Returns:
            Dict: {"inicio": int o None, "fin": int o None, "fecha": str o None}
        """
        patron_auditoria = re.compile(self.PATRON_AUDITORIA, re.IGNORECASE)
        
        pagina_inicio = None
        
        # Buscar primera coincidencia
        for idx, texto in enumerate(texto_paginas):
            if patron_auditoria.search(texto):
                pagina_inicio = idx
                
                if log_callback:
                    log_callback(f"✓ Auditoría detectada en página {idx + 1}")
                
                break
        
        # Si se detectó inicio, el fin es hasta el final del documento
        pagina_fin = None
        if pagina_inicio is not None:
            pagina_fin = len(texto_paginas) - 1
        
        return {
            "inicio": pagina_inicio,
            "fin": pagina_fin,
            "fecha": None  # Ya no se extrae fecha de auditoría
        }
    
    def extraer_fecha_contrato(self, texto: str, tipo_documento: str = 'PRORROGA') -> Optional[str]:
        """
        Extrae la fecha del contrato y la convierte a MM.YYYY.
        DEPRECATED: Usar _extraer_fecha_contrato_prioritaria() que ya incluye la lógica completa.
        
        Args:
            texto: Texto donde buscar la fecha
            tipo_documento: 'PRORROGA' o 'RENOVACION'
        
        Returns:
            Fecha en formato MM.YYYY o None si no se encuentra
        """
        if tipo_documento == 'PRORROGA':
            patron_fecha = re.compile(self.PATRON_FECHA_FINALIZACION_PRORROGA, re.IGNORECASE)
            sumar_dias = 1
        else:  # RENOVACION
            patron_fecha = re.compile(self.PATRON_FECHA_INICIO_RENOVACION, re.IGNORECASE)
            sumar_dias = 0  # RENOVACIÓN: tomar fecha tal cual
        
        match = patron_fecha.search(texto)
        
        if match:
            dia = int(match.group(1))
            mes_texto = match.group(2).lower()
            anio = int(match.group(3))
            
            # Convertir mes a número
            mes_num = self.MESES.get(mes_texto)
            if mes_num:
                try:
                    # Crear fecha
                    fecha_obj = datetime(anio, int(mes_num), dia)
                    
                    # Aplicar ajuste solo si es PRÓRROGA
                    if sumar_dias > 0:
                        fecha_obj += timedelta(days=sumar_dias)
                    
                    return f"{fecha_obj.strftime('%m')}.{fecha_obj.year}"
                except ValueError:
                    return None
        
        return None