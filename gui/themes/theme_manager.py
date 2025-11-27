"""
Theme Manager - Gestor Universal de Temas
Maneja la carga y cambio de temas desde archivos JSON
Compatible con CustomTkinter y PyQt5
"""

import json
from pathlib import Path
from typing import Dict, Any, Optional


class ThemeManager:
    """Gestor centralizado de temas para interfaces gráficas."""
    
    def __init__(self, themes_dir: str = "."):
        """
        Inicializa el gestor de temas.
        
        Args:
            themes_dir: Directorio donde se encuentran los archivos JSON de temas
        """
        self.themes_dir = Path(themes_dir)
        self.current_theme: str = "light"
        self.themes: Dict[str, Dict[str, Any]] = {}
        self._load_themes()
    
    def _load_themes(self) -> None:
        """Carga todos los archivos de tema disponibles."""
        theme_files = list(self.themes_dir.glob("theme_*.json"))
        
        if not theme_files:
            raise FileNotFoundError(
                f"No se encontraron archivos de tema en {self.themes_dir}"
            )
        
        for theme_file in theme_files:
            try:
                with open(theme_file, 'r', encoding='utf-8') as f:
                    theme_data = json.load(f)
                    theme_name = theme_data.get("name", theme_file.stem.replace("theme_", ""))
                    self.themes[theme_name] = theme_data
            except json.JSONDecodeError as e:
                print(f"Error al cargar {theme_file}: {e}")
    
    def get_theme(self, theme_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Obtiene los datos de un tema.
        
        Args:
            theme_name: Nombre del tema. Si es None, devuelve el tema actual
            
        Returns:
            Diccionario con los datos del tema
        """
        name = theme_name or self.current_theme
        if name not in self.themes:
            raise ValueError(f"Tema '{name}' no encontrado")
        return self.themes[name]
    
    def set_theme(self, theme_name: str) -> None:
        """
        Cambia el tema actual.
        
        Args:
            theme_name: Nombre del tema a activar
        """
        if theme_name not in self.themes:
            raise ValueError(f"Tema '{theme_name}' no encontrado")
        self.current_theme = theme_name
    
    def toggle_theme(self) -> str:
        """
        Alterna entre tema claro y oscuro.
        
        Returns:
            Nombre del nuevo tema activo
        """
        self.current_theme = "dark" if self.current_theme == "light" else "light"
        return self.current_theme
    
    def get_color(self, *keys: str) -> str:
        """
        Obtiene un color específico del tema actual.
        
        Args:
            *keys: Ruta de claves para acceder al color (ej: "colors", "primary")
            
        Returns:
            Código hexadecimal del color
        """
        theme = self.get_theme()
        value = theme
        
        for key in keys:
            if isinstance(value, dict):
                value = value.get(key)
            else:
                raise KeyError(f"No se pudo acceder a {'.'.join(keys)}")
        
        return value
    
    def get_component_colors(self, component: str) -> Dict[str, str]:
        """
        Obtiene todos los colores de un componente específico.
        
        Args:
            component: Nombre del componente (button, card, input)
            
        Returns:
            Diccionario con los colores del componente
        """
        return self.get_theme()["components"][component]
    
    def get_available_themes(self) -> list:
        """Retorna lista de temas disponibles."""
        return list(self.themes.keys())
    
    def get_theme_icon(self, theme_name: Optional[str] = None) -> str:
        """
        Obtiene el icono representativo del tema.
        
        Args:
            theme_name: Nombre del tema. Si es None, usa el tema actual
            
        Returns:
            Emoji del icono (☀️ para claro, 🌙 para oscuro)
        """
        name = theme_name or self.current_theme
        return "☀️" if name == "light" else "🌙"