import streamlit as st
import pandas as pd
import plotly.express as px
from pptx import Presentation
from pptx.util import Inches, Pt
import io
from datetime import datetime, timedelta
from supabase import create_client, Client # NOVO: Importação do Supabase

# --- CONFIGURAÇÕES DA PÁGINA ---
st.set_page_config(
    page_title="Ecoa: Plataforma de Escuta Organizacional",
    page_icon="🌱",
    layout="wide"
)

# --- CONEXÃO AUTOMÁTICA COM O SUPABASE (SECRETS) ---
@st.cache_resource
def init_connection():
    try:
        # O sistema vai buscar as chaves no cofre seguro do Streamlit
        url = st.secrets["SUPABASE_URL"]
        key = st.secrets["SUPABASE_KEY"]
        return create_client(url, key)
    except Exception:
        return None # Se não achar as chaves, não quebra o sistema

supabase = init_connection()

# --- INICIALIZAÇÃO DE DADOS E ESTADOS (MEMÓRIA DO SISTEMA) ---
if 'dados_locais' not in st.session_state:
    st.session_state.dados_locais = pd.DataFrame(columns=["data", "departamento", "lideranca", "comunicacao", "reconhecimento", "enps"])

if 'perguntas' not in st.session_state:
    # Banco de perguntas padrão editável
    st.session_state.perguntas = pd.DataFrame({
        "Ativa": [True, True, True, True],
        "Pilar Estratégico": ["Liderança", "Comunicação", "Reconhecimento", "eNPS"],
        "Texto da Pergunta": [
            "Meu gestor direto me ouve e oferece feedbacks construtivos.",
            "As informações importantes chegam até mim de forma clara.",
            "Sinto que meu esforço é reconhecido e valorizado.",
            "De 0 a 10, o quanto recomendaria nossa empresa como um bom lugar para trabalhar?"
        ]
    })

if 'mensagem_padrao' not in st.session_state:
    st.session_state.mensagem_padrao = "Olá, {nome}! Sua voz é fundamental para construirmos um ambiente cada vez melhor. Reserve 2 minutinhos para nos contar como você se sente até o dia {data_validade}. É 100% seguro e anônimo.\nAcesse: {link_pesquisa}"

if 'logo_empresa' not in st.session_state:
    st.session_state.logo_empresa = None

if 'empresa_atual' not in st.session_state:
    st.session_state.empresa_atual = "Sua Empresa"

if 'data_validade' not in st.session_state:
    st.session_state.data_validade = datetime.today().date() + timedelta(days=15)

# --- MENU LATERAL DE NAVEGAÇÃO ---
with st.sidebar:
    st.title("🌱 Ecoa")
    st.markdown("---")
    
    # O menu principal que muda as telas
    menu = st.radio(
        "Menu Principal",
        [
            "🏢 Empresa",
            "📝 Formulário da Pesquisa",
            "✉️ Mensagem Automática",
            "🔗 Gerenciamento de Links",
            "📊 Dashboard Geral",
            "📑 Relatórios",
            "👥 Clientes (Usuários)",
            "⚙️ Configurações"
        ]
    )
    
    st.markdown("---")
    st.caption("Desenvolvido com 💙 por Cris Lima")

# --- LÓGICA DE EXIBIÇÃO DO CABEÇALHO ---
col_logo, col_titulo = st.columns([1, 8])
with col_logo:
    if st.session_state.logo_empresa is not None:
        st.image(st.session_state.logo_empresa, width=80)
    else:
        st.markdown("## 🌱")
with col_titulo:
    st.title(menu) # O título da página muda conforme o menu selecionado


# =====================================================================
# MÓDULO 1: EMPRESA
# =====================================================================
if menu == "🏢 Empresa":
    st.markdown("### Cadastro e Dados Estruturais")
    st.write("Gerencie as informações da empresa cliente que está rodando a pesquisa atual.")
    
    col1, col2 = st.columns(2)
    with col1:
        nome_empresa_input = st.text_input("Nome Fantasia da Empresa", st.session_state.empresa_atual)
        st.text_input("CNPJ", "00.000.000/0001-00")
    with col2:
        st.selectbox("Porte da Empresa", ["Micro (até 9 func.)", "Pequena (10 a 49)", "Média (50 a 99)", "Grande (+100)"])
        st.selectbox("Segmento", ["Serviços", "Indústria", "Comércio", "Tecnologia", "Saúde"])
        
    st.markdown("#### Estrutura de Departamentos")
    st.write("Adicione os departamentos que aparecerão para o colaborador selecionar:")
    st.text_area("Departamentos (um por linha)", "Administrativo\nVendas\nLogística\nTecnologia\nAtendimento", height=120)
    
    if st.button("Salvar Dados da Empresa", type="primary"):
        st.session_state.empresa_atual = nome_empresa_input
        st.success(f"Dados salvos! A pesquisa atual está configurada para: **{st.session_state.empresa_atual}**")

