# Análisis Inteligente de Documentos Multimodal (Gemini 2.5 Flash)

Este sistema es una solución de vanguardia para el análisis de documentos e imágenes. Utiliza el modelo **Gemini 2.5 Flash** de Google para procesar PDFs y fotos, extrayendo información con precisión humana, identificando objetos visuales (Modo Lens) y permitiendo búsquedas semánticas con razonamiento profundo.

## 🚀 Características Principales

*   **Análisis Multimodal**: Sube **PDFs** (nativos o escaneados) o **Imágenes** (JPG, PNG, WEBP). El sistema lee todo.
*   **Visual Search (Modo Lens)**: Si subes la foto de un coche, producto o lugar, el sistema usa **Google Search Grounding** para identificar la Marca, Modelo y Año exacto.
*   **Búsqueda Semántica con Razonamiento**: No busca solo por palabras clave.
    *   *Ejemplo*: Si buscas "documentos de deuda", el sistema lee el contenido real y te explica: *"💡 Análisis: Este documento es relevante porque contiene una tabla de amortización..."*.
    *   **Full Context**: Lee el documento completo (50k+ caracteres), no solo resúmenes, para encontrar detalles ocultos.
*   **Prevención de Duplicados**: Sistema inteligente que bloquea la subida de archivos ya existentes para mantener limpia tu base de datos.
*   **Clasificación Dinámica**: No usa categorías fijas. El modelo determina profesionalmente de qué trata el documento (ej: "Factura Electrónica", "Contrato de Arrendamiento").

## 📂 Estructura del Proyecto

```
/
├── backend/                # El "Cerebro" del sistema
│   ├── main.py             # API Principal (FastAPI)
│   ├── gemini_service.py   # Integración con Google Gemini (Vision + Search)
│   ├── vector_store.py     # Base de datos vectorial (FAISS) + Gestión de Duplicados
│   ├── embeddings.py       # Generador de Embeddings Locales
│   └── requirements.txt    # Todas las dependencias (Backend + Frontend)
│
├── frontend/               # La "Interfaz"
│   └── app.py              # Aplicación Web (Streamlit)
│
├── data/                   # Almacenamiento
│   ├── uploads/            # PDFs/Imágenes subidos y sus .txt extraídos
│   └── faiss_index.bin     # Índice de búsqueda rápida
└── README.md
```

## 🛠️ Requisitos e Instalación

Necesitas tener **Python 3.10+** instalado.

1.  **Clonar/Descargar** este repositorio.
2.  **Instalar dependencias**:
    (Todas las librerías necesarias están en `backend/requirements.txt`)
    ```bash
    pip install -r backend/requirements.txt
    ```

> **Nota**: Este proyecto usa `google-generativeai`. Asegúrate de tener una API KEY válida configurada en `backend/gemini_service.py`.

## ⚡ Guía de Ejecución

Necesitas abrir **DOS terminales** separadas.

### 1️⃣ Terminal 1: Iniciar el Backend (API)
Aquí corre la lógica pesada.
```bash
cd backend
python main.py
```
*Espera a ver el mensaje: `Application startup complete`.*

### 2️⃣ Terminal 2: Iniciar el Frontend (Web)
Aquí interactúas con el programa.
```bash
streamlit run frontend/app.py
```
*Se abrirá tu navegador automáticamente en `http://localhost:8501`.*

## 🔍 Cómo Usar

1.  **Cargar**: Arrastra un PDF o una Foto al recuadro de carga.
    *   *Si es duplicado, el sistema te avisará inmediatamente.*
2.  **Analizar**: Haz clic en el botón azul.
    *   Verás la clasificación, el resumen y el texto extraído.
    *   Si es una imagen de un objeto, verás su identificación precisa.
3.  **Buscar**: Ve a la barra lateral izquierda "Búsqueda Semántica".
    *   Escribe algo complejo como *"¿Qué coche aparece en las fotos?"* o *"contratos mayores a 1000 pesos"*.
    *   El sistema leerá los documentos y te dará una respuesta razonada.

---
**Tecnologías**: Python, FastAPI, Streamlit, Google Gemini 2.5 Flash, FAISS, Sentence-Transformers.
