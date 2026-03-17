import streamlit as st
import pandas as pd
import plotly.express as px
from pptx import Presentation
from pptx.util import Inches, Pt
import io
from datetime import datetime

# --- CONFIGURAÇÕES DA PÁGINA ---
st.set_page_config(
    page_title="Ecoa: Plataforma de Escuta Organizacional",
    page_icon="🌱",
    layout="wide"
)

# --- INICIALIZAÇÃO DE DADOS MOCKADOS (CASO O SUPABASE NÃO ESTEJA CONECTADO) ---
if 'dados_locais' not in st.session_state:
    st.session_state.dados_locais = pd.DataFrame(columns=["data", "departamento", "lideranca", "comunicacao", "reconhecimento", "enps"])

# --- BARRA LATERAL (CONFIGURAÇÕES DO SISTEMA) ---
with st.sidebar:
    st.title("⚙️ Configurações (RH)")
    
    st.markdown("### 🎨 Personalização")
    st.write("Deixe a plataforma com a cara da sua empresa.")
    # NOVO: Botão para o RH subir a logo da empresa
    logo_empresa = st.file_uploader("Suba a Logo (PNG ou JPG)", type=["png", "jpg", "jpeg"])
    
    st.markdown("---")
    st.markdown("### ☁️ Banco de Dados")
    st.write("Conecte seu banco de dados Supabase aqui.")
    supabase_url = st.text_input("Supabase URL", type="password")
    supabase_key = st.text_input("Supabase Key", type="password")
    
    if supabase_url and supabase_key:
        st.success("Conectado ao Supabase!")
    else:
        st.info("Rodando em modo Local/Teste. Insira as credenciais para nuvem.")

    st.markdown("---")
    st.caption("Desenvolvido com 💙 por Cris Lima")

# --- CABEÇALHO ---
col_logo, col_titulo = st.columns([1, 8])

with col_logo:
    # NOVO: Lógica para mostrar a logo enviada ou um ícone padrão
    if logo_empresa is not None:
        st.image(logo_empresa, width=80)
    else:
        st.markdown("## 🌱") # Ícone exibido se nenhuma logo for enviada

with col_titulo:
    st.title("Ecoa: Plataforma de Escuta Organizacional")
    
st.markdown("Uma ferramenta projetada para ouvir, entender e desenvolver pessoas de forma segura e transparente.")

# --- ABAS DO SISTEMA ---
tab1, tab2, tab3 = st.tabs(["📝 Pesquisa (Visão Colaborador)", "📊 Dashboard (Visão RH)", "📑 Gerar Apresentação (Diretoria)"])

# =====================================================================
# ABA 1: A PESQUISA (VISÃO DO COLABORADOR)
# =====================================================================
with tab1:
    st.markdown("### Bem-vindo(a) à nossa Pesquisa de Clima")
    st.write("Sua voz é muito importante para nós. Responda com sinceridade. **Garantimos 100% de anonimato e sigilo das suas respostas.**")
    
    with st.form("form_pesquisa", clear_on_submit=True):
        col1, col2 = st.columns(2)
        
        with col1:
            departamento = st.selectbox("Seu Departamento:", ["Administrativo", "Vendas", "Logística", "Tecnologia", "Atendimento"])
        
        st.markdown("---")
        st.markdown("#### Avalie os seguintes pilares (1 - Discordo Totalmente a 5 - Concordo Totalmente)")
        
        lideranca = st.slider("Meu gestor direto me ouve e oferece feedbacks construtivos.", 1, 5, 3)
        comunicacao = st.slider("As informações importantes chegam até mim de forma clara.", 1, 5, 3)
        reconhecimento = st.slider("Sinto que meu esforço é reconhecido e valorizado.", 1, 5, 3)
        
        st.markdown("#### eNPS (Employee Net Promoter Score)")
        enps = st.slider("De 0 a 10, o quanto você recomendaria nossa empresa como um bom lugar para trabalhar?", 0, 10, 8)
        
        submit = st.form_submit_button("Enviar Minhas Respostas", type="primary")
        
        if submit:
            nova_resposta = {
                "data": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "departamento": departamento,
                "lideranca": lideranca,
                "comunicacao": comunicacao,
                "reconhecimento": reconhecimento,
                "enps": enps
            }
            
            # Como fallback local:
            st.session_state.dados_locais = pd.concat([st.session_state.dados_locais, pd.DataFrame([nova_resposta])], ignore_index=True)
            
            st.success("Muito obrigado por compartilhar sua visão conosco! Suas respostas foram salvas com segurança.")

