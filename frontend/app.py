import streamlit as st
import requests
import os
import time
import pdfplumber
from PIL import Image

# URL de API Backend
API_URL = "http://localhost:8000"

st.set_page_config(
    page_title="Análisis Multimodal de Archivos",
    page_icon="🧠",
    layout="wide"
)

# CSS Personalizado para apariencia premium
st.markdown("""
<style>
    /* Modo Oscuro Global */
    .stApp {
        background-color: #0e1117;
        color: #fafafa;
    }
    .main {
        background-color: #0e1117;
    }
    /* Botones */
    .stButton>button {
        width: 100%;
        border-radius: 8px;
        height: 3em;
        background-color: #00D4FF; /* Neon Cyan for contrast */
        color: black;
        font-weight: bold;
        border: none;
        transition: all 0.3s ease;
    }
    .stButton>button:hover {
        background-color: #00a3cc;
        color: white;
        transform: scale(1.02);
        box-shadow: 0 4px 12px rgba(0, 212, 255, 0.4);
    }
    /* Tarjetas */
    .card {
        padding: 20px;
        background-color: #262730; /* Streamlit Dark Gray */
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.3);
        margin-bottom: 20px;
        color: #ffffff; /* Explicit White Text */
        border: 1px solid #41424C;
    }
    h3 {
        color: #00D4FF !important;
    }
    strong {
        color: #E0E0E0;
    }
    /* Ajustes de Título */
    .block-container {
        padding-top: 1rem;
        padding-bottom: 0rem;
    }
    h1 {
        margin-bottom: 2rem;
    }
    
    /* Animación del Botón de Carga de Archivos */
    [data-testid="stFileUploader"] button {
        transition: all 0.3s ease;
        border: 1px solid #41424C;
    }
    [data-testid="stFileUploader"] button:hover {
        transform: scale(1.05);
        border-color: #00D4FF !important;
        color: #00D4FF !important;
        box-shadow: 0 0 10px rgba(0, 212, 255, 0.2);
    }
</style>
""", unsafe_allow_html=True)

st.markdown("""
    <h1 style='display: flex; align-items: center; gap: 0px; margin-top: 20px;'>
        <div style='font-size: 1.2em; margin-right: 8px; margin-left: -5px;'>🧠</div> Análisis Multimodal de Archivos
    </h1>
""", unsafe_allow_html=True)
st.markdown("Sube **PDFs, Imágenes o Fotos** para que la IA los analice, clasifique y extraiga su información.")

