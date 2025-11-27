"""
Script para verificar y crear archivos __init__.py faltantes.
Ejecuta este script ANTES de build.py para asegurar que todos los paquetes
sean importables correctamente.
"""

import os
from pathlib import Path


def verificar_y_crear_init_py():
    """
    Verifica que todas las carpetas de módulos tengan __init__.py
    Los crea si faltan.
    """
    print("=" * 60)
    print("🔍 VERIFICACIÓN DE ARCHIVOS __init__.py")
    print("=" * 60)
    print()
    
    base_dir = Path(os.getcwd())
    
    # Carpetas que deben tener __init__.py
    carpetas_requeridas = [
        "core",
        "core/utils",
        "core/renovaciones",
        "core/contratos",
        "controllers",
        "gui",
        "gui/widgets",
        "gui/themes",
    ]
    
    archivos_creados = []
    archivos_existentes = []
    carpetas_faltantes = []
    
    for carpeta_rel in carpetas_requeridas:
        carpeta = base_dir / carpeta_rel
        init_file = carpeta / "__init__.py"
        
        # Verificar si la carpeta existe
        if not carpeta.exists():
            carpetas_faltantes.append(carpeta_rel)
            print(f"⚠️  Carpeta no existe: {carpeta_rel}")
            continue
        
        # Verificar si existe __init__.py
        if init_file.exists():
            archivos_existentes.append(carpeta_rel)
            print(f"✅ {carpeta_rel}/__init__.py (existe)")
        else:
            # Crear __init__.py vacío
            try:
                with open(init_file, 'w', encoding='utf-8') as f:
                    f.write(f'"""\n')
                    f.write(f'Paquete: {carpeta_rel}\n')
                    f.write(f'"""\n')
                
                archivos_creados.append(carpeta_rel)
                print(f"✨ {carpeta_rel}/__init__.py (CREADO)")
            except Exception as e:
                print(f"❌ Error al crear {carpeta_rel}/__init__.py: {e}")
    
    # Resumen
    print()
    print("=" * 60)
    print("📊 RESUMEN")
    print("=" * 60)
    print(f"✅ Archivos existentes: {len(archivos_existentes)}")
    print(f"✨ Archivos creados: {len(archivos_creados)}")
    print(f"⚠️  Carpetas faltantes: {len(carpetas_faltantes)}")
    print()
    
    if archivos_creados:
        print("📝 Archivos __init__.py creados:")
        for carpeta in archivos_creados:
            print(f"   - {carpeta}/__init__.py")
        print()
    
    if carpetas_faltantes:
        print("⚠️  ADVERTENCIA: Carpetas faltantes:")
        for carpeta in carpetas_faltantes:
            print(f"   - {carpeta}")
        print("\n   Estas carpetas no existen en tu proyecto.")
        print("   Si deberían existir, créalas antes de continuar.")
        print()
    
    if len(archivos_creados) == 0 and len(carpetas_faltantes) == 0:
        print("🎉 ¡Perfecto! Todos los archivos __init__.py están presentes.")
    elif len(archivos_creados) > 0:
        print("✅ Archivos __init__.py creados exitosamente.")
        print("   Ahora puedes ejecutar build.py")
    
    print("=" * 60)
    print()


def escanear_carpetas_sin_init():
    """
    Escanea el proyecto buscando carpetas con archivos .py
    que NO tengan __init__.py (posibles paquetes incompletos)
    """
    print("=" * 60)
    print("🔍 ESCANEO COMPLETO DE CARPETAS")
    print("=" * 60)
    print()
    
    base_dir = Path(os.getcwd())
    carpetas_modulos = ["core", "controllers", "gui"]
    
    problemas = []
    
    for carpeta_principal in carpetas_modulos:
        carpeta_path = base_dir / carpeta_principal
        
        if not carpeta_path.exists():
            continue
        
        # Buscar todas las subcarpetas
        for carpeta in carpeta_path.rglob("*"):
            if not carpeta.is_dir():
                continue
            
            # Ignorar __pycache__
            if "__pycache__" in str(carpeta):
                continue
            
            # Verificar si la carpeta contiene archivos .py
            archivos_py = list(carpeta.glob("*.py"))
            
            if len(archivos_py) > 0:
                # Hay archivos .py, debe tener __init__.py
                init_file = carpeta / "__init__.py"
                
                if not init_file.exists():
                    ruta_relativa = carpeta.relative_to(base_dir)
                    problemas.append((str(ruta_relativa), len(archivos_py)))
    
    if problemas:
        print("⚠️  CARPETAS CON ARCHIVOS .py SIN __init__.py:")
        print()
        for carpeta, num_archivos in problemas:
            print(f"   📁 {carpeta}")
            print(f"      └─ {num_archivos} archivo(s) .py encontrado(s)")
            print(f"      └─ ❌ Falta __init__.py")
            print()
        
        print("💡 RECOMENDACIÓN:")
        print("   Estas carpetas contienen archivos .py pero no tienen __init__.py")
        print("   Esto puede causar problemas de importación.")
        print()
        
        respuesta = input("¿Deseas crear __init__.py en estas carpetas? (S/N): ").strip().lower()
        
        if respuesta in ("s", "si", "sí", "yes", "y"):
            print()
            for carpeta, _ in problemas:
                carpeta_path = base_dir / carpeta
                init_file = carpeta_path / "__init__.py"
                
                try:
                    with open(init_file, 'w', encoding='utf-8') as f:
                        f.write(f'"""\n')
                        f.write(f'Paquete: {carpeta}\n')
                        f.write(f'"""\n')
                    
                    print(f"   ✨ Creado: {carpeta}/__init__.py")
                except Exception as e:
                    print(f"   ❌ Error en {carpeta}: {e}")
            
            print("\n✅ Archivos __init__.py creados.")
        else:
            print("\n⏭️  Omitiendo creación de archivos.")
    else:
        print("✅ No se encontraron problemas.")
        print("   Todas las carpetas con archivos .py tienen __init__.py")
    
    print()
    print("=" * 60)
    print()


if __name__ == "__main__":
    print("\n")
    print("🛠️  HERRAMIENTA DE VERIFICACIÓN DE PAQUETES PYTHON")
    print("   Asegura que todos los módulos sean importables")
    print()
    
    # Verificar y crear __init__.py en carpetas conocidas
    verificar_y_crear_init_py()
    
    # Escanear proyecto completo buscando problemas
    escanear_carpetas_sin_init()
    
    print("🎯 PRÓXIMO PASO:")
    print("   Ejecuta: python build.py")
    print()