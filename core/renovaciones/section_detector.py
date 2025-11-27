"""
Detector de secciones para workflow de Renovaciones.
Detecta: Renovacion de Contrato, Guía de Peligros, Auditoría.
Extrae fecha de contrato desde la página de Auditoría.
"""

import re
from typing import List, Dict, Tuple, Optional


class SectionDetector:
    """
    Detecta y clasifica las 3 secciones principales en PDFs de renovaciones.
    """
    
    PATRONES = {
        "renovacion": [
            "PRÓRROGA DE CONTRATO",
            "PRORROGA DE CONTRATO",
            "Renovación de Contrato",
            "Renovacion de Contrato",
            "RENOVACIÓN DE CONTRATO",
            "RENOVACION DE CONTRATO"
        ],
        "guia_peligros": [
            "Guía de tipos de peligros y riesgos asociados",
            "Guia de tipos de peligros",
            "tipos de peligros y riesgos",
            "PELIGROS RIESGOS"
        ],
        "auditoria": [
            "Informe de auditoría final",
            "Informe de auditoria final",
            "INFORME DE AUDITORÍA FINAL",
            "INFORME DE AUDITORIA FINAL",
            "Fecha de creación:"
        ]
    }
    
    def __init__(self):
        self.log_callback = None
    
    def detectar_todas_secciones(
        self, 
        texto_paginas: List[str],
        log_callback=None
    ) -> Dict:
        """
        Detecta todas las secciones en el PDF completo.
        
        Args:
            texto_paginas: Lista con texto extraído por página
            log_callback: Función para logging (opcional)
        
        Returns:
            Dict con estructura:
            {
                "total_paginas": int,
                "secciones": [
                    {
                        "tipo_seccion": str,
                        "pagina_inicio": int,
                        "pagina_fin": int,
                        "total_paginas_seccion": int,
                        "metadata": dict
                    },
                    ...
                ],
                "errores": []
            }
        """
        self.log_callback = log_callback
        n_paginas = len(texto_paginas)
        
        resultado = {
            "total_paginas": n_paginas,
            "secciones": [],
            "errores": []
        }
        
        if log_callback:
            log_callback(f"📄 Analizando {n_paginas} páginas...")
        
        # Detectar auditoría primero (para extraer fecha)
        auditorias, fecha_contrato = self._detectar_auditorias(texto_paginas)
        
        # Detectar renovación de contrato
        renovaciones = self._detectar_renovaciones(texto_paginas, fecha_contrato)
        resultado["secciones"].extend(renovaciones)
        
        # Detectar guías de peligro
        guias = self._detectar_guias_peligro(texto_paginas)
        resultado["secciones"].extend(guias)
        
        # Agregar auditorías
        resultado["secciones"].extend(auditorias)
        
        # Ordenar por página de inicio
        resultado["secciones"].sort(key=lambda x: x["pagina_inicio"])
        
        if log_callback:
            log_callback(f"✅ Detección completa: {len(resultado['secciones'])} secciones encontradas")
        
        return resultado
    
    def _detectar_renovaciones(
        self, 
        texto_paginas: List[str],
        fecha_contrato: Optional[str]
    ) -> List[Dict]:
        """
        Detecta renovaciones de contrato.
        La renovación va desde la página 0 hasta antes de la guía de peligros.
        """
        renovaciones = []
        n_paginas = len(texto_paginas)
        
        # Buscar inicio de renovación (primera página con patrón)
        inicio_renovacion = None
        for i, texto in enumerate(texto_paginas):
            texto_lower = texto.lower()
            if any(patron.lower() in texto_lower for patron in self.PATRONES["renovacion"]):
                inicio_renovacion = i
                break
        
        if inicio_renovacion is None:
            if self.log_callback:
                self.log_callback("  ⚠️ No se detectó renovación de contrato")
            return []
        
        # Buscar fin de renovación (antes de guía de peligros o auditoría)
        fin_renovacion = n_paginas - 1
        
        # Buscar inicio de guía de peligros
        for i, texto in enumerate(texto_paginas):
            texto_lower = texto.lower()
            if any(patron.lower() in texto_lower for patron in self.PATRONES["guia_peligros"]):
                fin_renovacion = i - 1
                break
        
        # Si no hay guía, buscar auditoría
        if fin_renovacion == n_paginas - 1:
            for i, texto in enumerate(texto_paginas):
                texto_lower = texto.lower()
                if any(patron.lower() in texto_lower for patron in self.PATRONES["auditoria"]):
                    fin_renovacion = i - 1
                    break
        
        # Validar rango
        if fin_renovacion < inicio_renovacion:
            fin_renovacion = inicio_renovacion
        
        renovacion = {
            "tipo_seccion": "Renovacion de Contrato",
            "pagina_inicio": inicio_renovacion,
            "pagina_fin": fin_renovacion,
            "total_paginas_seccion": fin_renovacion - inicio_renovacion + 1,
            "metadata": {
                "fecha_contrato": fecha_contrato
            }
        }
        renovaciones.append(renovacion)
        
        if self.log_callback:
            self.log_callback(
                f"  ✓ Renovación de Contrato: páginas {inicio_renovacion}-{fin_renovacion} "
                f"(Fecha: {fecha_contrato})"
            )
        
        return renovaciones
    
    def _detectar_guias_peligro(self, texto_paginas: List[str]) -> List[Dict]:
        """
        Detecta guías de peligro usando marcador de tabla de peligros.
        """
        guias = []
        n_paginas = len(texto_paginas)
        
        # Buscar páginas con el patrón de guía de peligros
        paginas_candidatas = []
        for i, texto in enumerate(texto_paginas):
            texto_lower = texto.lower()
            if any(patron.lower() in texto_lower for patron in self.PATRONES["guia_peligros"]):
                paginas_candidatas.append(i)
        
        if not paginas_candidatas:
            if self.log_callback:
                self.log_callback("  ⚠️ No se detectaron guías de peligro")
            return []
        
        inicio = paginas_candidatas[0]
        fin = inicio
        
        # Buscar paginación interna tipo "Page X of Y"
        for j in range(inicio, min(inicio + 15, n_paginas)):
            texto_lower = texto_paginas[j].lower()
            match = re.search(r'page\s+(\d+)\s+of\s+(\d+)', texto_lower)
            if match:
                pagina_actual = int(match.group(1))
                total_paginas = int(match.group(2))
                
                # Si encontramos la última página, ese es el fin
                if pagina_actual == total_paginas:
                    fin = j
                    break
        
        # Si no encontramos paginación, buscar hasta antes de auditoría
        if fin == inicio:
            for j in range(inicio + 1, n_paginas):
                texto_lower = texto_paginas[j].lower()
                if any(patron.lower() in texto_lower for patron in self.PATRONES["auditoria"]):
                    fin = j - 1
                    break
            else:
                fin = n_paginas - 1
        
        guia = {
            "tipo_seccion": "Guia de Peligro",
            "pagina_inicio": inicio,
            "pagina_fin": fin,
            "total_paginas_seccion": fin - inicio + 1,
            "metadata": {
                "tiene_paginacion": fin > inicio
            }
        }
        guias.append(guia)
        
        if self.log_callback:
            self.log_callback(f"  ✓ Guía de Peligro: páginas {inicio}-{fin}")
        
        return guias
    
    def _detectar_auditorias(
        self, 
        texto_paginas: List[str]
    ) -> Tuple[List[Dict], Optional[str]]:
        """
        Detecta informes de auditoría y extrae la fecha del contrato.
        
        Returns:
            Tuple: (lista de auditorías, fecha_contrato en formato MM.YYYY)
        """
        auditorias = []
        fecha_contrato = None
        
        # Buscar todas las páginas con el patrón de auditoría
        paginas_aud = []
        for i, texto in enumerate(texto_paginas):
            texto_lower = texto.lower()
            if any(patron.lower() in texto_lower for patron in self.PATRONES["auditoria"]):
                paginas_aud.append(i)
        
        if not paginas_aud:
            if self.log_callback:
                self.log_callback("  ⚠️ No se detectaron auditorías")
            return [], None
        
        # Agrupar páginas consecutivas
        inicio = paginas_aud[0]
        fin = paginas_aud[-1]
        
        # Extraer fecha del contrato de la página de auditoría
        fecha_contrato = self._extraer_fecha_auditoria(texto_paginas, inicio, fin)
        
        auditoria = {
            "tipo_seccion": "Auditoria",
            "pagina_inicio": inicio,
            "pagina_fin": fin,
            "total_paginas_seccion": fin - inicio + 1,
            "metadata": {
                "fecha_contrato": fecha_contrato
            }
        }
        auditorias.append(auditoria)
        
        if self.log_callback:
            self.log_callback(f"  ✓ Auditoría: páginas {inicio}-{fin} (Fecha: {fecha_contrato})")
        
        return auditorias, fecha_contrato
    
    def _extraer_fecha_auditoria(
        self, 
        texto_paginas: List[str], 
        inicio_aud: int,
        fin_aud: int
    ) -> Optional[str]:
        """
        Extrae la fecha del contrato desde la página de auditoría.
        Busca patrón: "Fecha de creación: YYYY-MM-DD"
        Retorna formato: "MM.YYYY"
        
        Args:
            texto_paginas: Lista de textos por página
            inicio_aud: Índice de inicio de auditoría
            fin_aud: Índice de fin de auditoría
        
        Returns:
            Fecha en formato "MM.YYYY" o None si no se encuentra
        """
        # Buscar en todas las páginas de auditoría
        for i in range(inicio_aud, fin_aud + 1):
            if i >= len(texto_paginas):
                continue
            
            texto = texto_paginas[i]
            
            # Patrón: "Fecha de creación: YYYY-MM-DD"
            patron = r'Fecha de creación:\s*(\d{4})-(\d{2})-(\d{2})'
            match = re.search(patron, texto, re.IGNORECASE)
            
            if match:
                año = match.group(1)
                mes = match.group(2)
                # Formato: MM.YYYY
                return f"{mes}.{año}"
        
        return None