# Barra lateral para Búsqueda e Historial
with st.sidebar:
    st.header("🔍 Búsqueda & Razonamiento")
    st.markdown("Haz preguntas complejas sobre tus archivos. La IA entiende el contexto visual y textual.")
    search_query = st.text_input("", placeholder="Ej: ¿Qué coche es rojo? o Busca facturas de >$100")
    st.caption("💡 Truco: Puedes buscar por conceptos visuales, valores numéricos o texto específico.")
    
    if st.button("Buscar"):
        if search_query:
            with st.spinner("Buscando..."):
                try:
                    res = requests.get(f"{API_URL}/search", params={"query": search_query})
                    if res.status_code == 200:
                        results = res.json()
                        st.session_state['search_results'] = results
                    else:
                        st.error("Error en la búsqueda")
                except Exception as e:
                    st.error(f"Error de conexión: {e}")

    # Mostrar Resultados de Búsqueda
    if 'search_results' in st.session_state:
        st.subheader("Resultados")
        results = st.session_state['search_results']
        if not results:
            st.info("No se encontraron coincidencias.")
        for item in results:
            meta = item['metadata']
            
            # Verificar Datos de Reranking IA
            if 'ai_score' in item:
                # Modo Rerank con Gemini
                score = item['ai_score']
                reasoning = item.get('ai_reasoning', '')
                
                quality = "Alta" if score > 0.8 else "Media" if score > 0.5 else "Baja"
                color = "green" if score > 0.8 else "orange" if score > 0.5 else "red"
                
                with st.expander(f"{meta['filename']} ({int(score*100)}%)"):
                    st.markdown(f"**Relevancia:** :{color}[{quality}]")
                    if reasoning:
                        st.info(f"💡 **Análisis:** {reasoning}")
                    st.caption(f"Categoría: {meta.get('category', 'N/A')}")
                    st.write(f"**Resumen:** {meta.get('summary', '')[:150]}...")
            
            else:
                # Modo Legado (Distancia L2)
                score = item['distance']
                # Interpretar puntuación (menor es mejor para L2)
                quality = "Alta" if score < 1.0 else "Media" if score < 1.4 else "Baja"
                color = "green" if score < 1.0 else "orange" if score < 1.4 else "red"
                
                with st.expander(f"{meta['filename']}"):
                    st.markdown(f"**Coincidencia Vectorial:** :{color}[{quality} ({int((2-min(score, 2))*50)}%)]")
                    st.caption(f"Categoría: {meta.get('category', 'N/A')}")
                    st.write(f"**Resumen:** {meta.get('summary', '')[:150]}...")

    st.markdown("---")
    st.header("📂 Historial")
    
    # Callback para Borrar Todo
    def delete_all_callback():
        try:
            res = requests.delete(f"{API_URL}/documents")
            if res.status_code == 200:
                 if 'search_results' in st.session_state:
                     del st.session_state['search_results']
                 st.toast("Historial borrado correctamente")
                 # No se necesita sleep para callback, toast usualmente sobrevive o aparece en la siguiente ejecución
            else:
                 st.error(f"Error: {res.text}")
        except Exception as e:
            st.error(f"Error de conexión: {e}")

    # Dialogo de confirmación usando st.dialog (Popup Modal)
    @st.dialog("⚠️ Confirmar Borrado")
    def open_delete_dialog():
        # CSS Hack para forzar el centrado vertical estricto del modal
        st.markdown(
            """
            <style>
            div[data-testid="stDialog"] > div:first-child {
                display: flex;
                align-items: center;
                justify-content: center;
                height: 100vh;
                margin: 0 !important;
            }
            div[data-testid="stDialog"] > div:first-child > div {
                margin-top: 0 !important;
                max-height: 80vh;
                overflow-y: auto;
            }
            </style>
            """,
            unsafe_allow_html=True
        )

        st.write("¿Estás seguro de que quieres borrar **TODO** el historial?")
        st.write("Esta acción no se puede deshacer.")
        
        col_d1, col_d2 = st.columns(2)
        with col_d1:
            if st.button("Sí, borrar todo", type="primary", use_container_width=True):
                delete_all_callback()
                st.rerun()
        with col_d2:
            if st.button("Cancelar", use_container_width=True):
                st.rerun()

    cols_container = st.container()
    with cols_container:
        if st.button("🗑️ Borrar Todo", type="primary", use_container_width=True):
            open_delete_dialog()
    
    # Esperar el siguiente ciclo de ejecución para actualizar UI (implícito en callback)

    # Obtener documentos
    try:
        res_docs = requests.get(f"{API_URL}/documents")
        if res_docs.status_code == 200:
            docs = res_docs.json()
            st.caption(f"Total: {len(docs)} documentos")
            
            if docs:
                # Mapa Nombre -> ID
                name_to_id = {d['filename']: d['id'] for d in docs}
                file_options = list(name_to_id.keys())
                
                # Lógica para limpiar selección después de borrar
                if 'deleted_files' not in st.session_state:
                    st.session_state['deleted_files'] = []

                # Filtrar opciones para excluir los conocidos como eliminados localmente (feedback visual)
                # Pero típicamente st.rerun() volverá a comprobar el backend.
                
                selected_filenames = st.multiselect(
                    "Seleccionar documentos para borrar:", 
                    file_options,
                    key="delete_multiselect"
                )
                
                if st.button("Borrar Seleccionados"):
                    if selected_filenames:
                        progress_bar = st.progress(0)
                        for i, name in enumerate(selected_filenames):
                           doc_id = name_to_id.get(name)
                           if doc_id:
                               try:
                                   res = requests.delete(f"{API_URL}/documents/{doc_id}")
                                   if res.status_code == 200:
                                       pass
                                   else:
                                       st.error(f"Error borrando {name}")
                               except Exception as e:
                                   st.error(f"Error de conexión: {e}")
                           
                           progress_bar.progress((i + 1) / len(selected_filenames))
                        
                        st.success(f"Proceso finalizado.")
                        time.sleep(1)
                        # Forzar reinicio del widget multiselect
                        if "delete_multiselect" in st.session_state:
                            del st.session_state["delete_multiselect"]
                        st.rerun()
                    else:
                        st.warning("Por favor, selecciona al menos un archivo.")
                
                # List details below
                with st.expander("Ver detalles de todos"):
                    for i, doc in enumerate(docs):
                        st.markdown(f"""
                        <div style="margin-bottom: 2px; font-weight: 600; display: flex; align-items: flex-start; gap: 6px;">
                            <span style="min-width: 1.2em;">📄</span>
                            <span style="word-break: break-word; line-height: 1.2;">{doc['filename']}</span>
                        </div>
                        <div style="font-size: 0.85em; color: #aaa; margin-bottom: 5px; display: flex; align-items: center; gap: 4px;">
                            <span style="position: relative; top: -2px;">📂</span> <span>{doc.get('category', 'N/A')}</span>
                        </div>
                        """, unsafe_allow_html=True)
                        st.info(doc.get('summary', 'Sin resumen disponible.'))
                        
                        # Only show separator if it's not the last item
                        if i < len(docs) - 1:
                            st.markdown("<hr style='margin: 5px 0; border-color: #41424C; opacity: 0.6;'>", unsafe_allow_html=True)
            else:
                st.info("El historial está vacío.")

        else:
            st.warning("No se pudo cargar el historial.")
    except Exception as e:
        st.warning(f"Error de conexión: {e}")

