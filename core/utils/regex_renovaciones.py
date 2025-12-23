"""
Patrones de expresiones regulares para detección de secciones en contratos de renovación.
Módulo de configuración centralizada para facilitar mantenimiento.

Este módulo contiene todos los patrones regex utilizados en el proceso de detección
de secciones en documentos de renovación de contratos. Centralizar estos patrones
permite:
- Mantenimiento más sencillo
- Agregar nuevas variantes sin modificar la lógica core
- Documentación clara de cada patrón
- Testing independiente de regex
"""

import re


# ============================================================================
# PATRONES DE FECHA DE FIRMA
# ============================================================================

class PatronesFecha:
    """
    Patrones regex para extracción de fecha de contratos de renovación.
    
    IMPORTANTE: Se busca la fecha de finalización/inicio del contrato,
    NO la fecha de firma del documento.
    
    - PRÓRROGA: busca "hasta el DD de MES del AAAA" en Cláusula Primera
    - RENOVACIÓN: busca "a partir del DD de MES del AAAA" en Cláusula Sexta
    """
    
    # Patrón para PRÓRROGA: "hasta el 15 de diciembre del 2025" o "hasta el 15 de diciembre de 2025"
    # Formato: "hasta el DD de MES de(l) AAAA" - "del" es opcional
    FECHA_FINALIZACION_PRORROGA = r"hasta\s+el\s+(\d{1,2})\s+de\s+(\w+)\s+de(?:l)?\s+(\d{4})"
    
    # Patrón ESPECÍFICO para antecedentes: "prorrogado sucesivamente hasta el 15 de diciembre de 2025"
    # Se usa en la Cláusula Primera (ANTECEDENTES) para priorizar la extracción correcta
    FECHA_ANTECEDENTES_PRORROGA = r"prorrogado\s+sucesivamente\s+hasta\s+el\s+(\d{1,2})\s+de\s+(\w+)\s+de(?:l)?\s+(\d{4})"
    
    # Patrón para RENOVACIÓN: "a partir del 02 de noviembre del 2025"
    # Formato: "a partir del DD de MES del AAAA"
    # Nota: "de" puede ser "de" o "del" (variante)
    FECHA_INICIO_RENOVACION = r"a\s+partir\s+del\s+(\d{1,2})\s+de[l]?\s+(\w+)\s+del\s+(\d{4})"
    
    # NOTA: Los patrones de fecha de firma del documento NO se usan
    # porque el sistema necesita la fecha de finalización/inicio del contrato
    # NO la fecha en que se firmó el documento
    
    # Lista ordenada de patrones (se prueban en este orden)
    TODOS_LOS_PATRONES = [
        FECHA_ANTECEDENTES_PRORROGA,  # Primero buscar en antecedentes
        FECHA_FINALIZACION_PRORROGA,  # Luego búsqueda general
        FECHA_INICIO_RENOVACION
    ]


# ============================================================================
# PATRONES DE SECCIONES DEL CONTRATO
# ============================================================================

class PatronesSecciones:
    """
    Patrones regex para identificación de secciones principales del contrato.
    """
    
    # Patrón para detectar inicio de contrato de renovación
    INICIO_CONTRATO = r'PRÓRROGA DE CONTRATO'
    
    # Patrón para detectar la cláusula de antecedentes
    CLAUSULA_ANTECEDENTES = r'CLÁUSULA PRIMERA:\s*ANTECEDENTES'
    
    # Patrón para detectar la causa objetiva
    CLAUSULA_CAUSA_OBJETIVA = r'CLÁUSULA SEGUNDA:\s*CAUSA OBJETIVA'
    
    # Patrón para detectar prórroga del plazo
    CLAUSULA_PRORROGA = r'CLÁUSULA TERCERA:\s*PRORROGA DEL PLAZO'
    
    # Patrón para detectar puesto y lugar de trabajo
    CLAUSULA_PUESTO = r'CLÁUSULA CUARTA:\s*PUESTO Y LUGAR DE TRABAJO'
    
    # Patrón para detectar remuneración
    CLAUSULA_REMUNERACION = r'CLÁUSULA QUINTA:\s*REMUNERACIÓN'
    
    # Patrón para detectar jornada y horario
    CLAUSULA_JORNADA = r'CLÁUSULA\s+(?:SEXTA|SÉTIMA):\s*JORNADA Y HORARIO'


# ============================================================================
# PATRONES DE DATOS DEL TRABAJADOR
# ============================================================================

class PatronesTrabajador:
    """
    Patrones regex para extracción de información del trabajador.
    """
    
    # Patrón para DNI: "identificado con DNI N° 12345678"
    DNI = r'identificado con DNI N[°º]\s*(\d{8})'
    
    # Patrón para nombre completo (después de "la otra parte")
    NOMBRE_COMPLETO = r'la otra parte\s+([A-ZÁÉÍÓÚÑ\s,]+),\s*identificado'
    
    # Patrón para domicilio
    DOMICILIO = r'con domicilio en\s+([^,]+),\s*distrito'
    
    # Patrón para distrito
    DISTRITO = r'distrito\s+(?:de\s+)?([^,]+),\s*provincia'
    
    # Patrón para provincia  
    PROVINCIA = r'provincia\s+(?:de\s+|y departamento de\s+)?([^,]+)'


# ============================================================================
# PATRONES DE DATOS DEL CONTRATO
# ============================================================================

