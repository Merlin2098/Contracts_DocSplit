## 📁 Estructura del Proyecto

```
├── arquitectura.md
├── arquitectura_.png
├── controllers
│   ├── contratos_controller.py
│   └── renovaciones_controller.py
├── core
│   ├── contratos
│   │   ├── diagnostico.py
│   │   └── processor.py
│   ├── pdf_tools
│   │   ├── contratos_normalizer.py
│   │   ├── extractor.py
│   │   ├── pdf_splitter.py
│   │   ├── renovaciones_detector.py
│   │   └── section_detector.py
│   ├── renovaciones
│   │   └── processor.py
│   └── utils
│       ├── file_utils.py
│       ├── json_handler.py
│       ├── logger.py
│       └── validators.py
├── data
├── gui
│   ├── main_window.py
│   ├── resources
│   │   └── app.ico
│   ├── tab_contratos.py
│   ├── tab_renovaciones.py
│   ├── themes
│   │   ├── theme_dark.json
│   │   ├── theme_light.json
│   │   └── theme_manager.py
│   └── widgets
│       ├── file_selector.py
│       ├── log_viewer.py
│       └── progress_dialog.py
├── mapa.py
├── progreso.md
└── tests
|   └── test_core_modules.py
│       ├── file_selector.py
│__main.py