# Área Principal - Lado a Lado optimizado con gran espacio
col1, col2 = st.columns([1, 1], gap="large")

# Callback para limpiar resultados cuando cambia el archivo
def reset_analysis():
    if 'analysis_result' in st.session_state:
        del st.session_state['analysis_result']
    if 'chat_history' in st.session_state:
        del st.session_state['chat_history']
    if 'processed_files' in st.session_state:
        del st.session_state['processed_files']
    if 'batch_results' in st.session_state:
        del st.session_state['batch_results']


with col1:
    st.markdown("""
        <h3 style='display: flex; align-items: center; gap: 8px; margin-bottom: 5px;'>
            <div style='margin-left: -5px;'>📤</div> Cargar Documento(s)
        </h3>
    """, unsafe_allow_html=True)
    uploaded_files = st.file_uploader("Elige archivo(s) (PDF o Imagen)", type=["pdf", "png", "jpg", "jpeg", "webp"], accept_multiple_files=True, on_change=reset_analysis, key="main_file_uploader")

    if uploaded_files:
        # 1. MOSTRAR VISTA PREVIA (Detectar de la lista)
        # Mostrar carrusel/columnas de hasta 3
        st.caption(f"📑 Vista Previa de Selección ({len(uploaded_files)})")
        
        # Paginar vista previa si son muchos
        cols = st.columns(min(len(uploaded_files), 3))
        
        for i, file_obj in enumerate(uploaded_files[:3]):
             fname = file_obj.name.lower()
             ftype = file_obj.type
             
             with cols[i]:
                 if "image" in ftype or any(fname.endswith(ext) for ext in ['.png', '.jpg', '.jpeg', '.webp']):
                      st.image(file_obj, caption=file_obj.name, use_container_width=True)
                 elif "pdf" in ftype or fname.endswith('.pdf'):
                      try:
                          with pdfplumber.open(file_obj) as pdf:
                              if len(pdf.pages) > 0:
                                  im = pdf.pages[0].to_image(resolution=150).original
                                  st.image(im, caption=file_obj.name, use_container_width=True)
                      except:
                          st.caption(f"Previo no disponible: {file_obj.name}")
        
        if len(uploaded_files) > 3:
            st.caption(f"...y {len(uploaded_files)-3} más.")

        # 2. VALIDACIÓN DE DUPLICADOS STRICTA (Bloqueante)
        # Verificamos TODOS los archivos seleccionados. Si ALGUNO existe, mostramos error y bloqueamos.
        # EXCEPCIÓN: Si el archivo acaba de ser procesado (está en session_state), lo dejamos pasar para ver resultados.
        
        if 'processed_files' not in st.session_state:
            st.session_state['processed_files'] = set()

        try:
             doc_res = requests.get(f"{API_URL}/documents")
             if doc_res.status_code == 200:
                 existing_filenames = [d.get('filename') for d in doc_res.json()]
                 
                 # Solo consideramos duplicados aquellos que YA existían y NO son los que acabamos de subir con éxito
                 duplicates = []
                 for f in uploaded_files:
                     if f.name in existing_filenames:
                         if f.name not in st.session_state['processed_files']:
                             duplicates.append(f.name)
                 
                 if duplicates:
                    st.error(f"⚠️ Archivos duplicados detectados: {', '.join(duplicates)}")
                    st.warning("El sistema no permite subir archivos que ya existen. Elimínalos de la selección para continuar.")
                    st.stop() # DETENER EJECUCIÓN (Bloqueo real)
                 
                 # Si no hay duplicados bloqueantes, pero hay archivos en 'processed_files', mostramos éxito
                 processed_here = [f.name for f in uploaded_files if f.name in st.session_state['processed_files']]
                 if processed_here:
                     st.success(f"✅ Archivos procesados: {len(processed_here)}/{len(uploaded_files)}")
                     
        except Exception as e:
            # Si falla la conexión, no bloqueamos para no romper la UX
            print(f"Error checking duplicates: {e}")
            pass

        st.caption(f"{len(uploaded_files)} archivo(s) listo(s) para analizar")
        
        # Botón de Análisis Masivo - Solo mostrar si NO hay resultados aún
        if 'batch_results' not in st.session_state or not st.session_state['batch_results']:
            if st.button("Analizar Todo"):
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                # Inicializar set de procesados y lista de resultados
                if 'processed_files' not in st.session_state:
                    st.session_state['processed_files'] = set()
                if 'batch_results' not in st.session_state:
                    st.session_state['batch_results'] = []
                
                for i, uploaded_file in enumerate(uploaded_files):
                    status_text.text(f"Procesando {uploaded_file.name} ({i+1}/{len(uploaded_files)})...")
                    
                    # 2. Analyze
                    try:
                        uploaded_file.seek(0)
                        files = {"file": (uploaded_file.name, uploaded_file, uploaded_file.type)}
                        response = requests.post(f"{API_URL}/analyze", files=files)
                        
                        if response.status_code == 200:
                            data = response.json()
                            st.session_state['analysis_result'] = data # Legacy support for logic checks
                            st.session_state['batch_results'].append(data) # Agregando a lista
                            st.session_state['processed_files'].add(uploaded_file.name) # MARCAR COMO PROCESADO
                        else:
                            st.error(f"Error en {uploaded_file.name}: {response.text}")
                    except Exception as e:
                        st.error(f"Error conectando: {e}")
                    
                    progress_bar.progress((i + 1) / len(uploaded_files))
                
                status_text.text("¡Proceso completado!")
                time.sleep(1)
                st.rerun()

    # Vista previa del ÚLTIMO archivo cargado o seleccionado (para mantener UI limpia)
    # Si hay results, mostramos info del result. Si no, mostramos preview del primer archivo subido.
    if uploaded_files and len(uploaded_files) == 1:
        # Legacy single file preview logic
        uploaded_file = uploaded_files[0]
        # (Mantener lógica de preview visual aquí si se quiere, simplificado para batch)
        # ... (Omitido para brevedad en batch, pero idealment mostrar preview simple)


