import os
import sys
import pkg_resources
import subprocess
import shutil

# ==========================================================
# CONFIGURACIÓN
# ==========================================================
NOMBRE_EXE = "GestionPDFs.exe"
MAIN_SCRIPT = "main.py"

DIST_PATH = "dist"
BUILD_PATH = "build"
SPEC_PATH = "spec"

EXCLUSIONES = [
    "pip", "wheel", "setuptools", "pkg_resources",
    "distutils", "ensurepip", "test", "tkinter.test",
    "pytest", "pytest_cov", "coverage", "pytest-qt"
]

# ==========================================================
# VALIDAR ENTORNO VIRTUAL
# ==========================================================
def validar_entorno_virtual():
    print("=" * 60)
    print("🔍 VALIDACIÓN DE ENTORNO VIRTUAL")
    print("=" * 60)

    if sys.prefix == sys.base_prefix:
        print("⚠️  ADVERTENCIA: No estás dentro de un entorno virtual (venv).")
        print("   Se recomienda usar uno, pero continuaremos de todas formas.")
    else:
        print(f"✅ Entorno virtual detectado: {sys.prefix}")

    print()
    paquetes = sorted([(pkg.key, pkg.version) for pkg in pkg_resources.working_set])
    print(f"📦 Librerías instaladas ({len(paquetes)}):")
    
    # Mostrar solo las primeras 10 para no saturar
    for nombre, version in paquetes[:10]:
        flag = "🧹 (excluir)" if nombre in EXCLUSIONES else "✅"
        print(f"   {flag} {nombre:<20} {version}")
    
    if len(paquetes) > 10:
        print(f"   ... y {len(paquetes) - 10} más")
    print("\n")

# ==========================================================
# CONFIRMACIÓN MANUAL
# ==========================================================
def confirmar_ejecucion():
    print("=" * 60)
    print("⚠️  CONFIRMACIÓN DE EJECUCIÓN FINAL")
    print("=" * 60)
    respuesta = input("¿Deseas generar el ejecutable ahora? (S/N): ").strip().lower()

    if respuesta not in ("s", "si", "sí", "yes", "y"):
        print("\n🛑 Proceso cancelado por el usuario.")
        sys.exit(0)

    print("\n✅ Confirmado. Continuando con la generación...\n")

# ==========================================================
# LIMPIAR BUILDS ANTERIORES
# ==========================================================
def limpiar_builds():
    print("🧹 Limpiando builds anteriores...")
    for carpeta in [DIST_PATH, BUILD_PATH, SPEC_PATH]:
        if os.path.exists(carpeta):
            try:
                shutil.rmtree(carpeta)
                print(f"   ✅ Limpiado: {carpeta}")
            except Exception as e:
                print(f"   ⚠️  No se pudo limpiar {carpeta}: {e}")
    
    # Eliminar archivos .spec sueltos
    for archivo in os.listdir('.'):
        if archivo.endswith('.spec'):
            try:
                os.remove(archivo)
                print(f"   ✅ Eliminado: {archivo}")
            except Exception as e:
                print(f"   ⚠️  No se pudo eliminar {archivo}: {e}")
    print()

# ==========================================================
# CONSTRUIR COMANDO PYINSTALLER
# ==========================================================
def construir_comando():
    base_dir = os.getcwd()

    comando = [
        sys.executable, "-m", "PyInstaller",
        "--onedir",
        "--windowed",
        "--clean",
        "--log-level", "WARN",
        "--distpath", DIST_PATH,
        "--workpath", BUILD_PATH,
        "--specpath", SPEC_PATH,
        "--name", NOMBRE_EXE.replace(".exe", ""),

        # Añadir paths para que encuentre los módulos
        "--paths", base_dir,
        "--paths", os.path.join(base_dir, "core"),
        "--paths", os.path.join(base_dir, "controllers"),
        "--paths", os.path.join(base_dir, "gui"),

        # Dependencias ocultas necesarias
        "--hidden-import=PyQt5",
        "--hidden-import=PyQt5.QtCore",
        "--hidden-import=PyQt5.QtGui",
        "--hidden-import=PyQt5.QtWidgets",
        "--hidden-import=fitz",
        "--hidden-import=PIL",
        "--hidden-import=PIL.Image",
        "--hidden-import=tqdm",
    ]

    # Excluir módulos innecesarios
    for excl in EXCLUSIONES:
        comando += ["--exclude-module", excl]

    # ======================================================
    # 📂 ESTRUCTURA DE CARPETAS Y ARCHIVOS (DATOS)
    # ======================================================
    
    # 1. Temas JSON (DATOS CRÍTICOS)
    theme_dark = os.path.join(base_dir, "gui", "themes", "theme_dark.json")
    theme_light = os.path.join(base_dir, "gui", "themes", "theme_light.json")
    
    if os.path.exists(theme_dark):
        comando += ["--add-data", f"{theme_dark};gui/themes"]
        print(f"   ✅ Incluido: theme_dark.json")
    else:
        print(f"   ⚠️  No encontrado: theme_dark.json")
    
    if os.path.exists(theme_light):
        comando += ["--add-data", f"{theme_light};gui/themes"]
        print(f"   ✅ Incluido: theme_light.json")
    else:
        print(f"   ⚠️  No encontrado: theme_light.json")

    # 2. Icono de la aplicación (DATOS Y RECURSO EXE)
    ico_path = os.path.join(base_dir, "gui", "resources", "app.ico")
    if os.path.exists(ico_path):
        comando += ["--icon", ico_path]
        comando += ["--add-data", f"{ico_path};gui/resources"]
        print(f"   ✅ Incluido: app.ico")
    else:
        print(f"   ⚠️  No encontrado: app.ico (se usará icono por defecto)")

    # 3. Crear carpeta logs vacía en el bundle
    logs_dir = os.path.join(base_dir, "logs")
    if not os.path.exists(logs_dir):
        os.makedirs(logs_dir, exist_ok=True)
    
    logs_placeholder = os.path.join(logs_dir, ".keep")
    if not os.path.exists(logs_placeholder):
        with open(logs_placeholder, 'w') as f:
            f.write("# Placeholder para mantener la carpeta logs\n")
    
    comando += ["--add-data", f"{logs_placeholder};logs"]
    print(f"   ✅ Incluido: carpeta logs")

    # Script principal con ruta completa
    main_path = os.path.join(base_dir, MAIN_SCRIPT)
    comando.append(main_path)
    
    print()
    return comando