class PatronesContrato:
    """
    Patrones regex para extracción de información del contrato.
    """
    
    # Patrón para fecha de inicio del contrato original
    FECHA_INICIO = r'Con fecha\s+(\d{1,2}\s+de\s+\w+\s+del?\s+\d{4})'
    
    # Patrón para fecha de término de prórroga anterior
    FECHA_TERMINO_ANTERIOR = r'hasta el\s+(\d{1,2}\s+de\s+\w+\s+de(?:l)?\s+\d{4})'
    
    # Patrón para plazo de prórroga: "por un plazo de SEIS (06) meses"
    PLAZO_PRORROGA = r'por un plazo de\s+([A-Z]+)\s+\((\d+)\)\s+(días|meses)'
    
    # Patrón para nueva fecha de término
    NUEVA_FECHA_TERMINO = r'hasta el\s+(\d{1,2})\s+de\s+(\w+)\s+del?\s+(\d{4})'
    
    # Patrón para remuneración: "S/. 1,600.00"
    REMUNERACION = r'S/\.\s*([\d,]+\.\d{2})'
    
    # Patrón para puesto de trabajo
    PUESTO_TRABAJO = r'puesto de\s+([A-Z\s]+)(?:,|\s+el cual)'


# ============================================================================
# PATRONES DE DATOS DEL EMPLEADOR
# ============================================================================

class PatronesEmpleador:
    """
    Patrones regex para extracción de información del empleador.
    """
    
    # Patrón para RUC
    RUC = r'RUC\s+(\d{11})'
    
    # Patrón para razón social
    RAZON_SOCIAL = r'de una parte\s+([A-Z\s\.]+),\s*identificado con RUC'
    
    # Patrón para representante legal
    REPRESENTANTE = r'representado para estos efectos por\s+([A-ZÁÉÍÓÚÑ\s]+),'


# ============================================================================
# FUNCIONES AUXILIARES
# ============================================================================

def buscar_patron_multiple(texto, patrones, flags=re.IGNORECASE):
    """
    Busca múltiples patrones en orden hasta encontrar una coincidencia.
    
    Args:
        texto (str): Texto donde buscar
        patrones (list): Lista de patrones regex a probar
        flags: Flags de re (por defecto re.IGNORECASE)
    
    Returns:
        Match object si encuentra coincidencia, None si no encuentra nada
        
    Example:
        >>> patrones = [r'patrón1', r'patrón2']
        >>> match = buscar_patron_multiple(texto, patrones)
        >>> if match:
        ...     print(match.groups())
    """
    for patron in patrones:
        match = re.search(patron, texto, flags)
        if match:
            return match
    return None


def extraer_fecha_normalizada(match):
    """
    Extrae y normaliza una fecha desde un match object.
    
    Args:
        match: Match object de re.search con grupos (dia, mes, año)
    
    Returns:
        str: Fecha normalizada en formato "DD de MES de AAAA"
        
    Example:
        >>> match = re.search(patron, texto)
        >>> fecha = extraer_fecha_normalizada(match)
        >>> print(fecha)  # "15 de diciembre de 2025"
    """
    if not match:
        return None
    
    dia = match.group(1)
    mes = match.group(2)
    anio = match.group(3)
    
    return f"{dia} de {mes} de {anio}"


def normalizar_mes(mes):
    """
    Convierte nombre de mes en español a número.
    
    Args:
        mes (str): Nombre del mes en español
    
    Returns:
        str: Número del mes con formato "MM" (01-12)
        
    Example:
        >>> normalizar_mes("diciembre")
        "12"
    """
    meses = {
        'enero': '01',
        'febrero': '02',
        'marzo': '03',
        'abril': '04',
        'mayo': '05',
        'junio': '06',
        'julio': '07',
        'agosto': '08',
        'setiembre': '09',
        'septiembre': '09',
        'octubre': '10',
        'noviembre': '11',
        'diciembre': '12'
    }
    return meses.get(mes.lower(), None)


# ============================================================================
# VALIDADORES
# ============================================================================

def validar_fecha_peruana(dia, mes, anio):
    """
    Valida que una fecha sea válida según calendario peruano.
    
    Args:
        dia (str/int): Día del mes
        mes (str): Nombre del mes en español
        anio (str/int): Año de 4 dígitos
    
    Returns:
        bool: True si la fecha es válida, False si no
        
    Example:
        >>> validar_fecha_peruana("31", "febrero", "2025")
        False
        >>> validar_fecha_peruana("15", "diciembre", "2025")
        True
    """
    try:
        from datetime import datetime
        
        # Convertir mes a número
        mes_num = normalizar_mes(mes)
        if not mes_num:
            return False
        
        # Intentar crear fecha
        fecha = datetime(int(anio), int(mes_num), int(dia))
        return True
    except (ValueError, TypeError):
        return False


def validar_dni(dni):
    """
    Valida formato de DNI peruano (8 dígitos).
    
    Args:
        dni (str): Número de DNI
    
    Returns:
        bool: True si es válido, False si no
        
    Example:
        >>> validar_dni("12345678")
        True
        >>> validar_dni("123")
        False
    """
    return bool(re.match(r'^\d{8}$', str(dni)))


def validar_ruc(ruc):
    """
    Valida formato de RUC peruano (11 dígitos).
    
    Args:
        ruc (str): Número de RUC
    
    Returns:
        bool: True si es válido, False si no
        
    Example:
        >>> validar_ruc("20262478964")
        True
        >>> validar_ruc("123")
        False
    """
    return bool(re.match(r'^\d{11}$', str(ruc)))