# =====================================================================
# MÓDULO 2: FORMULÁRIO DA PESQUISA
# =====================================================================
elif menu == "📝 Formulário da Pesquisa":
    st.markdown("### Banco de Perguntas Dinâmico")
    st.write("Aqui você molda a voz da sua pesquisa. Marque a caixa **Ativa** para incluir a pergunta no formulário que será enviado. Você pode editar os textos clicando diretamente na tabela ou adicionar novas linhas no final.")
    
    # Editor de dados interativo do Streamlit
    perguntas_editadas = st.data_editor(
        st.session_state.perguntas,
        num_rows="dynamic", # Permite adicionar/excluir linhas
        use_container_width=True,
        hide_index=True
    )
    
    st.session_state.perguntas = perguntas_editadas
    st.success("As alterações na tabela são salvas automaticamente na memória desta sessão.")
    
    with st.expander("👀 Visualizar Formulário (Simulação do Colaborador)"):
        st.write("Assim é como o colaborador verá as perguntas ativas no celular dele:")
        st.markdown("---")
        for index, row in perguntas_editadas[perguntas_editadas["Ativa"]].iterrows():
            if row["Pilar Estratégico"] == "eNPS":
                st.slider(f"(eNPS) {row['Texto da Pergunta']}", 0, 10, 8, key=f"sim_{index}")
            else:
                st.slider(f"({row['Pilar Estratégico']}) {row['Texto da Pergunta']}", 1, 5, 3, key=f"sim_{index}")

# =====================================================================
# MÓDULO 3: MENSAGEM AUTOMÁTICA
# =====================================================================
elif menu == "✉️ Mensagem Automática":
    st.markdown("### Comunicação Humanizada")
    st.write("Personalize o texto de convite que será disparado via e-mail ou WhatsApp junto com o link da pesquisa.")
    st.info("Dicas de variáveis: Use `{nome}`, `{data_validade}` e `{link_pesquisa}`. O sistema as substituirá automaticamente.")
    
    msg_atual = st.text_area("Corpo da Mensagem", st.session_state.mensagem_padrao, height=150)
    if st.button("Salvar Modelo de Mensagem", type="primary"):
        st.session_state.mensagem_padrao = msg_atual
        st.success("Mensagem padrão atualizada com sucesso!")
        
    st.markdown("#### Pré-visualização do envio para o João:")
    data_formatada_preview = st.session_state.data_validade.strftime('%d/%m/%Y')
    empresa_slug_preview = st.session_state.empresa_atual.replace(" ", "").lower()
    link_preview = f"https://ecoa.app/{empresa_slug_preview}/xyz987"
    
    texto_preview = msg_atual.replace("{nome}", "João").replace("{link_pesquisa}", link_preview).replace("{data_validade}", data_formatada_preview)
    st.code(texto_preview)

# =====================================================================
# MÓDULO 4: GERENCIAMENTO DE LINKS
# =====================================================================
elif menu == "🔗 Gerenciamento de Links":
    st.markdown("### Controle de Acessos e Disparos")
    st.write("Gere links únicos para mapeamento seguro de respondentes ou um link geral para equipes operacionais.")
    
    # Configuração de Validade e Empresa
    st.markdown("#### ⚙️ Parâmetros da Campanha")
    col_param1, col_param2 = st.columns(2)
    with col_param1:
        st.info(f"**Empresa Atual:** {st.session_state.empresa_atual}\n\n*(Altere no módulo 'Empresa' se necessário)*")
    with col_param2:
        nova_validade = st.date_input("Data de Encerramento (Validade dos Links):", st.session_state.data_validade)
        st.session_state.data_validade = nova_validade
    
    st.markdown("---")
    
    # Geração dinâmica do link (Baseado no nome da empresa e data)
    empresa_slug = st.session_state.empresa_atual.replace(" ", "").lower()
    data_formatada = st.session_state.data_validade.strftime('%Y%m%d')
    link_geral = f"https://ecoa.app/pesquisa?empresa={empresa_slug}&validade={data_formatada}"
    
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("#### 📧 Envio em Lote (Link Único)")
        st.write("Faça upload de uma planilha com Nome e E-mail. O sistema criará links não-compartilháveis com validade atrelada.")
        st.file_uploader("Planilha de Colaboradores (.csv ou .xlsx)", type=["csv", "xlsx"])
        if st.button("Processar e Gerar Disparos"):
            st.success(f"Disparos simulados para {st.session_state.empresa_atual}! Os links expiram em {nova_validade.strftime('%d/%m/%Y')}.")
        
    with col2:
        st.markdown("#### 🌐 Link Geral da Campanha")
        st.write("Para murais, totens de RH ou grupos de WhatsApp. O IP será rastreado para evitar dupla resposta.")
        st.code(link_geral, language="html")
        st.button("Copiar Link Geral")