with col2:
    st.subheader("📊 Resultados del Análisis")
    
    # Usar batch_results si existe, si no fallback a single 'analysis_result' convertido a lista
    results_to_show = []
    if 'batch_results' in st.session_state and st.session_state['batch_results']:
        results_to_show = st.session_state['batch_results']
    elif 'analysis_result' in st.session_state:
        results_to_show = [st.session_state['analysis_result']]
        
    if results_to_show:
        for idx, res in enumerate(results_to_show):
            doc_filename = res.get('filename', f'Documento {idx+1}')
            
            # Contenedor Visual Distinto por Documento
            with st.container():
                st.markdown(f"#### 📄 {doc_filename}")
                
                if 'error' in res:
                    st.error(f"Error: {res['error']}")
                else:
                    category = res.get('category', 'N/A')
                    confidence = res.get('category_score', 0)
                    summary_text = res.get('summary')
                    full_text = res.get('full_text') or res.get('text_preview', '')
                    
                    # Layout Compacto
                    c1, c2 = st.columns([1, 2])
                    with c1:
                        st.info(f"**Categoría**: {category}\n\n(Confianza: {confidence*100:.0f}%)")
                    with c2:
                        st.write(f"**Resumen**: {summary_text[:300]}..." if len(summary_text)>300 else f"**Resumen**: {summary_text}")
                        # Expandir resumen completo si es largo
                        if len(summary_text) > 300:
                            with st.expander("Leer resumen completo"):
                                st.write(summary_text)

                    # Acciones
                    ac1, ac2, ac3 = st.columns(3)
                    
                    with ac1:
                        # AUDIO PLAYER unique key per doc
                        if st.button("🔊 Escuchar", key=f"btn_audio_{idx}"):
                             with st.spinner("Generando audio..."):
                                 try:
                                     ares = requests.post(f"{API_URL}/generate_audio", json={"text": summary_text})
                                     if ares.status_code == 200:
                                         apath = ares.json().get('audio_path')
                                         st.audio(apath)
                                     else:
                                         st.error("Error audio")
                                 except:
                                     st.error("Error conexión")

                    with ac2:
                        st.download_button("💾 Texto", data=full_text, file_name=f"{doc_filename}.txt", key=f"btn_dl_{idx}")
                    
                    with ac3:
                        with st.popover("💬 Chat"):
                             st.markdown(f"**Chat con {doc_filename}**")
                             # Mini Chat contextual
                             # Necesitamos ID real
                             real_id = None
                             try:
                                 # Optimización: No llamar a API por cada doc en loop si son muchos.
                                 # Pero por ahora ok.
                                 docs_check = requests.get(f"{API_URL}/documents").json()
                                 for d in docs_check:
                                     if d['filename'] == res.get('filename'):
                                         real_id = d['id']
                                         break
                             except: pass
                             
                             if real_id:
                                 q = st.text_input("Pregunta:", key=f"chat_input_{idx}")
                                 if q:
                                     with st.spinner("Pensando..."):
                                         cres = requests.post(f"{API_URL}/chat_document", json={"doc_id": real_id, "query": q})
                                         if cres.status_code == 200:
                                             st.markdown(cres.json().get('answer'))
                                         else:
                                             st.error("Error")
                             else:
                                 st.warning("ID no encontrado para chat")

                    # Vista de Texto Completo con Tabs
                    with st.expander("Ver texto extraído completo"):
                        tab1, tab2 = st.tabs(["👀 Vista Renderizada", "📝 Código Markdown"])
                        with tab1:
                            st.markdown(full_text)
                        with tab2:
                            st.text_area("Copiar Texto:", value=full_text, height=300, key=f"text_area_{idx}")

                    st.markdown("---")

    else:
        st.info("Sube y analiza documentos para interactuar con ellos.")