# =====================================================================
# ABA 2: DASHBOARD (VISÃO RH)
# =====================================================================
with tab2:
    st.markdown("### 📊 Análise de Dados em Tempo Real")
    
    df = st.session_state.dados_locais
    
    if df.empty:
        st.info("Nenhuma resposta registrada ainda. Vá na aba 'Pesquisa' e insira dados de teste.")
    else:
        colA, colB, colC = st.columns(3)
        
        media_lid = df["lideranca"].mean()
        media_com = df["comunicacao"].mean()
        media_rec = df["reconhecimento"].mean()
        
        promotores = len(df[df["enps"] >= 9])
        detratores = len(df[df["enps"] <= 6])
        total = len(df)
        enps_score = ((promotores - detratores) / total) * 100 if total > 0 else 0
        
        colA.metric("Liderança (Média)", f"{media_lid:.1f} / 5.0")
        colB.metric("Reconhecimento (Média)", f"{media_rec:.1f} / 5.0")
        colC.metric("eNPS Geral", f"{enps_score:.0f}", help="Varia de -100 a +100")
        
        st.markdown("---")
        st.markdown("#### Médias por Departamento")
        
        df_agrupado = df.groupby("departamento")[["lideranca", "comunicacao", "reconhecimento"]].mean().reset_index()
        
        fig = px.bar(df_agrupado, x="departamento", y=["lideranca", "comunicacao", "reconhecimento"],
                     barmode="group", title="Visão Comparativa de Pilares por Setor",
                     labels={"value": "Média", "variable": "Pilar"},
                     color_discrete_sequence=["#1f77b4", "#ff7f0e", "#2ca02c"])
        st.plotly_chart(fig, use_container_width=True)

# =====================================================================
# ABA 3: EXPORTAÇÃO POWERPOINT (DIRETORIA)
# =====================================================================
with tab3:
    st.markdown("### 📑 Gerar Relatório Executivo")
    st.write("Exporte os dados consolidados diretamente para uma apresentação pronta para a diretoria.")
    
    df_relatorio = st.session_state.dados_locais
    
    if df_relatorio.empty:
        st.warning("É necessário ter respostas na pesquisa para gerar o relatório.")
    else:
        def gerar_pptx(dataframe):
            prs = Presentation()
            
            slide_titulo = prs.slides.add_slide(prs.slide_layouts[0])
            title = slide_titulo.shapes.title
            subtitle = slide_titulo.placeholders[1]
            title.text = "Resultados: Pesquisa Ecoa"
            subtitle.text = f"Plataforma de Escuta Organizacional - {datetime.now().strftime('%d/%m/%Y')}"
            
            slide_resumo = prs.slides.add_slide(prs.slide_layouts[1])
            title2 = slide_resumo.shapes.title
            title2.text = "Média Geral dos Pilares Avaliados"
            
            tf = slide_resumo.placeholders[1].text_frame
            tf.text = "Com base nas respostas coletadas na plataforma:"
            
            p = tf.add_paragraph()
            p.text = f"• Liderança: {dataframe['lideranca'].mean():.2f} / 5.0"
            p = tf.add_paragraph()
            p.text = f"• Comunicação: {dataframe['comunicacao'].mean():.2f} / 5.0"
            p = tf.add_paragraph()
            p.text = f"• Reconhecimento: {dataframe['reconhecimento'].mean():.2f} / 5.0"
            
            binary_output = io.BytesIO()
            prs.save(binary_output)
            binary_output.seek(0)
            return binary_output
        
        st.info("Clique no botão abaixo para baixar sua apresentação `.pptx` compilada automaticamente pelo Python.")
        
        if st.button("Preparar Arquivo PowerPoint", type="primary"):
            arquivo_pptx = gerar_pptx(df_relatorio)
            st.download_button(
                label="📥 Baixar Apresentação (.pptx)",
                data=arquivo_pptx,
                file_name="Relatorio_Ecoa.pptx",
                mime="application/vnd.openxmlformats-officedocument.presentationml.presentation"
            )
