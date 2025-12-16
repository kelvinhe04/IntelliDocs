# Análisis Inteligente de Documentos Multimodal (Gemini 2.5 Flash)

Este sistema es una solución de vanguardia para el análisis de documentos e imágenes. Utiliza el modelo **Gemini 2.5 Flash** de Google para procesar PDFs y fotos, extrayendo información con precisión humana, identificando objetos visuales (Modo Lens) y permitiendo búsquedas semánticas con razonamiento profundo.

## 🚀 Características Principales (Base)

*   **Análisis Multimodal**: Sube **PDFs** (nativos o escaneados) o **Imágenes** (JPG, PNG, WEBP). El sistema lee todo.
*   **Visual Search (Modo Lens)**: Si subes la foto de un coche, producto o lugar, el sistema usa el vasto conocimiento multimodal de **Gemini** para identificar la Marca, Modelo y detalles visuales sin necesidad de OCR tradicional.
*   **Búsqueda Semántica con Razonamiento**: No busca solo por palabras clave.
    *   *Ejemplo*: Si buscas "documentos de deuda", el sistema lee el contenido real y te explica: *"💡 Análisis: Este documento es relevante porque contiene una tabla de amortización..."*.
    *   **Full Context**: Lee el documento completo (50k+ caracteres), no solo resúmenes, para encontrar detalles ocultos.
*   **Prevención de Duplicados**: Sistema inteligente que bloquea la subida de archivos ya existentes para mantener limpia tu base de datos.
*   **Clasificación Dinámica**: No usa categorías fijas. El modelo determina profesionalmente de qué trata el documento (ej: "Factura Electrónica", "Contrato de Arrendamiento").

## 🏆 Mejoras Hackathon (Nuevas Funcionalidades)

Estas son las mejoras "exponenciales" implementadas específicamente para el evento:

1.  **Carga por Lotes (Batch Upload)**:
    *   Ahora puedes arrastrar **múltiples archivos** a la vez. El sistema los procesará en cola automáticamente.
2.  **Chat con tu Documento**:
    *   Rompe la barrera estática. Después del análisis, apareció un chat interactivo para hacer preguntas específicas sobre el documento (ej: *"¿Cuánto es el total de la factura?"*).
    *   *Tecnología*: Usa la ventana de contexto de Gemini para leer el documento entero en cada pregunta.
3.  **Resumen de Audio (Text-to-Speech)**:
    *   Accesibilidad total. Un nuevo botón permite **escuchar** el análisis generado por la IA.
    *   *Ideal para*: Revisión rápida de documentos mientras haces otras tareas.
4.  **Comparador Inteligente (Cross-Document)**:
    *   ¿Indeciso entre dos contratos? Selecciónalos y la IA generará una **Tabla Comparativa** detallada con diferencias, similitudes y un veredicto final.
    *   *Capacidad*: Analiza múltiples documentos simultáneamente para encontrar discrepancias críticas.
5.  **Exportación a Excel (Reportes)**:
    *   Convierte el análisis comparativo de la IA en datos duros. Un botón genera automáticamente un archivo `.xlsx` listo para descargar.
    *   *Uso Real*: Convierte texto no estructurado (PDFs) en hojas de cálculo estructuradas para auditores.
6.  **Interfaz Premium (UI Polish)**:
    *   Rediseño completo visual. Iconografía vectorial (FontAwesome), paleta de colores coherente y eliminación de "emojis de juguete" para una apariencia 100% corporativa.
    *   *Layout*: Vista previa inteligente que se adapta (1/3 de pantalla) para no saturar la vista.

## 📂 Estructura del Proyecto

```
/
├── backend/                # El "Cerebro" del sistema
│   ├── main.py             # API Principal (FastAPI)
│   ├── gemini_service.py   # Integración Gemini (Vision + Search)
│   ├── vector_store.py     # Base de datos vectorial (FAISS)
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

## 🛠️ Instalación y Configuración
> **¡Importante!** Sigue estos pasos para aislar el proyecto y que todo funcione perfecto.

### 1️⃣ Crear el Entorno Virtual (La "Burbuja")
Esto crea una carpeta `.venv` donde vivirán las librerías del proyecto.

```bash
# En la carpeta raíz del proyecto:
python -m venv .venv
```

### 2️⃣ Activar el Entorno
Dependiendo de qué terminal uses, el comando varía:

*   **PowerShell (Windows / VS Code por defecto):**
    ```powershell
    .\.venv\Scripts\activate
    ```
*   **Git Bash / Linux / Mac:**
    ```bash
    source .venv/Scripts/activate
    ```
*(Sabrás que funcionó porque verás `(.venv)` en verde al inicio de tu línea de comandos).*

### 3️⃣ Instalar Dependencias
Una vez activado el entorno, instala todo lo necesario de una sola vez:
```bash
pip install -r backend/requirements.txt
```

### 4️⃣ Configurar la Clave Secreta (API Key)
Este proyecto necesita una llave de Google Gemini para funcionar.
1.  **Obtén tu API KEY gratis aquí:** [Google AI Studio](https://aistudio.google.com/app/apikey)
2.  Copia el archivo de ejemplo:
    *   Renombra `.env.example` a `.env` (o crea uno nuevo llamado `.env`).
3.  Edítalo y pega tu clave real:
    ```env
    GEMINI_API_KEY=Tu_Clave_Secreta_Aqui
    ```
*(El archivo `.env` es ignorado por Git para proteger tu seguridad).*

---

## ⚡ Guía de Ejecución

Debes abrir **DOS terminales** (y activar el entorno `.venv` en AMBAS).

### Terminal 1: Iniciar el Backend (Cerebro)
```bash
python backend/main.py
```
*Espera a ver: `Application startup complete`.*

### Terminal 2: Iniciar el Frontend (Interfaz)
```bash
streamlit run frontend/app.py
```
*Tu navegador se abrirá automáticamente en `http://localhost:8501`.*

## 🔍 Cómo Usar

1.  **Carga Inteligente (Batch)**:
    *   Arrastra uno o **múltiples archivos** al área de carga.
    *   *Seguridad*: El sistema detecta y bloquea duplicados automáticamente.
2.  **Análisis & Interacción**:
    *   Presiona **"Analizar Todo"** para procesar la cola.
    *   Explora las tarjetas de resultados: **Escucha el resumen** (🔊), **Chatea** con el documento (💬) o descarga el **Texto** (💾).
3.  **Comparación & Exportación** (Premium):
    *   En la barra lateral, ve a **Comparador Inteligente**.
    *   Selecciona 2 o más documentos de la lista.
    *   Clic en **Comparar Selección** para ver la tabla de diferencias generada por IA.
    *    **¡NUEVO!**: Presiona **"📥 Preparar Excel"** para descargar un reporte profesional editable.
4.  **Búsqueda Profunda**:
    *   Usa la barra lateral **"Búsqueda & Razonamiento"**.
    *   Pregunta en lenguaje natural (ej: *"¿Qué facturas vencen en diciembre?"*).

---
**Tecnologías**: Python, FastAPI, Streamlit, Google Gemini 2.5 Flash, FAISS, Sentence-Transformers, Pandas, OpenPyXL.
