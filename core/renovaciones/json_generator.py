"""
Generador de JSON consolidado con estructura de secciones detectadas.
Genera un UNICO JSON con todos los archivos procesados.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional, List


class JSONGenerator:
    """
    Genera un JSON consolidado con todos los PDFs procesados.
    Estructura similar a diagnostico_rangos.json
    """
    
    def __init__(self):
        """Inicializa el generador con un diccionario vacio para acumular datos."""
        self.datos_consolidados = {}
    
    def agregar_archivo(
        self,
        nombre_archivo: str,
        resultado_deteccion: Dict,
        fecha_contrato: Optional[str]
    ):
        """
        Agrega la informacion de un archivo al JSON consolidado.
        
        Args:
            nombre_archivo: Nombre del PDF procesado
            resultado_deteccion: Dict retornado por SectionDetector
            fecha_contrato: Fecha del contrato en formato MM.YYYY
        """
        # Convertir secciones al formato esperado
        secciones_formato = {}
        
        for seccion in resultado_deteccion.get("secciones", []):
            nombre_seccion = seccion["tipo_seccion"]
            
            # Si la seccion tiene paginas validas
            if seccion["pagina_inicio"] is not None and seccion["pagina_fin"] is not None:
                secciones_formato[nombre_seccion] = {
                    "inicio": seccion["pagina_inicio"] + 1,  # Convertir a base-1
                    "fin": seccion["pagina_fin"] + 1
                }
            else:
                # Seccion no detectada
                secciones_formato[nombre_seccion] = None
        
        # Agregar datos del archivo al consolidado
        self.datos_consolidados[nombre_archivo] = {
            "total_paginas": resultado_deteccion.get("total_paginas", 0),
            "fecha_contrato": fecha_contrato if fecha_contrato else "No detectada",
            "secciones": secciones_formato
        }
    
    def generar_json_consolidado(self, ruta_salida: Path, nombre_json: str = "diagnostico_rangos.json") -> Path:
        """
        Genera el archivo JSON consolidado con todos los archivos procesados.
        
        Args:
            ruta_salida: Directorio donde guardar el JSON
            nombre_json: Nombre del archivo JSON (default: diagnostico_rangos.json)
            
        Returns:
            Path del archivo JSON generado
        """
        ruta_json = ruta_salida / nombre_json
        
        # Guardar JSON con formato legible
        with open(ruta_json, 'w', encoding='utf-8') as f:
            json.dump(self.datos_consolidados, f, indent=2, ensure_ascii=False)
        
        return ruta_json
    
    def obtener_resumen(self) -> Dict:
        """
        Obtiene un resumen de los datos consolidados.
        
        Returns:
            Dict con estadisticas del procesamiento
        """
        total_archivos = len(self.datos_consolidados)
        total_paginas = sum(datos["total_paginas"] for datos in self.datos_consolidados.values())
        
        # Contar fechas detectadas
        fechas_detectadas = sum(
            1 for datos in self.datos_consolidados.values() 
            if datos["fecha_contrato"] != "No detectada"
        )
        
        return {
            "total_archivos": total_archivos,
            "total_paginas": total_paginas,
            "fechas_detectadas": fechas_detectadas,
            "fechas_no_detectadas": total_archivos - fechas_detectadas
        }
    
    @staticmethod
    def cargar_json(ruta_json: Path) -> Dict:
        """
        Carga un JSON consolidado previamente generado.
        
        Args:
            ruta_json: Ruta al archivo JSON
            
        Returns:
            Dict con la estructura cargada
        """
        with open(ruta_json, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    @staticmethod
    def validar_json(estructura: Dict) -> bool:
        """
        Valida que el JSON consolidado tenga la estructura esperada.
        
        Args:
            estructura: Dict cargado del JSON
            
        Returns:
            True si la estructura es valida
        """
        if not isinstance(estructura, dict):
            return False
        
        # Verificar que cada archivo tenga los campos requeridos
        for nombre_archivo, datos in estructura.items():
            campos_requeridos = ["total_paginas", "fecha_contrato", "secciones"]
            if not all(campo in datos for campo in campos_requeridos):
                return False
        
        return True