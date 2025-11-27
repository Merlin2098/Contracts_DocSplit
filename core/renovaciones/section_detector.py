"""
Detector de secciones para PDFs de Renovaciones.
Detecta 3 secciones:
  1. Contrato (Prórroga de Contrato)
  2. Guia de Peligros (tabla de peligros y riesgos)
  3. Auditoria (Informe de auditoría final)

Autor: Sistema de Procesamiento de Documentos
Versión: 1.1 - Actualizado con patrones reales
"""

import re
from typing import List, Dict, Optional, Callable


class SectionDetector:
    """
    Detecta las 3 secciones en PDFs de renovaciones de contrato.
    Patrones actualizados según documentos reales.
    """
    
    # Patrones de detección actualizados
    PATRON_CONTRATO = r"PR[OÓ]RROGA\s+DE\s+CONTRATO"
    PATRON_GUIA_PELIGROS = r"PELIGROS\s+RIESGOS\s+EVENTO"
    PATRON_AUDITORIA = r"Informe\s+de\s+auditor[ií]a\s+final"
    
    # Patrones adicionales para delimitar fin de contrato
    PATRON_FIRMA_CONTRATO = r"En\s+señal\s+de\s+conformidad.*suscriben"
    PATRON_TITULO_GUIA = r"Gu[ií]a\s+de\s+tipos\s+de\s+peligros"
    
    # Patrón de fecha narrativa: "31 de Octubre del 2025"
    PATRON_FECHA_NARRATIVA = r"(\d{1,2})\s+de\s+(\w+)\s+del\s+(\d{4})"
    
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
        
        # Construir resultado
        resultado = {
            "total_paginas": total_paginas,
            "secciones": [
                {
                    "tipo_seccion": "Contrato",
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
                    "tipo_seccion": "Auditoria",
                    "pagina_inicio": auditoria["inicio"],
                    "pagina_fin": auditoria["fin"],
                    "metadata": {
                        "fecha_contrato": auditoria["fecha"]
                    }
                }
            ]
        }
        
        return resultado
    
    def _detectar_contrato(
        self,
        texto_paginas: List[str],
        log_callback: Optional[Callable] = None
    ) -> Dict:
        """
        Detecta la sección de Contrato (Prórroga de Contrato).
        Usa sistema híbrido para detectar el fin del contrato.
        
        Returns:
            Dict: {"inicio": int o None, "fin": int o None, "fecha": str o None}
        """
        patron_contrato = re.compile(self.PATRON_CONTRATO, re.IGNORECASE)
        patron_fecha = re.compile(self.PATRON_FECHA_NARRATIVA, re.IGNORECASE)
        
        pagina_inicio = None
        fecha_contrato = None
        
        # Buscar primera coincidencia
        for idx, texto in enumerate(texto_paginas):
            if patron_contrato.search(texto):
                pagina_inicio = idx
                
                # Buscar fecha narrativa en las primeras 3 páginas
                for i in range(idx, min(idx + 3, len(texto_paginas))):
                    match_fecha = patron_fecha.search(texto_paginas[i])
                    if match_fecha:
                        dia = match_fecha.group(1).zfill(2)
                        mes_texto = match_fecha.group(2).lower()
                        anio = match_fecha.group(3)
                        
                        # Convertir mes a número
                        mes = self.MESES.get(mes_texto)
                        if mes:
                            fecha_contrato = f"{mes}.{anio}"
                            break
                
                if log_callback:
                    log_callback(f"✓ Contrato detectado en página {idx + 1}")
                    if fecha_contrato:
                        log_callback(f"  Fecha: {fecha_contrato}")
                
                break
        
        # Si se detectó inicio, buscar fin con sistema híbrido
        pagina_fin = None
        if pagina_inicio is not None:
            # OPCIÓN A: Buscar bloque de firma (más confiable)
            patron_firma = re.compile(self.PATRON_FIRMA_CONTRATO, re.IGNORECASE | re.DOTALL)
            
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
                            log_callback(f"  Fin detectado por título de Guía en página {idx}")
                        break
            
            # OPCIÓN C: Fallback - buscar tabla de peligros
            if pagina_fin is None:
                patron_guia = re.compile(self.PATRON_GUIA_PELIGROS, re.IGNORECASE)
                
                for idx in range(pagina_inicio + 1, len(texto_paginas)):
                    if patron_guia.search(texto_paginas[idx]):
                        pagina_fin = idx - 1
                        if log_callback:
                            log_callback(f"  Fin detectado por tabla de peligros en página {idx}")
                        break
            
            # OPCIÓN D: Si no encuentra siguiente sección, buscar Auditoría
            if pagina_fin is None:
                patron_auditoria = re.compile(self.PATRON_AUDITORIA, re.IGNORECASE)
                for idx in range(pagina_inicio + 1, len(texto_paginas)):
                    if patron_auditoria.search(texto_paginas[idx]):
                        pagina_fin = idx - 1
                        if log_callback:
                            log_callback(f"  Fin detectado por Auditoría en página {idx}")
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
    
    def _detectar_guia_peligros(
        self,
        texto_paginas: List[str],
        log_callback: Optional[Callable] = None
    ) -> Dict:
        """
        Detecta la sección de Guía de Peligros.
        Usa detección dual: título o tabla de peligros.
        
        Returns:
            Dict: {"inicio": int o None, "fin": int o None, "fecha": str o None}
        """
        pagina_inicio = None
        
        # OPCIÓN A: Buscar por título de Guía (más preciso)
        patron_titulo_guia = re.compile(self.PATRON_TITULO_GUIA, re.IGNORECASE)
        
        for idx, texto in enumerate(texto_paginas):
            if patron_titulo_guia.search(texto):
                pagina_inicio = idx
                
                if log_callback:
                    log_callback(f"✓ Guía de Peligros detectada en página {idx + 1} (por título)")
                
                break
        
        # OPCIÓN B: Si no encuentra título, buscar por tabla de peligros
        if pagina_inicio is None:
            patron_tabla = re.compile(self.PATRON_GUIA_PELIGROS, re.IGNORECASE)
            
            for idx, texto in enumerate(texto_paginas):
                if patron_tabla.search(texto):
                    pagina_inicio = idx
                    
                    if log_callback:
                        log_callback(f"✓ Guía de Peligros detectada en página {idx + 1} (por tabla)")
                    
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
        # Fecha en formato YYYY-MM-DD (ej: 2025-10-31)
        patron_fecha_iso = re.compile(r"20\d{2}-(?:0[1-9]|1[0-2])-(?:0[1-9]|[12]\d|3[01])")
        
        pagina_inicio = None
        fecha_contrato = None
        
        # Buscar primera coincidencia
        for idx, texto in enumerate(texto_paginas):
            if patron_auditoria.search(texto):
                pagina_inicio = idx
                
                # Buscar fecha ISO en la misma página
                match_fecha = patron_fecha_iso.search(texto)
                if match_fecha:
                    # Convertir YYYY-MM-DD a MM.YYYY
                    fecha_iso = match_fecha.group(0)
                    partes = fecha_iso.split('-')
                    fecha_contrato = f"{partes[1]}.{partes[0]}"
                
                if log_callback:
                    log_callback(f"✓ Auditoría detectada en página {idx + 1}")
                    if fecha_contrato:
                        log_callback(f"  Fecha: {fecha_contrato}")
                
                break
        
        # Si se detectó inicio, el fin es hasta el final del documento
        pagina_fin = None
        if pagina_inicio is not None:
            pagina_fin = len(texto_paginas) - 1
        
        return {
            "inicio": pagina_inicio,
            "fin": pagina_fin,
            "fecha": fecha_contrato
        }
    
    def extraer_fecha_contrato(self, texto: str) -> Optional[str]:
        """
        Extrae la fecha del contrato en formato narrativo y la convierte a MM.YYYY.
        
        Args:
            texto: Texto donde buscar la fecha
        
        Returns:
            Fecha en formato MM.YYYY o None si no se encuentra
        """
        patron_fecha = re.compile(self.PATRON_FECHA_NARRATIVA, re.IGNORECASE)
        match = patron_fecha.search(texto)
        
        if match:
            dia = match.group(1).zfill(2)
            mes_texto = match.group(2).lower()
            anio = match.group(3)
            
            # Convertir mes a número
            mes = self.MESES.get(mes_texto)
            if mes:
                return f"{mes}.{anio}"
        
        return None