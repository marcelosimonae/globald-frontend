import streamlit as st
import pandas as pd

def render_export_buttons():
    """
    Renderiza os botões de download para os resultados gerados,
    lendo os dados do st.session_state.
    """
    st.markdown("---")
    st.subheader("⬇️ Exportar Resultados")

    # Verifica se há resultados para exportar no estado da sessão
    if 'search_results' in st.session_state and st.session_state.search_results:
        
        # Cria um DataFrame com os resultados para facilitar a exportação
        df = pd.DataFrame(st.session_state.search_results)

        # Prepara os dados para download em CSV
        csv_data = df.to_csv(index=False).encode('utf-8')

        # Prepara os dados para download em TXT
        txt_lines = []
        for item in st.session_state.search_results:
            txt_lines.append(f"--- TIPO DE CONTEÚDO: {item['content_type']} ---")
            txt_lines.append("\n[ORIGINAL]\n")
            txt_lines.append(str(item['original']))
            txt_lines.append("\n\n[GERADO PELA IA]\n")
            txt_lines.append(str(item['generated']))
            txt_lines.append("\n" + "="*50 + "\n")
        
        txt_data = "\n".join(txt_lines)

        # Exibe os botões de download lado a lado
        col1, col2 = st.columns(2)
        with col1:
            st.download_button(
                label="📥 Baixar como CSV",
                data=csv_data,
                file_name="report_globald.csv",
                mime="text/csv",
            )
        with col2:
            st.download_button(
                label="📄 Baixar como TXT",
                data=txt_data,
                file_name="report_globald.txt",
                mime="text/plain",
            )
    else:
        st.info("Gere um conteúdo primeiro para habilitar a exportação.")