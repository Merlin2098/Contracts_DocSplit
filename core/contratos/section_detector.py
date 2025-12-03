"""
Detector de secciones para contratos iniciales.
Ubicación: core/contratos/section_detector.py

Detecta 12 secciones usando:
- Patrones de texto múltiples
- Heurísticas basadas en página ancla (RIT)
- Validación multi-patrón (RISST requiere ≥2 coincidencias)
- Detección condicional (RISST Chinalco solo si existe Auditoría)
- Detección multinivel para Alta SUNAT (Nivel 1: Formulario 1604, Nivel 2: T-Registro)
- Estrategia híbrida para Derechohabientes (valida páginas vacías en rango)
- Detección inteligente de Guía de Peligros (descarta referencias, busca tabla real)
- Detección RISST por máximas coincidencias (evita falsos positivos en menciones)
"""

import os
import re
import fitz  # PyMuPDF
from datetime import datetime, timedelta


class SectionDetector:
    """
    Detector de las 12 secciones de contratos con heurísticas avanzadas.
    
    Secciones detectadas:
    1. Contrato de Trabajo
    2. Constancia de Alta (SUNAT)
    3. Guía de Peligros
    4. Constancia de Alta DerechoHabiente
    5. Constancia de recepción de la Política de Comportamiento
    6. Constancia de política de reembolso de viajes
    7. Código de Conducta
    8. Constancia de RIT,RISST,HOST.SEXUAL,P.SALARIAL
    9. RIT 2025
    10. RISST 2025
    11. RISST CHINALCO 2025 (condicional)
    12. Contrato Auditoría
    """
    
    # Patrones de detección para cada sección
    PATRONES = {
        "contrato": [
            "CONTRATO DE TRABAJO"
        ],
        
        "alta_sunat": {
            # NIVEL 1: Patrones de página inicial (más confiables)
            "inicio_primario": [
                "Formulario 1604",
                "Comprobante de Información Registrada",
                "se realizó satisfactoriamente la modificacion del registro del trabajador",
                "CONSTANCIA DE MODIFICACIÓN O ACTUALIZACIÓN DE DATOS"
            ],
            
            # NIVEL 2: Patrones de página secundaria (T-Registro)
            "inicio_secundario": [
                "T-Registro: Registro de Prestadores",
                "T-REGISTRO",
                "T - Registro",
                "T-REGISTRO: REGISTRO DE PRESTADORES"
            ],
            
            # Patrones de fin
            "fin": [
                "¿Aplica convenio para evitar doble imposición?",
                "Aplica convenio para evitar doble imposición",
                "convenio para evitar doble imposición"
            ]
        },
        
        "guia_peligros": {
            # Patrones de título
            "titulo": [
                "Guía de tipos de peligros y riesgos asociados",
                "GuÃ­a de tipos de peligros"
            ],
            
            # Patrones de validación (debe tener al menos 2)
            "validacion": [
                "PELIGROS",
                "RIESGOS",
                "EVENTO O EXPOSICIÓN PELIGROSA",
                "DAÑO O DETERIORO DE LA SALUD",
                "Peligros Mecánicos",
                "Peligros Eléctricos",
                "Peligros Químicos"
            ],
            
            # Patrones de continuación (para páginas siguientes)
            "continuacion": [
                "PELIGROS",
                "RIESGOS",
                "DAÑO O DETERIORO",
                "Page",  # Footer común en documentos multipágina
                "Peligros",
                "Riesgos"
            ]
        },
        
        "politica_comportamiento": [
            # Patrones específicos de la constancia firmada
            "CONSTANCIA DE RECEPCIÓN DE LA POLÍTICA DE COMPORTAMIENTO",
            "CONSTANCIA DE RECEPCION DE LA POLITICA DE COMPORTAMIENTO",
            "El que suscribe el presente documento, trabajador de METSO",
            "ha recibido un ejemplar de la Política de comportamiento"
        ],
        
        "politica_reembolso": {
            # Patrones del título del documento
            "titulo": [
                "Política de gestión de viajes y reembolso",
                "PolÃ­tica de gestiÃ³n de viajes",
                "política de reembolso"
            ],
            
            # Patrones de constancia firmada
            "constancia": [
                "constancia",
                "he recibido",
                "firmo",
                "firma"
            ]
        },
        
        "codigo_conducta": {
            # Patrones de constancia firmada (NO del documento)
            "constancia": [
                "CONSTANCIA DE ENTREGA",
                "CÓDIGO DE CONDUCTA"
            ],
            
            # Patrones de validación
            "validacion": [
                "dejo constancia que he recibido",
                "firmo la presente",
                "certifico que tengo pleno conocimiento"
            ]
        },
        
        "rit_2025": [
            "CONSTANCIA DE RECEPCIÓN DEL REGLAMENTO INTERNO DE TRABAJO",
            "CONSTANCIA DE RECEPCION DEL REGLAMENTO INTERNO DE TRABAJO",
            "conste por el presente documento que yo",
            "reglamento interno de trabajo"
        ],
        
        "risst_2025": [
            "Reglamento Interno de Seguridad",
            "Reglamento Interno De Seguridad Y Salud En El Trabajo",
            "CERTIFICACIÓN Y COMPROMISO",
            "Certificado de Recepción y Compromiso",
            "RISST",
            "RISTT",
            "habiendo recibido una copia del presente",
            "declaro haber tomado pleno conocimiento del contenido"
        ],
        
        "risst_chinalco": [
            "CONSTANCIA",
            "Reglamento Interno de Seguridad y Salud Ocupacional",
            "Ha recibido un ejemplar del",
            "además se compromete a cumplir",
            "MCP"
        ],
        
        "auditoria": [
            "INFORME DE AUDITORÍA FINAL",
            "INFORME DE AUDITORIA FINAL",
            "Auditoría Final",
            "Final Audit Report"
        ]
    }
    
    def __init__(self, ruta_pdf):
        """
        Inicializa el detector con un PDF.
        
        Args:
            ruta_pdf (str): Ruta completa al archivo PDF
        """
        self.ruta_pdf = ruta_pdf
        self.texto_paginas = []
        self.total_paginas = 0
        
        # Extraer texto de todas las páginas
        self._extraer_texto()
    
    def _extraer_texto(self):
        """Extrae el texto de todas las páginas del PDF."""
        try:
            with fitz.open(self.ruta_pdf) as pdf:
                self.total_paginas = len(pdf)
                for pagina in pdf:
                    texto = pagina.get_text("text")
                    self.texto_paginas.append(texto)
        except Exception as e:
            raise Exception(f"Error al extraer texto del PDF: {str(e)}")
    
    def detectar_todas_secciones(self):
        """
        Detecta las 12 secciones en el PDF.
        
        Returns:
            dict: {
                'secciones': {
                    'Contrato de Trabajo': {'inicio': 1, 'fin': 15},
                    ...
                },
                'fecha_contrato': str or None,
                'fecha_origen': 'sunat'
            }
        """
        secciones = {}
        
        # 1. Contrato de Trabajo (siempre al inicio)
        inicio_contrato, fin_contrato = self._detectar_contrato()
        secciones['Contrato de Trabajo'] = self._format_rango(inicio_contrato, fin_contrato)
        
        # 2. Constancia de Alta (SUNAT)
        inicio_alta, fin_alta = self._detectar_alta_sunat()
        secciones['Constancia de Alta'] = self._format_rango(inicio_alta, fin_alta)
        
        # Extraer fecha SOLO de SUNAT
        fecha_contrato = self._extraer_fecha_sunat(inicio_alta, fin_alta)
        
        # 3. Guía de Peligros (ahora recibe fin_alta para buscar desde ahí)
        inicio_guia, fin_guia = self._detectar_guia_peligros(fin_alta)
        secciones['Guia de Peligro'] = self._format_rango(inicio_guia, fin_guia)
        
        # 4. Constancia de Alta DerechoHabiente (con estrategia híbrida mejorada)
        inicio_dh, fin_dh = self._detectar_alta_derechohabiente(fin_alta, inicio_guia)
        secciones['Constancia de Alta DerechoHabiente'] = self._format_rango(inicio_dh, fin_dh)
        
        # 5. Constancia de recepción de la Política de Comportamiento
        inicio_pc, fin_pc = self._detectar_politica_comportamiento()
        secciones['Constancia de recepción de la Politica de Comportamiento'] = self._format_rango(inicio_pc, fin_pc)
        
        # 6. Constancia de política de reembolso de viajes
        inicio_pr, fin_pr = self._detectar_politica_reembolso()
        secciones['Constancia de politica de reembolso de viajes'] = self._format_rango(inicio_pr, fin_pr)
        
        # 7. Código de Conducta
        inicio_cc, fin_cc = self._detectar_codigo_conducta()
        secciones['Codigo de conducta'] = self._format_rango(inicio_cc, fin_cc)
        
        # 8. Constancia de RIT,RISST,HOST.SEXUAL,P.SALARIAL
        inicio_constancia, fin_constancia = self._detectar_constancia_rit_risst(inicio_pr, inicio_cc)
        secciones['Constancia de RIT,RISST,HOST.SEXUAL,P.SALARIAL'] = self._format_rango(inicio_constancia, fin_constancia)
        
        # 9. RIT 2025
        inicio_rit, fin_rit = self._detectar_rit_2025()
        secciones['RIT 2025'] = self._format_rango(inicio_rit, fin_rit)
        
        # 10. RISST 2025
        inicio_risst, fin_risst = self._detectar_risst_2025()
        secciones['RISST 2025'] = self._format_rango(inicio_risst, fin_risst)
        
        # 12. Contrato Auditoría
        inicio_auditoria, fin_auditoria = self._detectar_auditoria()
        secciones['Contrato Auditoria'] = self._format_rango(inicio_auditoria, fin_auditoria)
        
        # 11. RISST CHINALCO 2025 (condicional)
        inicio_chinalco, fin_chinalco = self._detectar_risst_chinalco(inicio_auditoria)
        secciones['RISST CHINALCO 2025'] = self._format_rango(inicio_chinalco, fin_chinalco)
        
        return {
            'secciones': secciones,
            'fecha_contrato': fecha_contrato,
            'fecha_origen': 'sunat'
        }
    
    def _format_rango(self, inicio, fin):
        """
        Formatea un rango de páginas a base-1 para el JSON.
        
        Args:
            inicio (int or None): Índice de inicio (base-0)
            fin (int or None): Índice de fin (base-0)
        
        Returns:
            dict or None: {'inicio': int, 'fin': int} en base-1, o None si ambos son None
        """
        if inicio is None and fin is None:
            return None
        
        return {
            'inicio': inicio + 1 if inicio is not None else None,
            'fin': fin + 1 if fin is not None else None
        }
    
    def _detectar_contrato(self):
        """
        Detecta el Contrato de Trabajo.
        Asume que siempre está en la página 1.
        Busca el fin usando el patrón "CONSTANCIA DE ALTA".
        
        Returns:
            tuple: (inicio, fin) en base-0
        """
        inicio = 0
        
        # Buscar fin del contrato (donde aparece Alta SUNAT)
        for i, texto in enumerate(self.texto_paginas):
            texto_lower = texto.lower()
            
            if "constancia de alta" in texto_lower or "formulario 1604" in texto_lower:
                return inicio, i - 1 if i > 0 else inicio
        
        # Si no se encuentra fin, asumir página 0
        return inicio, inicio
    
    def _detectar_alta_sunat(self):
        """
        Detecta Constancia de Alta (SUNAT) usando detección multinivel.
        
        Estrategia:
        1. NIVEL 1 (PRIMARIO): Buscar patrones de "Formulario 1604", etc.
        2. NIVEL 2 (SECUNDARIO): Si no se encuentra, buscar "T-Registro"
        
        Fin: Se determina buscando el patrón "convenio para evitar doble imposición"
        
        Returns:
            tuple: (inicio, fin) en base-0
        """
        inicio = None
        fin = None
        
        # NIVEL 1: Buscar patrones primarios
        for i, texto in enumerate(self.texto_paginas):
            if any(patron.lower() in texto.lower() for patron in self.PATRONES["alta_sunat"]["inicio_primario"]):
                inicio = i
                break
        
        # NIVEL 2: Si no se encontró en nivel 1, buscar patrones secundarios
        if inicio is None:
            for i, texto in enumerate(self.texto_paginas):
                if any(patron.lower() in texto.lower() for patron in self.PATRONES["alta_sunat"]["inicio_secundario"]):
                    inicio = i
                    break
        
        # Buscar fin
        if inicio is not None:
            for i in range(inicio, self.total_paginas):
                texto = self.texto_paginas[i]
                if any(patron.lower() in texto.lower() for patron in self.PATRONES["alta_sunat"]["fin"]):
                    fin = i
                    break
            
            # Si no se encuentra fin, usar inicio como fin
            if fin is None:
                fin = inicio
        
        return inicio, fin
    
    def _detectar_guia_peligros(self, fin_sunat=None):
        """
        Detecta Guía de Peligros usando patrones de título y validación.
        Busca desde fin_sunat en adelante para evitar detectar referencias en el contrato.
        Requiere al menos 2 patrones de validación para confirmar que es tabla real.
        Extiende búsqueda a páginas consecutivas que contengan patrones de continuación.
        
        Args:
            fin_sunat (int or None): Índice de fin de SUNAT para iniciar búsqueda después
        
        Returns:
            tuple: (inicio, fin) en base-0
        """
        # Definir inicio de búsqueda (después de SUNAT si existe)
        inicio_busqueda = fin_sunat + 1 if fin_sunat is not None else 0
        inicio = None
        
        # Buscar página de inicio
        for i in range(inicio_busqueda, self.total_paginas):
            texto = self.texto_paginas[i]
            
            # Verificar si contiene el título
            tiene_titulo = any(patron.lower() in texto.lower() for patron in self.PATRONES["guia_peligros"]["titulo"])
            
            if tiene_titulo:
                # VALIDAR QUE SEA DOCUMENTO REAL (no referencia)
                # Contar patrones de validación (tabla de peligros/riesgos)
                coincidencias = sum(1 for patron in self.PATRONES["guia_peligros"]["validacion"] if patron in texto)
                
                # Si tiene al menos 2 validaciones, es tabla real (no referencia)
                if coincidencias >= 2:
                    inicio = i
                    break
        
        if inicio is None:
            return None, None
        
        # Extender búsqueda hacia adelante para páginas de continuación
        fin = inicio
        
        for i in range(inicio + 1, self.total_paginas):
            texto = self.texto_paginas[i]
            
            # Contar patrones de continuación
            coincidencias_continuacion = sum(1 for patron in self.PATRONES["guia_peligros"]["continuacion"] if patron in texto)
            
            # Si tiene al menos 3 patrones de continuación, es parte del documento
            if coincidencias_continuacion >= 3:
                fin = i
            else:
                # Si no cumple, terminamos la búsqueda
                break
        
        return inicio, fin
    
    def _detectar_alta_derechohabiente(self, fin_alta_sunat, inicio_guia_peligros):
        """
        Detecta Constancia de Alta DerechoHabiente usando estrategia híbrida mejorada.
        
        Estrategia (orden de prioridad):
        1. PRIORIDAD 1: Calcular rango desde fin_sunat + 1 hasta siguiente sección conocida
        2. Validar que todas las páginas en ese rango sean "vacías"
        3. PRIORIDAD 2: Si existe Guía de Peligros, usar página anterior (fallback)
        4. PRIORIDAD 3: Página después de SUNAT si es vacía (último recurso)
        
        Args:
            fin_alta_sunat (int or None): Índice de fin de Alta SUNAT
            inicio_guia_peligros (int or None): Índice de inicio de Guía de Peligros
        
        Returns:
            tuple: (inicio, fin) en base-0
        """
        # PRIORIDAD 1: Estrategia híbrida (rango calculado + validación)
        if fin_alta_sunat is not None:
            # Buscar la siguiente sección conocida después de SUNAT
            siguiente_seccion = self._encontrar_siguiente_seccion(fin_alta_sunat + 1)
            
            if siguiente_seccion is not None:
                inicio_candidato = fin_alta_sunat + 1
                fin_candidato = siguiente_seccion - 1
                
                # Validar que el rango sea lógico
                if inicio_candidato <= fin_candidato and inicio_candidato < self.total_paginas:
                    # Validar que todas las páginas en el rango sean "vacías"
                    todas_vacias = all(
                        self._es_pagina_vacia_o_firma(pag) 
                        for pag in range(inicio_candidato, fin_candidato + 1)
                    )
                    
                    # Si todas las páginas son válidas, retornar el rango completo
                    if todas_vacias:
                        return inicio_candidato, fin_candidato
        
        # PRIORIDAD 2: Heurística con Guía de Peligros (fallback)
        if inicio_guia_peligros is not None and inicio_guia_peligros > 0:
            candidato = inicio_guia_peligros - 1
            # Validar que la página sea vacía antes de retornarla
            if self._es_pagina_vacia_o_firma(candidato):
                return candidato, candidato
        
        # PRIORIDAD 3: Después de SUNAT (último recurso)
        if fin_alta_sunat is not None and fin_alta_sunat < self.total_paginas - 1:
            candidato = fin_alta_sunat + 1
            if self._es_pagina_vacia_o_firma(candidato):
                return candidato, candidato
        
        return None, None
    
    def _encontrar_siguiente_seccion(self, desde_pagina):
        """
        Encuentra la primera sección conocida después de una página dada.
        Busca patrones de títulos de secciones documentales.
        
        Args:
            desde_pagina (int): Página desde donde iniciar búsqueda (base-0)
        
        Returns:
            int or None: Índice de la siguiente sección, o None si no se encuentra
        """
        for i in range(desde_pagina, self.total_paginas):
            texto = self.texto_paginas[i]
            texto_upper = texto.upper()
            
            # Patrones de secciones conocidas (títulos de documentos)
            patrones_secciones = [
                "GUÍA DE TIPOS DE PELIGROS",
                "GUIA DE TIPOS DE PELIGROS",
                "POLÍTICA DE GESTIÓN",
                "POLITICA DE GESTION",
                "POLÍTICA DE COMPORTAMIENTO",
                "POLITICA DE COMPORTAMIENTO",
                "POLICY",
                "CONSTANCIA DE RECEPCIÓN",
                "CONSTANCIA DE RECEPCION",
                "CONSTANCIA DE ENTREGA",
                "CÓDIGO DE CONDUCTA",
                "CODIGO DE CONDUCTA",
                "REGLAMENTO INTERNO",
                "CERTIFICACIÓN Y COMPROMISO"
            ]
            
            # Verificar si la página contiene algún patrón de sección
            if any(patron in texto_upper for patron in patrones_secciones):
                # Validar que no sea una página vacía con solo mención
                if len(texto.strip()) > 200:  # Páginas de sección tienen contenido
                    return i
        
        return None
    
    def _es_pagina_vacia_o_firma(self, indice_pagina):
        """
        Determina si una página está "vacía" o contiene solo firma.
        
        Criterios:
        - Longitud de texto < 150 caracteres
        - O solo contiene firma (patrón: nombre + fecha + "EST")
        - No contiene patrones de otras secciones conocidas
        
        Args:
            indice_pagina (int): Índice de la página (base-0)
        
        Returns:
            bool: True si la página está vacía o solo tiene firma
        """
        if indice_pagina >= self.total_paginas:
            return False
        
        texto = self.texto_paginas[indice_pagina]
        texto_limpio = texto.strip()
        
        # Criterio 1: Página muy corta (< 150 caracteres)
        if len(texto_limpio) < 150:
            return True
        
        # Criterio 2: Solo contiene firma (patrón común: nombre + fecha + "EST" o "CDT")
        # Ejemplo: "Carlos Igor rojo Díaz (1 dic.. 2025 12:57:38 EST)"
        patron_firma = r'\([0-9]{1,2}\s+\w+\.\.\s+[0-9]{4}\s+[0-9]{2}:[0-9]{2}:[0-9]{2}\s+(EST|CDT)\)'
        if re.search(patron_firma, texto):
            # Eliminar la firma y ver si queda algo relevante
            texto_sin_firma = re.sub(patron_firma, '', texto)
            # Eliminar nombres (pueden tener varios espacios)
            texto_sin_firma = re.sub(r'[A-Z][a-z]+(\s+[A-Z][a-z]+)*', '', texto_sin_firma)
            texto_sin_firma = texto_sin_firma.strip()
            
            # Si después de quitar firma y nombre queda poco texto, es página vacía
            if len(texto_sin_firma) < 50:
                return True
        
        # Criterio 3: No debe contener patrones de otras secciones importantes
        patrones_excluidos = [
            "CONSTANCIA",
            "POLÍTICA",
            "POLITICA",
            "REGLAMENTO",
            "CÓDIGO",
            "CODIGO",
            "PELIGROS",
            "FORMULARIO",
            "GUÍA",
            "GUIA",
            "Document Title",
            "Position of document",
            "Policy"
        ]
        
        texto_upper = texto.upper()
        for patron in patrones_excluidos:
            if patron in texto_upper:
                return False
        
        # Si no cumple ningún criterio específico, no es página vacía
        return False
    
    def _detectar_politica_comportamiento(self):
        """
        Detecta Constancia de Política de Comportamiento.
        
        Returns:
            tuple: (inicio, fin) en base-0
        """
        for i, texto in enumerate(self.texto_paginas):
            texto_lower = texto.lower()
            
            if any(patron.lower() in texto_lower for patron in self.PATRONES["politica_comportamiento"]):
                return i, i
        
        return None, None
    
    def _detectar_politica_reembolso(self):
        """
        Detecta Constancia de Política de Reembolso.
        
        Estrategia:
        1. Encontrar todas las páginas que mencionan "Política de reembolso"
        2. Buscar desde la ÚLTIMA página hacia atrás
        3. Retornar la que contenga patrones de constancia ("constancia", "firma", etc.)
        
        Returns:
            tuple: (inicio, fin) en base-0
        """
        paginas_con_politica = []
        
        # Buscar todas las páginas que mencionan la política
        for i, texto in enumerate(self.texto_paginas):
            texto_lower = texto.lower()
            if any(patron.lower() in texto_lower for patron in self.PATRONES["politica_reembolso"]["titulo"]):
                paginas_con_politica.append(i)
        
        if not paginas_con_politica:
            return None, None
        
        # Buscar desde la última página hacia atrás
        for pag in reversed(paginas_con_politica):
            texto_lower = self.texto_paginas[pag].lower()
            
            # Verificar si tiene patrones de constancia
            if any(patron in texto_lower for patron in self.PATRONES["politica_reembolso"]["constancia"]):
                return pag, pag
        
        # Si ninguna tiene patrones de constancia, retornar la primera encontrada
        return paginas_con_politica[0], paginas_con_politica[0]
    
    def _detectar_codigo_conducta(self):
        """
        Detecta Constancia de Código de Conducta (NO el documento completo).
        
        Estrategia:
        1. Buscar páginas que contengan AMBOS: "CONSTANCIA DE ENTREGA" + "CÓDIGO DE CONDUCTA"
        2. Validar que contenga patrones de constancia firmada
        
        Returns:
            tuple: (inicio, fin) en base-0
        """
        for i, texto in enumerate(self.texto_paginas):
            texto_upper = texto.upper()
            texto_lower = texto.lower()
            
            # Verificar que contenga AMBOS patrones de constancia
            tiene_constancia_entrega = "CONSTANCIA DE ENTREGA" in texto_upper
            tiene_codigo_conducta = "CÓDIGO DE CONDUCTA" in texto_upper or "CODIGO DE CONDUCTA" in texto_upper
            
            if tiene_constancia_entrega and tiene_codigo_conducta:
                # Validar que sea realmente una constancia firmada
                if any(patron in texto_lower for patron in self.PATRONES["codigo_conducta"]["validacion"]):
                    return i, i
        
        return None, None
    
    def _detectar_constancia_rit_risst(self, inicio_politica_reembolso, inicio_codigo_conducta):
        """
        Detecta Constancia de RIT,RISST,HOST.SEXUAL,P.SALARIAL usando heurística con validación.
        
        Estrategia:
        1. Intentar heurística primaria: politica_reembolso + 1
        2. Validar contenido (requiere ≥3 patrones)
        3. Si falla, usar heurística secundaria: codigo_conducta + 1
        4. Validar contenido
        5. Si ambas fallan, retornar None
        
        Args:
            inicio_politica_reembolso (int or None): Índice de inicio de Política de Reembolso
            inicio_codigo_conducta (int or None): Índice de inicio de Código de Conducta
        
        Returns:
            tuple: (inicio, fin) en base-0
        """
        # Patrones de validación de la Constancia RIT,RISST
        patrones_validacion = [
            "reglamento interno de seguridad y salud en el trabajo",
            "risst",
            "reglamento interno de trabajo",
            "rit",
            "procedimiento de investigación y sanción del hostigamiento sexual",
            "procedimiento de investigacion y sancion del hostigamiento sexual",
            "dejo constancia que he recibido lo siguiente"
        ]
        
        # HEURÍSTICA PRIMARIA: politica_reembolso + 1
        if inicio_politica_reembolso is not None:
            candidato_primario = inicio_politica_reembolso + 1
            
            # Validar que el candidato esté dentro del rango
            if candidato_primario < self.total_paginas:
                texto_candidato = self.texto_paginas[candidato_primario].lower()
                
                # Contar coincidencias
                coincidencias = sum(1 for patron in patrones_validacion if patron in texto_candidato)
                
                # Si tiene al menos 3 coincidencias, es válido
                if coincidencias >= 3:
                    return candidato_primario, candidato_primario
        
        # HEURÍSTICA SECUNDARIA: codigo_conducta + 1
        if inicio_codigo_conducta is not None:
            candidato_secundario = inicio_codigo_conducta + 1
            
            # Validar que el candidato esté dentro del rango
            if candidato_secundario < self.total_paginas:
                texto_candidato = self.texto_paginas[candidato_secundario].lower()
                
                # Contar coincidencias
                coincidencias = sum(1 for patron in patrones_validacion if patron in texto_candidato)
                
                # Si tiene al menos 3 coincidencias, es válido
                if coincidencias >= 3:
                    return candidato_secundario, candidato_secundario
        
        # Si ninguna heurística funcionó, retornar None
        return None, None
    
    def _detectar_rit_2025(self):
        """
        Detecta RIT 2025 buscando patrones específicos.
        
        Returns:
            tuple: (inicio, fin) en base-0
        """
        paginas_candidatas = []
        
        for i, texto in enumerate(self.texto_paginas):
            texto_normalizado = re.sub(r'\s+', ' ', texto)
            texto_lower = texto_normalizado.lower()
            
            if "conste por el presente documento que yo" in texto_lower and "reglamento interno de trabajo" in texto_lower:
                paginas_candidatas.append(i)
        
        if paginas_candidatas:
            return paginas_candidatas[0], paginas_candidatas[0]
        
        return None, None
    
    def _detectar_risst_2025(self):
        """
        Detecta RISST 2025 con validación multi-patrón.
        Requiere al menos 2 coincidencias para confirmar.
        Prioriza la página con más coincidencias para evitar falsos positivos.
        
        Returns:
            tuple: (inicio, fin) en base-0
        """
        paginas_risst = []
        
        for i, texto in enumerate(self.texto_paginas):
            # Contar cuántos patrones coinciden en esta página
            coincidencias = self._contar_coincidencias(texto, self.PATRONES["risst_2025"])
            
            # Si hay al menos 2 patrones coincidiendo, es candidata
            if coincidencias >= 2:
                paginas_risst.append((i, coincidencias))
        
        if paginas_risst:
            # Ordenar por número de coincidencias (descendente) y tomar la primera
            paginas_risst.sort(key=lambda x: x[1], reverse=True)
            return paginas_risst[0][0], paginas_risst[0][0]
        
        return None, None
    
    def _detectar_risst_chinalco(self, inicio_auditoria):
        """
        Detecta RISST CHINALCO 2025 (SOLO si existe Auditoría).
        Busca en la página inmediatamente anterior a Auditoría.
        Requiere al menos 2 coincidencias para confirmar.
        
        Args:
            inicio_auditoria (int or None): Índice de inicio de Auditoría
        
        Returns:
            tuple: (inicio, fin) en base-0
        """
        if inicio_auditoria is None or inicio_auditoria <= 0:
            return None, None
        
        # Página candidata: inmediatamente anterior a Auditoría
        pagina_candidata = inicio_auditoria - 1
        texto_candidato = self.texto_paginas[pagina_candidata]
        
        # Contar coincidencias
        coincidencias = self._contar_coincidencias(texto_candidato, self.PATRONES["risst_chinalco"])
        
        # Si hay al menos 2 patrones, confirmamos
        if coincidencias >= 2:
            return pagina_candidata, pagina_candidata
        
        return None, None
    
    def _detectar_auditoria(self):
        """
        Detecta Contrato Auditoría (puede ser múltiples páginas).
        
        Returns:
            tuple: (inicio, fin) en base-0
        """
        paginas_auditoria = []
        
        for i, texto in enumerate(self.texto_paginas):
            texto_lower = texto.lower()
            
            if any(patron.lower() in texto_lower for patron in self.PATRONES["auditoria"]):
                paginas_auditoria.append(i)
        
        if paginas_auditoria:
            return paginas_auditoria[0], paginas_auditoria[-1]
        
        return None, None
    
    def _contar_coincidencias(self, texto, patrones):
        """
        Cuenta cuántos patrones coinciden en un texto.
        
        Args:
            texto (str): Texto donde buscar
            patrones (list): Lista de patrones a buscar
        
        Returns:
            int: Número de patrones encontrados
        """
        return sum(1 for patron in patrones if re.search(patron, texto, re.IGNORECASE))
    
    def _extraer_fecha_sunat(self, inicio_sunat, fin_sunat):
        """
        Extrae la fecha de alta de la sección SUNAT.
        Busca el patrón: "Periodos laborales:...Fecha de inicio...DD/MM/YYYY"
        Retorna: "MM.YYYY"
        
        Args:
            inicio_sunat (int or None): Índice de inicio de sección SUNAT
            fin_sunat (int or None): Índice de fin de sección SUNAT
        
        Returns:
            str or None: Fecha en formato MM.YYYY
        """
        if inicio_sunat is None:
            return None
        
        try:
            # Determinar rango de páginas a leer
            fin = fin_sunat if fin_sunat is not None else inicio_sunat
            fin = min(fin + 1, inicio_sunat + 3)  # Leer máximo 3 páginas desde inicio
            
            # Leer texto de las páginas de SUNAT
            texto_sunat = ""
            for num_pag in range(inicio_sunat, min(fin, self.total_paginas)):
                texto_sunat += self.texto_paginas[num_pag]
            
            # PATRÓN PRIMARIO: Periodos laborales con tabla completa
            patron_principal = r'Periodos laborales:.*?Fecha de inicio\s+Fecha de fin\s+Motivo de baja\s+(\d{2}/\d{2}/\d{4})'
            match = re.search(patron_principal, texto_sunat, re.DOTALL)
            
            if match:
                fecha_str = match.group(1)  # Formato: DD/MM/YYYY
                return self._convertir_fecha_a_formato(fecha_str)
            
            # PATRÓN SECUNDARIO: Buscar directamente "Fecha de inicio:"
            patron_secundario = r'Fecha de inicio[:\s]+(\d{2}/\d{2}/\d{4})'
            match_secundario = re.search(patron_secundario, texto_sunat)
            
            if match_secundario:
                fecha_str = match_secundario.group(1)
                return self._convertir_fecha_a_formato(fecha_str)
            
            # PATRÓN TERCIARIO: Buscar cualquier fecha en formato DD/MM/YYYY después de "Periodos laborales"
            patron_terciario = r'Periodos laborales:.*?(\d{2}/\d{2}/\d{4})'
            match_terciario = re.search(patron_terciario, texto_sunat, re.DOTALL)
            
            if match_terciario:
                fecha_str = match_terciario.group(1)
                return self._convertir_fecha_a_formato(fecha_str)
            
            return None
            
        except Exception as e:
            print(f"⚠️ Error extrayendo fecha de SUNAT: {str(e)}")
            return None
    
    def _convertir_fecha_a_formato(self, fecha_str):
        """
        Convierte fecha de formato DD/MM/YYYY a MM.YYYY.
        Valida que la fecha sea correcta.
        
        Args:
            fecha_str (str): Fecha en formato DD/MM/YYYY
        
        Returns:
            str or None: Fecha en formato MM.YYYY o None si es inválida
        """
        try:
            partes = fecha_str.split('/')
            if len(partes) != 3:
                return None
            
            dia, mes, anio = partes
            
            # Validar que sean números
            if not (dia.isdigit() and mes.isdigit() and anio.isdigit()):
                return None
            
            # Validar rango de fecha
            dia_int = int(dia)
            mes_int = int(mes)
            anio_int = int(anio)
            
            # Crear objeto datetime para validar
            fecha_obj = datetime(anio_int, mes_int, dia_int)
            
            # Retornar formato MM.YYYY
            return f"{mes.zfill(2)}.{anio}"
            
        except ValueError:
            # Fecha inválida
            return None