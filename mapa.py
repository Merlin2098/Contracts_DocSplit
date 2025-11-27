import os

def generar_arbol(directorio, prefijo="", excluidos=None, carpetas_ignoradas=None):
    """
    Genera una lista de strings con el árbol de directorios, ignorando archivos y carpetas específicas.
    """
    if excluidos is None:
        excluidos = set()
    if carpetas_ignoradas is None:
        carpetas_ignoradas = set()

    contenido = []
    try:
        archivos = sorted(os.listdir(directorio))
    except PermissionError:
        return contenido  # Evita carpetas sin permisos

    for index, nombre in enumerate(archivos):
        if nombre in excluidos or nombre in carpetas_ignoradas:
            continue

        ruta = os.path.join(directorio, nombre)
        es_ultimo = index == len(archivos) - 1
        conector = "└── " if es_ultimo else "├── "
        contenido.append(f"{prefijo}{conector}{nombre}")

        if os.path.isdir(ruta):
            extension = "    " if es_ultimo else "│   "
            contenido.extend(
                generar_arbol(ruta, prefijo + extension, excluidos, carpetas_ignoradas)
            )
    return contenido


def obtener_archivos_raiz(directorio):
    """
    Devuelve una lista de archivos directamente en la raíz del proyecto.
    """
    return [
        f for f in os.listdir(directorio)
        if os.path.isfile(os.path.join(directorio, f))
    ]


if __name__ == "__main__":
    raiz = os.path.dirname(os.path.abspath(__file__))

    # Archivos que siempre se excluyen
    excluidos_por_defecto = {"main.py", "__init__.py", "requirements.txt"}

    # Carpetas que siempre se ignoran
    carpetas_ignoradas = {".git", "__pycache__", ".venv", "venv", ".idea", ".vscode", "logs"}

    # Detectar archivos raíz
    archivos_raiz = obtener_archivos_raiz(raiz)
    candidatos_excluir = [f for f in archivos_raiz if f not in excluidos_por_defecto]

    print("📁 Archivos detectados en la raíz del proyecto:")
    for f in candidatos_excluir:
        print(f"  - {f}")
    print("\n(Estos son los archivos que están directamente en la raíz.)")

    entrada = input(
        "\n👉 Ingresa los nombres de los archivos que deseas excluir (separa con '|', deja vacío para ninguno):\n> "
    ).strip()

    excluidos_usuario = set()
    if entrada:
        excluidos_usuario = set(map(str.strip, entrada.split("|")))

    # Combinar exclusiones
    excluidos = excluidos_por_defecto.union(excluidos_usuario)

    print("\n🚫 Archivos que serán excluidos del árbol:")
    for f in sorted(excluidos):
        print(f"  - {f}")

    print("\n🚫 Carpetas que serán ignoradas automáticamente:")
    for c in sorted(carpetas_ignoradas):
        print(f"  - {c}")

    # Generar árbol
    arbol = generar_arbol(raiz, excluidos=excluidos, carpetas_ignoradas=carpetas_ignoradas)
    salida = "\n".join(arbol)

    # Mostrar y guardar
    print("\n\n📄 Estructura del Proyecto:\n")
    print(salida)

    with open("README_tree.md", "w", encoding="utf-8") as f:
        f.write("## 📁 Estructura del Proyecto\n\n```\n")
        f.write(salida)
        f.write("\n```\n")

    print("\n✅ Árbol generado y guardado en README_tree.md\n")