# =====================================================================
# MÓDULO 5: DASHBOARD GERAL
# =====================================================================
elif menu == "📊 Dashboard Geral":
    st.markdown("### Análise de Dados em Tempo Real")
    
    df = st.session_state.dados_locais
    
    if df.empty:
        st.info("Nenhuma resposta registrada no momento. Conecte ao banco de dados ou simule respostas.")
    else:
        colA, colB, colC = st.columns(3)
        media_lid = df["lideranca"].mean() if "lideranca" in df else 0
        media_rec = df["reconhecimento"].mean() if "reconhecimento" in df else 0
        
        promotores = len(df[df["enps"] >= 9]) if "enps" in df else 0
        detratores = len(df[df["enps"] <= 6]) if "enps" in df else 0
        total = len(df)
        enps_score = ((promotores - detratores) / total) * 100 if total > 0 else 0
        
        colA.metric("Liderança (Média)", f"{media_lid:.1f} / 5.0")
        colB.metric("Reconhecimento (Média)", f"{media_rec:.1f} / 5.0")
        colC.metric("eNPS Geral", f"{enps_score:.0f}", help="Varia de -100 a +100")
        
        st.markdown("---")
        df_agrupado = df.groupby("departamento")[["lideranca", "comunicacao", "reconhecimento"]].mean().reset_index()
        fig = px.bar(df_agrupado, x="departamento", y=["lideranca", "comunicacao", "reconhecimento"],
                     barmode="group", title="Visão Comparativa de Pilares por Setor",
                     color_discrete_sequence=["#1f77b4", "#ff7f0e", "#2ca02c"])
        st.plotly_chart(fig, use_container_width=True)

# =====================================================================
# MÓDULO 6: RELATÓRIOS
# =====================================================================
elif menu == "📑 Relatórios":
    st.markdown("### Exportação e Apresentação Executiva")
    st.write("Exporte os dados consolidados diretamente para uma apresentação de PowerPoint pronta para a diretoria.")
    
    df_relatorio = st.session_state.dados_locais
    if df_relatorio.empty:
        st.warning("É necessário ter respostas na pesquisa para gerar o relatório.")
    else:
        def gerar_pptx(dataframe):
            prs = Presentation()
            slide_titulo = prs.slides.add_slide(prs.slide_layouts[0])
            slide_titulo.shapes.title.text = "Resultados: Pesquisa Ecoa"
            slide_titulo.placeholders[1].text = f"Empresa: {st.session_state.empresa_atual} - {datetime.now().strftime('%d/%m/%Y')}"
            
            slide_resumo = prs.slides.add_slide(prs.slide_layouts[1])
            slide_resumo.shapes.title.text = "Média Geral dos Pilares Avaliados"
            tf = slide_resumo.placeholders[1].text_frame
            tf.text = "Com base nas respostas coletadas na plataforma:"
            
            for pilar in ["lideranca", "comunicacao", "reconhecimento"]:
                if pilar in dataframe:
                    p = tf.add_paragraph()
                    p.text = f"• {pilar.capitalize()}: {dataframe[pilar].mean():.2f} / 5.0"
            
            binary_output = io.BytesIO()
            prs.save(binary_output)
            binary_output.seek(0)
            return binary_output
        
        st.info("Clique no botão abaixo para baixar sua apresentação `.pptx` compilada automaticamente.")
        if st.button("Preparar Arquivo PowerPoint", type="primary"):
            arquivo_pptx = gerar_pptx(df_relatorio)
            st.download_button("📥 Baixar Apresentação (.pptx)", data=arquivo_pptx, file_name=f"Relatorio_Ecoa_{st.session_state.empresa_atual.replace(' ', '')}.pptx", mime="application/vnd.openxmlformats-officedocument.presentationml.presentation")

# =====================================================================
# MÓDULO 7: CLIENTES (USUÁRIOS)
# =====================================================================
elif menu == "👥 Clientes (Usuários)":
    st.markdown("### Gestão de Acessos")
    st.write("Controle quem tem permissão para acessar o painel de resultados do Ecoa.")
    
    dados_usuarios = pd.DataFrame({
        "Nome": ["Cris Lima", "Juliana", "Diretor Financeiro"],
        "E-mail": ["cris@ecoa.app", "ju@ecoa.app", "diretor@empresa.com"],
        "Nível de Acesso": ["Admin Master", "Analista RH", "Apenas Leitura (Dashboard)"],
        "Status": ["Ativo", "Ativo", "Pendente"]
    })
    
    st.dataframe(dados_usuarios, use_container_width=True)
    st.button("➕ Adicionar Novo Usuário")

# =====================================================================
# MÓDULO 8: CONFIGURAÇÕES
# =====================================================================
elif menu == "⚙️ Configurações":
    st.markdown("### Configurações Globais do Sistema")
    
    st.markdown("#### 🎨 Identidade Visual")
    logo_upload = st.file_uploader("Substituir a Logo do Sistema (PNG ou JPG)", type=["png", "jpg", "jpeg"])
    if logo_upload is not None:
        st.session_state.logo_empresa = logo_upload
        st.success("Logo atualizada! Ela aparecerá no topo do menu lateral.")
        
    st.markdown("---")
    st.markdown("#### ☁️ Status do Banco de Dados")
    
    # O sistema agora apenas verifica se conectou automaticamente
    if supabase is not None:
        st.success("✅ Supabase conectado automaticamente e operando com segurança máxima!")
    else:
        st.warning("⚠️ Supabase não conectado. Configure as variáveis em 'Secrets' no painel do Streamlit Cloud.")