# ==========================================================
# GENERAR EXE
# ==========================================================
def generar_exe():
    print("=" * 60)
    print("🚀 INICIANDO GENERACIÓN DEL EJECUTABLE (MODO ONEDIR)")
    print("=" * 60)

    verificar_main()
    verificar_estructura()
    limpiar_builds()

    cmd = construir_comando()
    print("⚙️  Comando PyInstaller:")
    print("   ", " ".join(cmd[:10]), "...")  # Mostrar solo inicio del comando
    print("\n🔨 Compilando, por favor espera...\n")

    result = subprocess.run(cmd)

    print("=" * 60)
    if result.returncode == 0:
        carpeta_exe = os.path.join(DIST_PATH, NOMBRE_EXE.replace(".exe", ""))
        print(f"✅ Generación completada correctamente.")
        print(f"📂 Carpeta de salida: {carpeta_exe}")
        print(f"📦 Ejecutable: {os.path.join(carpeta_exe, NOMBRE_EXE)}")
        print(f"\n💡 Para distribuir: Comprime toda la carpeta '{carpeta_exe}'")
    else:
        print("❌ Error: PyInstaller no se ejecutó correctamente.")
        print("💡 Revisa los mensajes de error arriba para más detalles.")
    print("=" * 60)

# ==========================================================
# VERIFICAR SCRIPT PRINCIPAL
# ==========================================================
def verificar_main():
    ruta = os.path.join(os.getcwd(), MAIN_SCRIPT)
    if not os.path.isfile(ruta):
        print(f"❌ ERROR: No se encontró '{MAIN_SCRIPT}' en el directorio actual.")
        sys.exit(1)
    else:
        print(f"✅ Archivo principal encontrado: {MAIN_SCRIPT}\n")

# ==========================================================
# VERIFICAR ESTRUCTURA DE CARPETAS
# ==========================================================
def verificar_estructura():
    print("🔍 Verificando estructura del proyecto:")
    
    carpetas_requeridas = [
        "core",
        "controllers", 
        "gui"
    ]
    
    archivos_criticos = [
        "main.py",
        "gui/main_window.py",
        "gui/tab_renovaciones.py",
        "gui/tab_contratos.py",
        "core/utils/logger.py",
        "controllers/renovaciones_controller.py",
        "controllers/contratos_controller.py"
    ]
    
    archivos_opcionales = [
        "gui/themes/theme_dark.json",
        "gui/themes/theme_light.json",
        "gui/resources/app.ico"
    ]
    
    todo_ok = True
    
    # Verificar carpetas
    for carpeta in carpetas_requeridas:
        if os.path.exists(carpeta):
            print(f"   ✅ Carpeta '{carpeta}' encontrada")
        else:
            print(f"   ❌ Carpeta '{carpeta}' NO encontrada")
            todo_ok = False
    
    # Verificar archivos críticos
    for archivo in archivos_criticos:
        if os.path.exists(archivo):
            print(f"   ✅ Archivo '{archivo}' encontrado")
        else:
            print(f"   ❌ Archivo '{archivo}' NO encontrado")
            todo_ok = False
    
    # Verificar archivos opcionales
    for archivo in archivos_opcionales:
        if os.path.exists(archivo):
            print(f"   ✅ Archivo '{archivo}' encontrado")
        else:
            print(f"   ⚠️  Archivo '{archivo}' NO encontrado (opcional)")
    
    if not todo_ok:
        print("\n❌ ERROR: Estructura del proyecto incompleta.")
        print("   Asegúrate de ejecutar este script desde la raíz del proyecto.")
        sys.exit(1)
    
    print()

# ==========================================================
# EJECUCIÓN PRINCIPAL
# ==========================================================
if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("   GENERADOR DE EJECUTABLE - GESTIÓN DE PDFs")
    print("   Renovaciones y Contratos")
    print("=" * 60 + "\n")
    
    validar_entorno_virtual()
    confirmar_ejecucion()
    generar_exe()
    
    print("\n🎉 Proceso completado. ¡Gracias por usar el generador!")