import streamlit as st
import requests
import os
import time

# Backend API URL
API_URL = "http://localhost:8000"

st.set_page_config(
    page_title="Análisis Inteligente de Documentos",
    page_icon="📄",
    layout="wide"
)

# Custom CSS for a premium look
st.markdown("""
<style>
    /* Dark Mode Global */
    .stApp {
        background-color: #0e1117;
        color: #fafafa;
    }
    .main {
        background-color: #0e1117;
    }
    /* Buttons */
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
    /* Cards */
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
    /* Title Adjustments */
    .block-container {
        padding-top: 1rem;
        padding-bottom: 0rem;
    }
    h1 {
        margin-bottom: 2rem;
    }
    
    /* File Uploader Button Animation */
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

st.title("Análisis Inteligente de Documentos")
st.markdown("Sube tus documentos (PDF) para análisis automático, resumen y clasificación.")

# Sidebar for Search and History
with st.sidebar:
    st.header("🔍 Búsqueda Semántica")
    st.markdown("Buscar en documentos analizados...")
    search_query = st.text_input("", placeholder="Ej: contrato, factura...")
    
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

    # Display Search Results
    if 'search_results' in st.session_state:
        st.subheader("Resultados")
        results = st.session_state['search_results']
        if not results:
            st.info("No se encontraron coincidencias.")
        for item in results:
            meta = item['metadata']
            score = item['distance']
            
            # Interpret score (lower is better for L2)
            quality = "Alta" if score < 1.0 else "Media" if score < 1.4 else "Baja"
            color = "green" if score < 1.0 else "orange" if score < 1.4 else "red"
            
            with st.expander(f"{meta['filename']}"):
                st.markdown(f"**Coincidencia:** :{color}[{quality} ({int((2-min(score, 2))*50)}%)]")
                st.caption(f"Categoría: {meta.get('category', 'N/A')}")
                st.write(f"**Resumen:** {meta.get('summary', '')[:150]}...")

    st.markdown("---")
    st.header("📂 Historial")
    
    col_hist1, col_hist2 = st.columns([1,1])
    with col_hist1:
        if st.button("🔄 Actualizar"):
             st.rerun()
    with col_hist2:
        if st.button("🗑️ Borrar Todo", type="primary"):
            try:
                res = requests.delete(f"{API_URL}/documents")
                if res.status_code == 200:
                     st.session_state['search_results'] = [] # Clear local results
                     st.rerun()
                else:
                     st.error(f"Error: {res.text}")
            except Exception as e:
                # Ignore rerun exception if it happens to be caught, although specifically Exception shouldn't catch BaseException (which RerunException is).
                # But safer to just print e
                st.error(f"Error de conexión: {e}")

    # Fetch docs
    try:
        res_docs = requests.get(f"{API_URL}/documents")
        if res_docs.status_code == 200:
            docs = res_docs.json()
            st.caption(f"Total: {len(docs)} documentos")
            
            if docs:
                # Map Name -> ID
                name_to_id = {d['filename']: d['id'] for d in docs}
                file_options = list(name_to_id.keys())
                
                # Logic to clear selection after delete
                if 'deleted_files' not in st.session_state:
                    st.session_state['deleted_files'] = []

                # Filter options to exclude locally known deleted ones (visual feedback)
                # But typically st.rerun() will recheck backend.
                
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
                        # Force reset of multiselect widget
                        if "delete_multiselect" in st.session_state:
                            del st.session_state["delete_multiselect"]
                        st.rerun()
                    else:
                        st.warning("Por favor, selecciona al menos un archivo.")
                
                # List details below
                with st.expander("Ver detalles de todos"):
                    for doc in docs:
                         st.caption(f"📄 {doc['filename']} ({doc.get('category', 'N/A')})")
            else:
                st.info("El historial está vacío.")

        else:
            st.warning("No se pudo cargar el historial.")
    except Exception as e:
        st.warning(f"Error de conexión: {e}")

# Main Area - Side-by-Side optimized with large gap
col1, col2 = st.columns([1, 1], gap="large")

# Callback to clear results when file changes
def reset_analysis():
    if 'analysis_result' in st.session_state:
        del st.session_state['analysis_result']

with col1:
    st.subheader("📤 Cargar Documento")
    uploaded_file = st.file_uploader("Elige un archivo PDF", type="pdf", on_change=reset_analysis)

    if uploaded_file is None and 'analysis_result' in st.session_state:
        del st.session_state['analysis_result']

    if uploaded_file is not None:
        if st.button("Analizar Documento"):
            with st.spinner("Procesando documento (Extrayendo, Clasificando, Resumiendo)..."):
                try:
                    files = {"file": (uploaded_file.name, uploaded_file, "application/pdf")}
                    response = requests.post(f"{API_URL}/analyze", files=files)
                    
                    if response.status_code == 200:
                        data = response.json()
                        st.session_state['analysis_result'] = data
                        st.success("¡Análisis Completado!")
                    else:
                        st.error(f"Falló el análisis: {response.text}")
                except Exception as e:
                    st.error(f"Error conectando al backend: {e}")

with col2:
    st.subheader("📊 Resultados del Análisis")
    if 'analysis_result' in st.session_state:
        res = st.session_state['analysis_result']
        
        if 'error' in res:
            st.error(f"Error: {res['error']}")
        else:
            category_score = res.get('category_score', 0)
            category_name = res.get('category', 'Desconocido').upper()
            

            with st.expander("Clasificación IA", expanded=True):
                 st.info(f"Categoría: **{res.get('category')}** (Confianza: {res.get('category_score', 0)*100:.1f}%)")
            
            st.success("Resumen Generado:")
            st.write(res.get('summary'))
            
            with st.expander("Ver texto extraído completo"):
                full_text = res.get('full_text') or res.get('text_preview', '')
                
                tab1, tab2 = st.tabs(["👀 Vista Renderizada", "📝 Código Markdown"])
                
                with tab1:
                    st.info("Aquí ves las tablas y títulos con formato bonito.")
                    st.markdown(full_text)
                    
                with tab2:
                    st.text_area("Copiar Texto:", value=full_text, height=300)

    else:
        st.info("Sube y analiza un documento para ver los resultados aquí.")
