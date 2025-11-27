# 📋 Roadmap del Proyecto

## ✅ COMPLETADO

### 🧩 Fase 1: Arquitectura Base
- ✅ GUI con PyQt5 (2 tabs + theme manager)  
- ✅ Widgets reutilizables (`FileSelector`, `LogViewer`, `ProgressDialog`)  
- ✅ Sistema de temas (dark/light)

---

### ⚙️ Fase 2: Workflow Renovaciones
- ✅ Módulos core compartidos (`extractor`, `file_utils`, `logger`)  
- ✅ Detector de 3 secciones  
- ✅ Controller con logs dual y medición de tiempo  
- ✅ Tab con barra de progreso integrada  
- ✅ Sistema funcional end-to-end  

---

### 🗂️ Fase 3: Workflow Contratos - Paso 1 (**Normalizar**)
**Objetivo:** Implementar normalización de nombres de archivos PDF y estructurar sistema de logs centralizado

**Archivos creados/modificados:**
- `core/pdf_tools/contratos_normalizer.py` → Lógica de normalización  
- `controllers/contratos_controller.py` → Función `normalizar_contratos()`  
- `gui/tab_contratos.py` → Conectar botón **"① Normalizar"**

**Nuevas características:**
- ✅ Normaliza nombres de archivos  
  - `"Contrato - Juan Perez (2).pdf"` → `"Juan Perez.pdf"`  
- ✅ Evita sobrescribir archivos existentes  
- ✅ Genera log con timestamp  
- ✅ Muestra progreso en barra integrada  
- ✅ **Implementación de carpeta de logs centralizada:**  
  - Estructura: `logs/{pestaña}/{año}/{mes}/`  
  - Ejemplo: `logs/contratos/2025/11/normalizar_12.11.2025_10.30.log`  
- ✅ Integración con sistema de control de tiempo y resultados en GUI  

**⏱ Tiempo estimado:** 1 sesión  
**🟢 Estado:** **Completado con éxito**

---

## 🎯 PENDIENTE

### 🔍 Fase 4: Workflow Contratos - Paso 2 (**Diagnosticar**)
**Objetivo:** Detectar 12 secciones y generar JSON

**Archivos a crear/modificar:**
- `core/pdf_tools/contratos_detector.py` → Detector de 12 secciones con heurísticas  
- `controllers/contratos_controller.py` → Función `diagnosticar_contratos()`  
- `gui/tab_contratos.py` → Conectar botón **"② Diagnosticar"**

**Funcionalidad esperada:**
- Detecta 12 secciones (Contrato, Alta Sunat, Guía, Derechohabiente, Políticas, RIT, RISST, Auditoría, etc.)  
- Usa heurísticas con página ancla  
- Genera `diagnostico_DD.MM.YYYY_HH.MM.SS.json`  
- Genera `diagnostico_DD.MM.YYYY_HH.MM.SS.log`  
- Extrae fecha del contrato  
- Guarda resultados en carpeta de logs estructurada por mes y año  

**⏱ Tiempo estimado:** 1–2 sesiones  

---

### 🧠 Fase 5: Workflow Contratos - Paso 3 (**Procesar**)
**Objetivo:** Extraer secciones usando JSON de diagnóstico

**Archivos a modificar:**
- `controllers/contratos_controller.py` → Función `procesar_contratos()`  
- `gui/tab_contratos.py` → Conectar botón **"③ Procesar"**

**Funcionalidad esperada:**
- Lee JSON de diagnóstico  
- Extrae secciones detectadas  
- Renombra: `{Seccion}-{Fecha}-{NombreArchivo}.pdf`  
- Genera logs duales con timestamp  
- Mide tiempo de ejecución  
- Almacena logs en `logs/contratos/{año}/{mes}/`  

**⏱ Tiempo estimado:** 1 sesión  

---

### 🧪 Fase 6: Validación y Pruebas
**Objetivo:** Asegurar calidad y robustez

**Tareas:**
- Crear tests unitarios para módulos core  
- Crear tests de integración para controllers  
- Validar manejo de errores (PDFs corruptos, permisos, etc.)  
- Probar con datasets reales  
- Documentar casos edge  

**Archivos:**
- `tests/test_renovaciones_detector.py`  
- `tests/test_contratos_detector.py`  
- `tests/test_extractor.py`  
- `tests/test_file_utils.py`  

**⏱ Tiempo estimado:** 1–2 sesiones  

---

### 🎨 Fase 7: Optimización y UX
**Objetivo:** Mejorar experiencia de usuario

**Mejoras sugeridas:**
- Arreglar tema claro (contraste de colores)  
- Agregar botón **"Abrir carpeta"** después de procesar  
- Implementar **Drag & Drop** para seleccionar carpetas  
- Agregar validación de PDFs antes de procesar  
- Mostrar preview del primer PDF antes de procesar  
- Agregar botón **"Cancelar"** en procesamiento  

**⏱ Tiempo estimado:** 1–2 sesiones  

---

### 🚀 Fase 8: Distribución
**Objetivo:** Empaquetar aplicación para distribución

**Tareas:**
- Configurar PyInstaller  
- Crear ejecutable `.exe` (one-directory)  
- Crear instalador (opcional)  
- Documentar proceso de instalación  
- `README` con instrucciones de uso  

**Archivos:**
- `build_exe.spec` → Configuración de PyInstaller  
- `README.md` → Documentación completa  
- `requirements.txt` → Dependencias finales  

**⏱ Tiempo estimado:** 1 sesión  
