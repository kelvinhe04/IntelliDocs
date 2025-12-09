# Análisis Inteligente de Documentos Empresariales

Este sistema es una solución avanzada para la automatización del análisis de documentos. Permite subir archivos PDF, extraer su contenido (texto e imágenes), clasificarlos automáticamente por categoría (Legal, Financiero, Técnico) y generar resúmenes utilizando Inteligencia Artificial.

## 📂 Estructura del Proyecto

```
/
├── backend/                # El "Cerebro" del sistema (API)
│   ├── main.py             # Punto de entrada de la API (FastAPI)
│   ├── extractor.py        # Módulo de extracción de texto (OCR)
│   ├── summarizer.py       # Módulo de resumen (IA)
│   ├── classifier.py       # Módulo de clasificación
│   ├── embeddings.py       # Motor de búsqueda semántica
│   └── requirements.txt    # Dependencias de Python
│
├── frontend/               # La "Cara" del sistema (Interfaz)
│   └── app.py              # Aplicación web (Streamlit)
│
├── data/                   # Almacenamiento local (Ignorado por Git)
│   ├── uploads/            # Documentos subidos
│   └── faiss_index.bin     # Base de datos vectorial
│
└── README.md               # Este archivo
```

## 🧠 Tecnologías y Modelos (Cómo funciona)

Este sistema utiliza un stack tecnológico moderno de Inteligencia Artificial:

### Librerías Principales
-   **Backend**: `FastAPI` (Servidor rápido), `Uvicorn` (ASGI).
-   **Procesamiento PDF**: `pdfplumber` (Texto digital), `pytesseract` (OCR para imágenes).
-   **Frontend**: `Streamlit` (Interfaz web interactiva).
-   **Vectores**: `FAISS` (Búsqueda semántica de alta velocidad).

### Modelos de Inteligencia Artificial
El sistema descarga y ejecuta localmente los siguientes modelos de HuggingFace:

1.  **Resumen**: `csebuetnlp/mT5_multilingual_XLSum`
    *   *Función*: Modelo multilingüe experto en resumir textos en 45 idiomas (incluido Español).
2.  **Clasificación**: `facebook/bart-large-mnli`
    *   *Función*: Clasificación "Zero-Shot" (sin entrenamiento previo) para categorizar documentos.
3.  **Búsqueda (Embeddings)**: `sentence-transformers/all-MiniLM-L6-v2`
    *   *Función*: Convierte texto a vectores matemáticos para comparar su significado semántico.

## 🛠️ Requisitos Previos

Antes de iniciar, necesitas tener instalado:

1.  **Python 3.8+**: [Descargar Python](https://www.python.org/downloads/)
2.  **Tesseract OCR**: **CRUCIAL** para leer documentos escaneados o imágenes.
    *   **Descarga**: [Tesseract-OCR-w64-setup.exe](https://github.com/UB-Mannheim/tesseract/wiki) (Versión Windows 64-bit)
    *   **Instalación**: Instálalo en la ruta por defecto: `C:\Program Files\Tesseract-OCR`.
    *   *¿Para qué sirve?*: Sin esto, el sistema no podrá leer PDFs que sean imágenes (scans).

## 🚀 Guía de Inicio Rápido

El sistema requiere **dos terminales** abiertas simultáneamente.

### 1. Terminal 1: Iniciar el Backend
Esta terminal procesa los datos y ejecuta los modelos de IA.
```bash
cd backend
python main.py
```
*Espera hasta ver el mensaje: `Application startup complete`.*

### 2. Terminal 2: Iniciar el Frontend
Esta terminal lanza la página web donde usarás el programa.
Abre una **nueva** terminal en la carpeta del proyecto y ejecuta:
```bash
streamlit run frontend/app.py
```
*Se abrirá automáticamente el navegador en `http://localhost:8501`.*

## ⚠️ Solución de Problemas Comunes

-   **Error "Tesseract not found"**: Significa que no instalaste Tesseract OCR o no está en la ruta correcta. Instálalo según la sección de Requisitos.
-   **Error "ModuleNotFoundError"**: Te faltó instalar librerías. Ejecuta: `pip install -r backend/requirements.txt`.
-   **La página muestra "Connection Error"**: Asegúrate de que la Terminal 1 (Backend) sigue ejecutándose y no tiene errores.
