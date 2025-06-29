import streamlit as st
import requests
import re
import yaml
import pandas as pd
from yaml.loader import SafeLoader
import streamlit_authenticator as stauth

# --- Configuração da Página ---
st.set_page_config(page_title="GlobalD AI Optimizer", layout="wide")

# --- URL da API do Backend ---
try:
    BACKEND_URL = st.secrets["BACKEND_URL"]
except (FileNotFoundError, KeyError):
    BACKEND_URL = "https://globald-api.onrender.com/generate-content"

# --- Funções Auxiliares ---
def get_asin_from_url(url: str) -> str:
    """Extrai o ASIN de uma URL da Amazon."""
    match = re.search(r'/(dp|gp/product)/([A-Z0-9]{10})', url)
    return match.group(2) if match else ""

def render_export_buttons():
    """Renderiza os botões de download para os resultados gerados."""
    st.markdown("---")
    st.subheader("⬇️ Exportar Resultados")
    if 'export_data' in st.session_state and st.session_state.export_data:
        df = pd.DataFrame(st.session_state.export_data)
        csv_data = df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Baixar como CSV",
            data=csv_data,
            file_name="report_globald.csv",
            mime="text/csv",
            use_container_width=True
        )
    else:
        st.info("Gere um conteúdo primeiro para habilitar a exportação.")

# --- Lógica de Autenticação e Interface ---
try:
    with open('globald/config.yaml') as file:
        config = yaml.load(file, Loader=SafeLoader)
    authenticator = stauth.Authenticate(
        config['credentials'],
        config['cookie']['name'],
        config['cookie']['key'],
        config['cookie']['expiry_days']
    )
    authenticator.login()
except FileNotFoundError:
    st.error("Arquivo de configuração 'globald/config.yaml' não encontrado. Verifique a estrutura do seu projeto.")
    st.stop()

if st.session_state.get("authentication_status"):
    # --- APLICAÇÃO PRINCIPAL (APÓS LOGIN) ---
    with st.sidebar:
        st.subheader(f'Bem-vindo(a), *{st.session_state["name"]}*')
        authenticator.logout('Logout', 'main')
        st.markdown("---")
        try:
            st.image("globald/static/img/globald2.png")
        except FileNotFoundError:
            st.warning("Arquivo de logo não encontrado.")

    st.title("🚀 AI Product Listing Optimizer")
    st.markdown("Otimize títulos, descrições e mais, usando IA e as melhores práticas de SEO da Amazon.")

    with st.form("content_form"):
        st.markdown("##### 1. Insira o ASIN ou a URL do produto Amazon")
        product_input = st.text_input("ASIN ou URL", label_visibility="collapsed", placeholder="Ex: B08L6XYZ12 ou https://www.amazon.com/dp/B08L6XYZ12")

        st.markdown("##### 2. Configure as Opções de Geração")
        col1, col2 = st.columns(2)
        output_language = col1.selectbox("Idioma de Saída:", ("Portuguese", "English", "Spanish"))
        selected_llm_model = col2.selectbox("Modelo de IA:", ("gpt-4o", "gpt-4-turbo", "gpt-3.5-turbo"))

        st.markdown("##### 3. Selecione os Tipos de Conteúdo")
        c1, c2, c3, c4 = st.columns(4)
        gen_title = c1.checkbox("Título", value=True)
        gen_about = c2.checkbox("Descrição", value=True)
        gen_bullets = c3.checkbox("Features", value=True)
        gen_aplus = c4.checkbox("Conteúdo A+")
        
        submitted = st.form_submit_button("✨ Gerar Conteúdo com IA", use_container_width=True)

    if submitted and product_input:
        asin = get_asin_from_url(product_input) if product_input.startswith("http") else product_input
        if not (len(asin) == 10 and asin.isalnum()):
            st.error("Entrada inválida. Por favor, insira um ASIN ou URL de produto da Amazon válido.")
        else:
            with st.spinner("🔍 Analisando produto e gerando conteúdo com IA... Isso pode levar um momento."):
                try:
                    content_types = [name for name, checked in [("title", gen_title), ("about_product", gen_about), ("feature_bullets", gen_bullets), ("aplus_content", gen_aplus)] if checked]
                    if not content_types:
                        st.warning("Por favor, selecione pelo menos um tipo de conteúdo para gerar.")
                        st.stop()

                    payload = {"asin": asin, "output_language": output_language, "content_types": content_types, "llm_model": selected_llm_model}
                    
                    response = requests.post(BACKEND_URL, json=payload, timeout=300)
                    response.raise_for_status()
                    data = response.json()
                    
                    st.success("Conteúdo gerado com sucesso!")
                    st.markdown("---")

                    original = data['original_content']
                    generated = data['generated_content']
                    st.session_state.export_data = []

                    # --- LÓGICA DE EXIBIÇÃO DE RESULTADOS LADO A LADO ---
                    if "title" in generated:
                        st.subheader("Comparativo de Título")
                        col1, col2 = st.columns(2)
                        col1.markdown("**Original:**"); col1.info(original.get('product_title'))
                        col2.markdown("**Gerado pela IA:**"); col2.success(generated.get('title'))
                        st.session_state.export_data.append({"content_type": "Title", "original": original.get('product_title'), "generated": generated.get('title')})

                    if "about_product" in generated:
                        st.subheader("Comparativo de Descrição")
                        col1, col2 = st.columns(2)
                        col1.markdown("**Original:**"); col1.info(original.get('product_description'))
                        col2.markdown("**Gerado pela IA:**"); col2.success(generated.get('about_product'))
                        st.session_state.export_data.append({"content_type": "Description", "original": original.get('product_description'), "generated": generated.get('about_product')})

                    if "feature_bullets" in generated:
                        st.subheader("Comparativo de Features (Bullet Points)")
                        col1, col2 = st.columns(2)
                        col1.markdown("**Original:**"); col1.info(original.get('about_product'))
                        col2.markdown("**Gerado pela IA:**"); col2.success(generated.get('feature_bullets'))
                        st.session_state.export_data.append({"content_type": "Features", "original": original.get('about_product'), "generated": generated.get('feature_bullets')})

                    if "aplus_content" in generated:
                        st.subheader("Conteúdo A+ Gerado pela IA")
                        st.success(generated.get('aplus_content'))
                        st.session_state.export_data.append({"content_type": "A+ Content", "original": "N/A", "generated": generated.get('aplus_content')})

                    if data.get('product_photos'):
                        st.subheader("Imagens do Produto")
                        st.image(data['product_photos'], width=150)

                    render_export_buttons()

                except requests.exceptions.HTTPError as e:
                    st.error(f"Ocorreu um erro na API: {e.response.json().get('detail', e)}")
                except Exception as e:
                    st.error(f"Ocorreu um erro inesperado: {e}")

elif st.session_state.get("authentication_status") is False:
    st.error('Usuário/senha incorreto.')
elif st.session_state.get("authentication_status") is None:
    st.warning('Por favor, insira seu usuário e senha.')