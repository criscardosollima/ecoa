import streamlit as st
import pandas as pd
import plotly.express as px
from pptx import Presentation
from pptx.util import Inches, Pt
import io
from datetime import datetime, timedelta
from supabase import create_client, Client

# --- CONFIGURAÇÕES DA PÁGINA ---
st.set_page_config(
    page_title="Ecoa: Escuta Organizacional",
    page_icon="🌱",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- ESTILIZAÇÃO CSS AVANÇADA (LAYOUT MODERNO E PREMIUM) ---
st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

        html, body, [class*="css"] {
            font-family: 'Inter', sans-serif;
            color: #1e293b;
        }

        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        header {visibility: hidden;}
        
        .block-container {
            padding-top: 2rem;
            padding-bottom: 2rem;
            max-width: 1200px;
        }

        [data-testid="stSidebar"] {
            background-color: #f8fafc;
            border-right: 1px solid #e2e8f0;
        }
        
        div.stRadio > div {
            gap: 8px;
        }
        
        div.stRadio label {
            background-color: transparent;
            border-radius: 8px;
            padding: 10px 15px;
            transition: all 0.2s ease;
            border: 1px solid transparent;
            cursor: pointer;
            width: 100%;
        }

        div.stRadio label:hover {
            background-color: #f1f5f9;
            border-color: #e2e8f0;
        }

        div.stRadio label[data-selected="true"] {
            background-color: #eff6ff !important;
            border-color: #bfdbfe !important;
            color: #1e40af !important;
            font-weight: 600;
        }

        .stButton>button {
            border-radius: 8px;
            font-weight: 600;
            padding: 0.6rem 1.2rem;
            transition: all 0.3s;
        }

        .pilar-container {
            background-color: #ffffff;
            padding: 1.5rem;
            border-radius: 12px;
            border-left: 5px solid #1e3a8a;
            margin-bottom: 2rem;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        }
    </style>
""", unsafe_allow_html=True)

# --- CONEXÃO AUTOMÁTICA COM O SUPABASE ---
@st.cache_resource
def init_connection():
    try:
        # Busca as credenciais de forma segura nos Secrets do Streamlit Cloud
        url = st.secrets["SUPABASE_URL"]
        key = st.secrets["SUPABASE_KEY"]
        return create_client(url, key)
    except Exception:
        # Fallback caso os segredos não estejam configurados ainda
        return None

supabase = init_connection()

# --- INICIALIZAÇÃO DE ESTADOS ---
if 'autenticado' not in st.session_state:
    st.session_state.autenticado = False

if 'usuario_logado' not in st.session_state:
    st.session_state.usuario_logado = None

if 'usuarios' not in st.session_state:
    st.session_state.usuarios = pd.DataFrame({
        "Nome": ["Cris Lima", "Juliana", "Analista RH"],
        "E-mail": ["cris@ecoa.app", "ju@ecoa.app", "rh@empresa.com"],
        "Palavra-passe": ["admin123", "senha456", "cliente789"],
        "Perfil": ["Admin Master", "Analista RH", "Cliente (Leitura)"],
        "Qtd. Links": [10000, 2000, 500],
        "Status": ["Ativo", "Ativo", "Ativo"]
    })

# BANCO DE PERGUNTAS (35 QUESTÕES VALIDADAS)
if 'perguntas' not in st.session_state:
    st.session_state.perguntas = pd.DataFrame({
        "Ativa": [True] * 35,
        "Pilar Estratégico": [
            "Liderança & Gestão", "Liderança & Gestão", "Liderança & Gestão", "Liderança & Gestão", "Liderança & Gestão",
            "Segurança Psicológica", "Segurança Psicológica", "Segurança Psicológica", "Segurança Psicológica",
            "Bem-estar & Saúde Mental", "Bem-estar & Saúde Mental", "Bem-estar & Saúde Mental", "Bem-estar & Saúde Mental",
            "Reconhecimento & Valorização", "Reconhecimento & Valorização", "Reconhecimento & Valorização",
            "Desenvolvimento & Crescimento", "Desenvolvimento & Crescimento", "Desenvolvimento & Crescimento",
            "Comunicação & Transparência", "Comunicação & Transparência", "Comunicação & Transparência",
            "Diversidade & Inclusão", "Diversidade & Inclusão", "Diversidade & Inclusão",
            "Propósito & Orgulho", "Propósito & Orgulho", "Propósito & Orgulho",
            "Relacionamento Interpessoal", "Relacionamento Interpessoal", "Relacionamento Interpessoal",
            "Autonomia & Empoderamento", "Autonomia & Empoderamento",
            "Infraestrutura & Ferramentas", "eNPS"
        ],
        "Texto da Pergunta": [
            "O meu gestor direto estabelece expectativas claras sobre as minhas responsabilidades.",
            "Recebo feedback regular que me ajuda a evoluir no meu desempenho profissional.",
            "Sinto que o meu gestor se importa genuinamente comigo enquanto pessoa.",
            "A liderança da empresa age de forma coerente com os valores que promove.",
            "Confio na capacidade técnica e estratégica dos líderes da minha área.",
            "Nesta equipa, sinto-me seguro para assumir riscos sem receio de retaliação.",
            "Sinto-me à vontade para trazer problemas difíceis e erros à discussão sem julgamentos.",
            "As minhas competências e talentos únicos são valorizados e utilizados pela equipa.",
            "É fácil pedir ajuda aos meus colegas ou gestor quando encontro dificuldades.",
            "A organização incentiva e respeita o equilíbrio entre a minha vida pessoal e profissional.",
            "O volume de trabalho é equilibrado e não prejudica a minha saúde mental.",
            "Sinto que tenho apoio da empresa quando passo por momentos de elevado stress.",
            "A empresa promove iniciativas reais de cuidado com o bem-estar dos colaboradores.",
            "Recebi um elogio ou reconhecimento genuíno pelo meu trabalho nos últimos 7 dias.",
            "Acredito que os critérios para promoções e aumentos são justos e transparentes.",
            "Sinto-me valorizado pelos resultados que entrego à organização.",
            "Tenho oportunidades reais de aprender e crescer profissionalmente neste último ano.",
            "Existe alguém na empresa que incentiva ativamente o meu desenvolvimento.",
            "Vejo um caminho claro de evolução na carreira dentro desta organização.",
            "A liderança mantém-me informado sobre as decisões estratégicas da empresa.",
            "Sinto que os canais de comunicação interna funcionam de forma eficiente.",
            "Existe transparência sobre os sucessos e também sobre os desafios da empresa.",
            "Pessoas de todos os perfis têm as mesmas oportunidades de crescimento aqui.",
            "Sinto que posso ser eu próprio no trabalho sem precisar de 'máscaras'.",
            "A empresa combate activamente qualquer forma de discriminação ou exclusão.",
            "O propósito e a missão da empresa fazem-me sentir que o meu trabalho é importante.",
            "Tenho muito orgulho em dizer a outras pessoas que trabalho nesta organização.",
            "Sinto-me conectado com a cultura e com os valores praticados na empresa.",
            "Existe um forte espírito de colaboração e entreajuda entre os membros da equipa.",
            "Tenho um 'melhor amigo' ou relações de confiança profunda no ambiente de trabalho.",
            "Os conflitos na equipa são resolvidos de forma madura e construtiva.",
            "Tenho autonomia para decidir como realizar o meu trabalho da melhor forma.",
            "Sinto que a empresa confia na minha capacidade de tomar decisões importantes.",
            "Tenho acesso a todas as ferramentas e informações necessárias para ser excelente.",
            "Numa escala de 0 a 10, recomendaria esta empresa como um excelente lugar para trabalhar?"
        ]
    })

if 'empresa_atual' not in st.session_state:
    st.session_state.empresa_atual = "Sua Empresa"

if 'data_validade' not in st.session_state:
    st.session_state.data_validade = datetime.today().date() + timedelta(days=15)

if 'mensagem_padrao' not in st.session_state:
    st.session_state.mensagem_padrao = "Olá, {nome}! Sua voz é fundamental. Responda à nossa pesquisa até {data_validade}.\nAcesse: {link_pesquisa}"

if 'logo_personalizada' not in st.session_state:
    st.session_state.logo_personalizada = None

# Base de dados simulada para o Dashboard (carregada se o Supabase estiver offline)
if 'dados_historicos' not in st.session_state:
    st.session_state.dados_historicos = pd.DataFrame({
        "departamento": ["RH", "Financeiro", "Comercial", "TI", "Operações", "Logística", "RH", "TI", "Vendas"],
        "lideranca": [4.2, 3.8, 4.7, 3.1, 3.5, 3.9, 4.5, 3.3, 4.8],
        "comunicacao": [4.0, 3.5, 4.5, 3.0, 3.2, 3.7, 4.3, 3.1, 4.6],
        "reconhecimento": [3.8, 3.4, 4.6, 2.8, 3.0, 3.5, 4.1, 2.9, 4.7],
        "enps": [9, 7, 10, 5, 6, 8, 10, 6, 10]
    })

# =====================================================================
# LÓGICA DE NAVEGAÇÃO: PESQUISA PÚBLICA VS ÁREA ADM
# =====================================================================
query_params = st.query_params

if "view" in query_params and query_params["view"] == "survey":
    # --- INTERFACE DO COLABORADOR ---
    st.markdown("<h1 style='text-align: center; color: #1e3a8a;'>🌱 Ecoa</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #64748b; font-size: 1.2rem;'>Sua voz constrói o nosso amanhã.</p>", unsafe_allow_html=True)
    st.divider()

    st.markdown(f"""
    ### Olá! Que bom ter você aqui.
    Estamos iniciando nossa **Pesquisa de Escuta Organizacional** para a **{st.session_state.empresa_atual}**. 
    O objetivo deste espaço é ouvir genuinamente o que você pensa e sente sobre o nosso ambiente de trabalho.
    
    **Sua participação é fundamental e totalmente anônima.** Nenhuma resposta é vinculada ao seu nome ou e-mail. 
    Reserve cerca de **10 minutos** para responder com tranquilidade e sinceridade.
    """)
    
    with st.form("form_colaborador", clear_on_submit=True):
        st.markdown("#### 📍 Identificação Inicial")
        setor = st.selectbox("Selecione o seu Departamento:", 
                             ["Administrativo", "Comercial", "Financeiro", "Logística", "Operações", "RH", "TI"])
        
        st.divider()
        
        df_ativas = st.session_state.perguntas[st.session_state.perguntas["Ativa"]]
        pilares = df_ativas["Pilar Estratégico"].unique()
        
        for pilar in pilares:
            st.markdown(f"<div class='pilar-container'><h3>📊 {pilar}</h3>", unsafe_allow_html=True)
            questoes_pilar = df_ativas[df_ativas["Pilar Estratégico"] == pilar]
            
            for idx, row in questoes_pilar.iterrows():
                if pilar == "eNPS":
                    st.select_slider(f"**{row['Texto da Pergunta']}**", 
                                     options=[str(i) for i in range(11)], 
                                     value="8", key=f"q_{idx}")
                else:
                    st.radio(f"**{row['Texto da Pergunta']}**", 
                             options=["Discordo Totalmente", "Discordo", "Neutro", "Concordo", "Concordo Totalmente"], 
                             index=3, horizontal=True, key=f"q_{idx}")
            st.markdown("</div>", unsafe_allow_html=True)
            
        st.markdown("#### 💬 Espaço Aberto")
        comentario = st.text_area("Comentários ou sugestões adicionais (opcional):", placeholder="Sinta-se à vontade...")

        if st.form_submit_button("Enviar Minha Contribuição", type="primary", use_container_width=True):
            st.balloons()
            st.success("Obrigado! Suas respostas foram enviadas com sucesso.")
            st.info("Você pode fechar esta aba.")

# =====================================================================
# ÁREA ADMINISTRATIVA
# =====================================================================
elif not st.session_state.autenticado:
    # TELA DE LOGIN
    _, col_login, _ = st.columns([1, 1.2, 1])
    with col_login:
        st.write("")
        st.write("")
        st.markdown("<h1 style='text-align: center; color: #1e3a8a; font-size: 3rem;'>🌱 Ecoa</h1>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center; color: #64748b;'>Painel de Gestão Estratégica</p>", unsafe_allow_html=True)
        with st.form("login_form"):
            st.markdown("#### Autenticação")
            u_email = st.text_input("E-mail", placeholder="seu@email.com")
            u_pass = st.text_input("Senha", type="password", placeholder="••••••••")
            if st.form_submit_button("Entrar", use_container_width=True):
                u_db = st.session_state.usuarios
                valido = u_db[(u_db['E-mail'] == u_email) & (u_db['Palavra-passe'] == u_pass) & (u_db['Status'] == 'Ativo')]
                if not valido.empty:
                    st.session_state.autenticado = True
                    st.session_state.usuario_logado = valido.iloc[0]['Nome']
                    st.rerun()
                else: st.error("Acesso negado. Verifique suas credenciais.")

else:
    # INTERFACE ADMIN COMPLETA
    with st.sidebar:
        if st.session_state.logo_personalizada:
            st.image(st.session_state.logo_personalizada, width=120)
        else:
            st.markdown("<h2 style='color: #1e3a8a;'>🌱 Ecoa</h2>", unsafe_allow_html=True)
        
        st.caption(f"Admin: {st.session_state.usuario_logado}")
        st.divider()
        menu = st.radio("Navegação", 
                        ["🏢 Empresa", "📝 Formulário da Pesquisa", "✉️ Mensagem Automática", 
                         "🔗 Gerenciamento de Links", "📊 Dashboard Geral", "📑 Relatórios", 
                         "👥 Clientes (Utilizadores)", "⚙️ Configurações"], 
                        label_visibility="collapsed")
        st.divider()
        if st.button("🚪 Sair", use_container_width=True):
            st.session_state.autenticado = False
            st.rerun()
        st.caption("v1.2.5 | Desenvolvido por Cris Lima")

    st.markdown(f"<h2 style='color: #334155; font-weight: 700;'>{menu}</h2>", unsafe_allow_html=True)
    st.write(f"Configurações para: **{st.session_state.empresa_atual}**")
    st.divider()

    # --- MÓDULO EMPRESA ---
    if menu == "🏢 Empresa":
        st.markdown("### 🏛️ Dados Organizacionais")
        c1, c2 = st.columns(2)
        with c1:
            st.session_state.empresa_atual = st.text_input("Nome da Empresa", st.session_state.empresa_atual)
            st.text_input("CNPJ", "00.000.000/0001-00")
        with c2:
            st.selectbox("Porte", ["Micro", "Pequena", "Média", "Grande"])
            st.selectbox("Setor Econômico", ["Serviços", "Indústria", "Tecnologia", "Saúde"])
        st.text_area("Departamentos da Empresa", "RH\nComercial\nOperações\nFinanceiro\nTI", height=100)
        if st.button("Salvar Dados"): st.success("Informações atualizadas!")

    # --- MÓDULO FORMULÁRIO ---
    elif menu == "📝 Formulário da Pesquisa":
        st.markdown("### 📝 Editor de Questionário")
        st.info("Gerencie aqui as 35 questões baseadas em metodologias validadas.")
        p_edit = st.data_editor(st.session_state.perguntas, num_rows="dynamic", use_container_width=True, hide_index=True)
        st.session_state.perguntas = p_edit
        st.markdown("---")
        st.markdown(f"🔗 [Testar Experiência do Colaborador](/?view=survey)")

    # --- MÓDULO MENSAGEM ---
    elif menu == "✉️ Mensagem Automática":
        st.markdown("### ✉️ Convite Personalizado")
        msg = st.text_area("Texto da Mensagem", st.session_state.mensagem_padrao, height=200)
        st.caption("Variáveis: `{nome}`, `{data_validade}`, `{link_pesquisa}`")
        if st.button("Guardar"): 
            st.session_state.mensagem_padrao = msg
            st.success("Modelo salvo!")
        st.divider()
        st.markdown("#### Prévia (João)")
        prev = msg.replace("{nome}", "João").replace("{data_validade}", st.session_state.data_validade.strftime("%d/%m/%Y")).replace("{link_pesquisa}", "https://ecoa.app/pesquisa")
        st.info(prev)

    # --- MÓDULO LINKS ---
    elif menu == "🔗 Gerenciamento de Links":
        st.markdown("### 🔗 Controle de Disparos")
        st.session_state.data_validade = st.date_input("Data de Expiração", st.session_state.data_validade)
        slug = st.session_state.empresa_atual.lower().replace(' ', '')
        st.code(f"https://ecoa.app/{slug}/pesquisa?view=survey", language="html")
        st.file_uploader("Subir Lista de Colaboradores", type=["csv", "xlsx"])
        if st.button("Simular Disparos"): st.success("E-mails enviados!")

    # --- MÓDULO DASHBOARD ---
    elif menu == "📊 Dashboard Geral":
        st.markdown("### 📊 Inteligência de Dados")
        df = st.session_state.dados_historicos
        col1, col2, col3 = st.columns(3)
        
        # Métricas Consolidadas
        col1.metric("Liderança (Média)", f"{df['lideranca'].mean():.2f}", "+0.15")
        col2.metric("Comunicação (Média)", f"{df['comunicacao'].mean():.2f}", "-0.05")
        
        prom = len(df[df['enps'] >= 9])
        detr = len(df[df['enps'] <= 6])
        enps_val = ((prom - detr) / len(df)) * 100
        col3.metric("Score eNPS", f"{enps_val:.0f}", "Bom")
        
        st.divider()
        # Gráfico por Setor
        fig = px.bar(df.groupby("departamento")[["lideranca", "comunicacao"]].mean().reset_index(), 
                     x="departamento", y=["lideranca", "comunicacao"], 
                     barmode="group", title="Média por Departamento",
                     color_discrete_sequence=["#1e3a8a", "#10b981"])
        st.plotly_chart(fig, use_container_width=True)

    # --- MÓDULO RELATÓRIOS ---
    elif menu == "📑 Relatórios":
        st.markdown("### 📑 Exportação de Resultados")
        st.write("Gere o PowerPoint executivo com os dados atuais da campanha.")
        if st.button("🚀 Gerar Apresentação PPTX", type="primary"):
            prs = Presentation()
            slide = prs.slides.add_slide(prs.slide_layouts[0])
            slide.shapes.title.text = f"Resultados Ecoa: {st.session_state.empresa_atual}"
            slide.placeholders[1].text = f"Gerado em {datetime.now().strftime('%d/%m/%Y')}"
            
            buf = io.BytesIO()
            prs.save(buf)
            buf.seek(0)
            st.download_button("📥 Baixar PPTX", data=buf, file_name=f"Relatorio_{st.session_state.empresa_atual}.pptx")

    # --- MÓDULO USUÁRIOS ---
    elif menu == "👥 Clientes (Utilizadores)":
        st.markdown("### 👥 Gestão de Acessos")
        u_edit = st.data_editor(st.session_state.usuarios, num_rows="dynamic", use_container_width=True, hide_index=True)
        st.session_state.usuarios = u_edit

    # --- MÓDULO CONFIGURAÇÕES ---
    elif menu == "⚙️ Configurações":
        st.markdown("### ⚙️ Preferências do Sistema")
        up = st.file_uploader("Upload da Logo", type=["png", "jpg"])
        if up: st.session_state.logo_personalizada = up; st.success("Logo atualizada!")
        st.divider()
        if supabase: st.success("Conectado ao Supabase Cloud.")
        else: st.warning("Configurações do Supabase ausentes nos Secrets.")
        st.caption("Ecoa por Cris Lima | v1.2.5")
