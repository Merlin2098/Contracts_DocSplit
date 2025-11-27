"""
Detector de secciones para contratos iniciales.
Ubicación: core/contratos/section_detector.py

Detecta 12 secciones usando:
- Patrones de texto múltiples
- Heurísticas basadas en página ancla (RIT)
- Validación multi-patrón (RISST requiere ≥2 coincidencias)
- Detección condicional (RISST Chinalco solo si existe Auditoría)
- Detección multinivel para Alta SUNAT (Nivel 1: Formulario 1604, Nivel 2: T-Registro)
"""

import os
import re
import fitz  # PyMuPDF


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
            ]
        },
        
        "politica_comportamiento": [
            # Patrones específicos de la constancia firmada
            "CONSTANCIA DE RECEPCIÓN DE LA POLÍTICA DE COMPORTAMIENTO",
            "CONSTANCIA DE RECEPCION DE LA POLITICA DE COMPORTAMIENTO",
            "El que suscribe el presente documento, trabajador de METSO",
            "ha recibido un ejemplar de la Política de comportamiento"
        ],
        
        "politica_reembolso": [
            "Política de gestión de viajes y reembolso",
            "PolÃ­tica de gestiÃ³n de viajes",
            "política de reembolso"
        ],
        
        "codigo_conducta": [
            "CÓDIGO DE CONDUCTA",
            "CODIGO DE CONDUCTA",
            "constancia de entrega",
            "código de conducta"
        ],
        
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
            "Auditoría Final"
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
                'fecha_contrato': str or None
            }
        """
        secciones = {}
        
        # 1. Contrato de Trabajo (siempre al inicio)
        inicio_contrato, fin_contrato = self._detectar_contrato()
        secciones['Contrato de Trabajo'] = self._format_rango(inicio_contrato, fin_contrato)
        
        # Extraer fecha del contrato
        fecha_contrato = self._extraer_fecha_contrato(fin_contrato)
        
        # 2. Constancia de Alta (SUNAT)
        inicio_alta, fin_alta = self._detectar_alta_sunat()
        secciones['Constancia de Alta'] = self._format_rango(inicio_alta, fin_alta)
        
        # 3. Guía de Peligros
        inicio_guia, fin_guia = self._detectar_guia_peligros()
        secciones['Guia de Peligro'] = self._format_rango(inicio_guia, fin_guia)
        
        # 4. Constancia de Alta DerechoHabiente
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
        secciones['Codigo de Conducta'] = self._format_rango(inicio_cc, fin_cc)
        
        # 8. Constancia de RIT,RISST,HOST.SEXUAL,P.SALARIAL
        inicio_const, fin_const = self._detectar_constancia_rit_risst(inicio_pr, inicio_cc)
        secciones['Constancia de RIT,RISST,HOST.SEXUAL,P.SALARIAL'] = self._format_rango(inicio_const, fin_const)
        
        # 9. RIT 2025
        inicio_rit, fin_rit = self._detectar_rit_2025()
        secciones['RIT 2025'] = self._format_rango(inicio_rit, fin_rit)
        
        # 10. RISST 2025
        inicio_risst, fin_risst = self._detectar_risst_2025()
        secciones['RISST 2025'] = self._format_rango(inicio_risst, fin_risst)
        
        # 12. Contrato Auditoría (detectar antes de RISST Chinalco)
        inicio_aud, fin_aud = self._detectar_auditoria()
        secciones['Contrato Auditoria'] = self._format_rango(inicio_aud, fin_aud)
        
        # 11. RISST CHINALCO 2025 (condicional: solo si existe Auditoría)
        inicio_chinalco, fin_chinalco = self._detectar_risst_chinalco(inicio_aud)
        secciones['RISST CHINALCO 2025'] = self._format_rango(inicio_chinalco, fin_chinalco)
        
        return {
            'secciones': secciones,
            'fecha_contrato': fecha_contrato
        }
    
    def _format_rango(self, inicio, fin):
        """
        Formatea un rango de páginas para el JSON.
        Convierte índices base-0 a base-1.
        
        Args:
            inicio (int or None): Índice de inicio (base-0)
            fin (int or None): Índice de fin (base-0)
        
        Returns:
            dict or None: {'inicio': int, 'fin': int} o None
        """
        if inicio is not None and fin is not None:
            return {
                'inicio': inicio + 1,
                'fin': fin + 1
            }
        return None
    

    def _detectar_contrato(self):
        """
        Detecta el Contrato de Trabajo (siempre al inicio del PDF).
        
        Returns:
            tuple: (inicio, fin) en base-0
        """
        inicio = None
        fin = None
        
        # Buscar inicio
        for i, texto in enumerate(self.texto_paginas):
            if any(patron in texto for patron in self.PATRONES["contrato"]):
                inicio = i
                break
        
        if inicio is None:
            return None, None
        
        # Buscar fin: detectar inicio de alta_sunat
        for i in range(inicio + 1, self.total_paginas):
            texto_lower = self.texto_paginas[i].lower()
            
            # Verificar si encontramos patrones de Alta SUNAT (nivel 1 o nivel 2)
            if any(patron.lower() in texto_lower for patron in self.PATRONES["alta_sunat"]["inicio_primario"]):
                fin = i - 1
                break
            if any(patron.lower() in texto_lower for patron in self.PATRONES["alta_sunat"]["inicio_secundario"]):
                fin = i - 1
                break
        
        # Si no encontramos fin, asumir que termina antes de la última página
        if fin is None:
            fin = self.total_paginas - 1
        
        return inicio, fin
    
    def _detectar_alta_sunat(self):
        """
        Detecta Constancia de Alta (SUNAT) con sistema multi-nivel.
        
        Estrategia:
        - NIVEL 1: Busca patrones de página inicial (Formulario 1604)
        - NIVEL 2: Busca patrones de página secundaria (T-Registro)
        - Si solo encuentra Nivel 2, verifica página anterior
        
        Returns:
            tuple: (inicio, fin) en base-0
        """
        inicio_alta = None
        fin_alta = None
        
        # ============================================================
        # NIVEL 1: Buscar patrones de página inicial
        # ============================================================
        for i, texto in enumerate(self.texto_paginas):
            texto_lower = texto.lower()
            
            # Patrones únicos de la primera página de Alta SUNAT
            if any(patron.lower() in texto_lower for patron in self.PATRONES["alta_sunat"]["inicio_primario"]):
                inicio_alta = i
                
                # Buscar fin desde esta página
                for j in range(i, self.total_paginas):
                    texto_fin = self.texto_paginas[j].lower()
                    if any(patron.lower() in texto_fin for patron in self.PATRONES["alta_sunat"]["fin"]):
                        fin_alta = j
                        break
                
                # Si encontramos inicio en nivel 1, terminamos
                if fin_alta is None:
                    fin_alta = i
                return inicio_alta, fin_alta
        
        # ============================================================
        # NIVEL 2: Buscar patrones de página secundaria (T-Registro)
        # ============================================================
        for i, texto in enumerate(self.texto_paginas):
            texto_lower = texto.lower()
            
            if any(patron.lower() in texto_lower for patron in self.PATRONES["alta_sunat"]["inicio_secundario"]):
                # Verificar si la página anterior tiene contenido relacionado
                if i > 0:
                    texto_anterior = self.texto_paginas[i - 1].lower()
                    
                    # Si la página anterior tiene patrones relacionados, iniciar desde ahí
                    if any(patron.lower() in texto_anterior for patron in self.PATRONES["alta_sunat"]["inicio_primario"]):
                        inicio_alta = i - 1
                    else:
                        inicio_alta = i
                else:
                    inicio_alta = i
                
                # Buscar fin
                for j in range(inicio_alta, self.total_paginas):
                    texto_fin = self.texto_paginas[j].lower()
                    if any(patron.lower() in texto_fin for patron in self.PATRONES["alta_sunat"]["fin"]):
                        fin_alta = j
                        break
                
                if fin_alta is None:
                    fin_alta = inicio_alta
                
                return inicio_alta, fin_alta
        
        # No se encontró Alta SUNAT
        return None, None
    
    def _detectar_guia_peligros(self):
        """
        Detecta Guía de Peligros.
        Requiere validación para la primera página, luego continúa con páginas siguientes.
        
        Estrategia:
        1. Detecta primera página con validación estricta (evita falsas referencias)
        2. Continúa detectando páginas siguientes con el patrón del título
        
        Returns:
            tuple: (inicio, fin) en base-0
        """
        primera_pagina = None
        
        # PASO 1: Detectar primera página con validación estricta
        for i, texto in enumerate(self.texto_paginas):
            texto_upper = texto.upper()
            
            # Buscar patrón de título
            if "GUÍA DE TIPOS DE PELIGROS" in texto_upper or \
               "GUIA DE TIPOS DE PELIGROS" in texto_upper:
                
                # VALIDACIÓN: Verificar que sea el documento real, no solo una mención
                validaciones_encontradas = 0
                
                # Verificar columnas de la tabla
                if "PELIGROS" in texto_upper and "RIESGOS" in texto_upper:
                    validaciones_encontradas += 1
                
                if "EVENTO O EXPOSICIÓN PELIGROSA" in texto_upper or \
                   "EVENTO O EXPOSICION PELIGROSA" in texto_upper:
                    validaciones_encontradas += 1
                
                if "DAÑO O DETERIORO" in texto_upper or \
                   "DANO O DETERIORO" in texto_upper:
                    validaciones_encontradas += 1
                
                # Verificar categorías de peligros
                if "PELIGROS MECÁNICOS" in texto_upper or \
                   "PELIGROS MECANICOS" in texto_upper:
                    validaciones_encontradas += 1
                
                # Verificar numeración de items
                if "1.1" in texto and "1.2" in texto:
                    validaciones_encontradas += 1
                
                # Si tiene al menos 2 validaciones, es el documento real
                if validaciones_encontradas >= 2:
                    primera_pagina = i
                    break
        
        if primera_pagina is None:
            return None, None
        
        # PASO 2: Detectar páginas siguientes usando patrón simple del título
        ultima_pagina = primera_pagina
        
        # Buscar en las páginas siguientes (hasta 5 páginas después)
        for j in range(primera_pagina + 1, min(primera_pagina + 6, self.total_paginas)):
            texto_upper = self.texto_paginas[j].upper()
            
            # Si la página siguiente tiene el título o contenido relacionado, incluirla
            if "GUÍA DE TIPOS DE PELIGROS" in texto_upper or \
               "GUIA DE TIPOS DE PELIGROS" in texto_upper or \
               ("PELIGROS" in texto_upper and "RIESGOS" in texto_upper):
                ultima_pagina = j
            else:
                # Si no encontramos el patrón, terminamos la búsqueda
                break
        
        return primera_pagina, ultima_pagina
    
    def _detectar_alta_derechohabiente(self, fin_alta_sunat, inicio_guia):
        """
        Detecta Constancia de Alta DerechoHabiente con validación de legibilidad.
        
        Estrategia:
        1. Calcula rango potencial entre fin_alta_sunat y inicio_guia
        2. Verifica si la primera página es legible (>100 caracteres)
        3. Si es legible → NO hay DerechoHabiente
        4. Si NO es legible → busca hasta dónde continúa siendo ilegible
        
        Args:
            fin_alta_sunat (int or None): Fin de Alta SUNAT
            inicio_guia (int or None): Inicio de Guía de Peligros
        
        Returns:
            tuple: (inicio, fin) en base-0 o (None, None) si no existe
        """
        if fin_alta_sunat is None or inicio_guia is None:
            return None, None
        
        # Calcular rango potencial
        inicio_rango = fin_alta_sunat + 1
        fin_rango = inicio_guia - 1
        
        if inicio_rango > fin_rango:
            return None, None
        
        # Verificar si la primera página del rango es legible
        primera_pagina_texto = self.texto_paginas[inicio_rango]
        
        # Criterio: página legible = más de 100 caracteres de texto
        if len(primera_pagina_texto.strip()) > 100:
            # Primera página es legible → NO hay DerechoHabiente
            return None, None
        
        # Primera página NO es legible → buscar hasta dónde llega DerechoHabiente
        ultima_pagina_dh = inicio_rango
        
        for i in range(inicio_rango + 1, fin_rango + 1):
            texto = self.texto_paginas[i]
            
            if len(texto.strip()) > 100:
                # Encontramos página legible → termina DerechoHabiente
                break
            else:
                # Página NO legible → continúa DerechoHabiente
                ultima_pagina_dh = i
        
        return inicio_rango, ultima_pagina_dh
    
    def _detectar_politica_comportamiento(self):
        """
        Detecta Constancia de Política de Comportamiento.
        Busca la constancia firmada, no el documento completo.
        
        Returns:
            tuple: (inicio, fin) en base-0
        """
        for i, texto in enumerate(self.texto_paginas):
            texto_lower = texto.lower()
            
            # CRITERIO 1: Debe tener "CONSTANCIA DE RECEPCIÓN"
            if "constancia de recepción de la política de comportamiento" in texto_lower or \
               "constancia de recepcion de la politica de comportamiento" in texto_lower:
                
                # CRITERIO 2: Validar que sea la constancia real (no un header)
                # Debe contener texto de firma o declaración
                if "el que suscribe" in texto_lower or \
                   "apellidos y nombres" in texto_lower or \
                   "documento de identidad" in texto_lower:
                    return i, i
        
        return None, None
    
    def _detectar_politica_reembolso(self):
        """
        Detecta Constancia de política de reembolso (última ocurrencia).
        
        Returns:
            tuple: (inicio, fin) en base-0
        """
        paginas_encontradas = []
        
        for i, texto in enumerate(self.texto_paginas):
            texto_lower = texto.lower()
            
            if any(patron.lower() in texto_lower for patron in self.PATRONES["politica_reembolso"]):
                paginas_encontradas.append(i)
        
        if paginas_encontradas:
            ultima_pagina = paginas_encontradas[-1]
            return ultima_pagina, ultima_pagina
        
        return None, None
    
    def _detectar_codigo_conducta(self):
        """
        Detecta Código de Conducta usando búsqueda por patrón directo.
        
        Returns:
            tuple: (inicio, fin) en base-0
        """
        # Búsqueda por patrón
        for i, texto in enumerate(self.texto_paginas):
            texto_normalizado = re.sub(r'\s+', ' ', texto)
            texto_lower = texto_normalizado.lower()
            
            if "constancia de entrega" in texto_lower and "código de conducta" in texto_lower:
                return i, i
        
        return None, None
    
    def _detectar_constancia_rit_risst(self, inicio_politica_reembolso, inicio_codigo_conducta):
        """
        Detecta Constancia de RIT,RISST,HOST.SEXUAL,P.SALARIAL.
        Usa sistema de validación con doble heurística.
        
        Estrategia:
        1. Heurística primaria: politica_reembolso + 1
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
        
        Returns:
            tuple: (inicio, fin) en base-0
        """
        paginas_risst = []
        
        for i, texto in enumerate(self.texto_paginas):
            # Contar cuántos patrones coinciden en esta página
            coincidencias = self._contar_coincidencias(texto, self.PATRONES["risst_2025"])
            
            # Si hay al menos 2 patrones coincidiendo, es RISST
            if coincidencias >= 2:
                paginas_risst.append(i)
        
        if paginas_risst:
            # Tomar la última página detectada
            return paginas_risst[-1], paginas_risst[-1]
        
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
    
    def _extraer_fecha_contrato(self, fin_contrato):
        """
        Extrae la fecha del contrato desde la última página del bloque Contrato.
        Patrón: "el DD de MES del YYYY"
        Retorna: "MM.YYYY"
        
        Args:
            fin_contrato (int or None): Índice de la última página del contrato
        
        Returns:
            str or None: Fecha en formato MM.YYYY
        """
        if fin_contrato is None or fin_contrato >= self.total_paginas:
            return None
        
        texto_ultima_pagina = self.texto_paginas[fin_contrato]
        
        # Mapeo de meses
        meses = {
            'enero': '01', 'febrero': '02', 'marzo': '03', 'abril': '04',
            'mayo': '05', 'junio': '06', 'julio': '07', 'agosto': '08',
            'septiembre': '09', 'octubre': '10', 'noviembre': '11', 'diciembre': '12'
        }
        
        # Patrón: el DD de MES del YYYY
        patron = r'el\s+\d+\s+de\s+(\w+)\s+del?\s+(\d{4})'
        match = re.search(patron, texto_ultima_pagina, re.IGNORECASE)
        
        if match:
            mes_texto = match.group(1).lower()
            anio = match.group(2)
            mes_num = meses.get(mes_texto)
            
            if mes_num:
                return f"{mes_num}.{anio}"
        
        return None