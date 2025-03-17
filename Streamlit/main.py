import streamlit as st
import boto3
import matplotlib.pyplot as plt
import io
import re
import base64
import json
import unicodedata
from PIL import Image, ImageDraw

st.set_page_config(
    page_title="Validador de Identidade",
    page_icon="🔐",
    layout="wide"
)

st.title("Validador de Identidade")
st.write("Trabalho Final Cognitive Environments - FIAP")
st.write("- Felipe Fabossi | RM: 353427")
st.write("- Paola Lemes | RM: 336523")
st.write("- Yago Angelini | RM: 354173")

if 'nome_cnh' not in st.session_state:
    st.session_state.nome_cnh = ""
if 'cpf_cnh' not in st.session_state:
    st.session_state.cpf_cnh = ""
if 'nome_conta' not in st.session_state:
    st.session_state.nome_conta = ""
if 'endereco_conta' not in st.session_state:
    st.session_state.endereco_conta = ""
if 'correspondencia' not in st.session_state:
    st.session_state.correspondencia = False
if 'foto_cnh_bytes' not in st.session_state:
    st.session_state.foto_cnh_bytes = None
if 'foto_selfie_bytes' not in st.session_state:
    st.session_state.foto_selfie_bytes = None
if 'similaridade' not in st.session_state:
    st.session_state.similaridade = None
if 'processo_completo' not in st.session_state:
    st.session_state.processo_completo = False

def processar_cnh(file, aws_access_id, aws_access_key, region):
    bytes_test = file.getvalue()
    
    session = boto3.Session(aws_access_key_id=aws_access_id, aws_secret_access_key=aws_access_key)
    client = session.client('textract', region_name=region)
    response = client.analyze_document(Document={'Bytes': bytes_test}, FeatureTypes=['FORMS'])
    
    blocks = response["Blocks"]
    
    texto_extraido = []
    
    for block in blocks:
        if block["BlockType"] == "WORD" and int(block["Confidence"]) > 50:
            texto_extraido.append(block["Text"])
    
    return " ".join(texto_extraido)

def extrair_nome_cpf(texto_extraido):
    padrao_nome = r"HABILITAÇÃO\s+([A-Z\s]+?)\s+\d{2}/\d{2}/\d{4}"
    nome = re.search(padrao_nome, texto_extraido)
    nome = nome.group(1).strip() if nome else "Nome não encontrado"
    
    padrao_cpf = r"HAB\s+(\d{3}\.\d{3}\.\d{3}-\d{2})"
    cpf = re.search(padrao_cpf, texto_extraido)
    cpf = cpf.group(1) if cpf else "CPF não encontrado"
    
    return {"nome": nome, "cpf": cpf}

def extrair_texto_com_openai(file, api_key):
    import openai
    
    openai.api_key = api_key
    
    img = Image.open(io.BytesIO(file.getvalue()))
    
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    imagem_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
    
    try:
        response = openai.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": "Por favor, descreva detalhadamente o que você vê nesta imagem, incluindo qualquer texto visível."
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/png;base64,{imagem_base64}"
                            }
                        }
                    ]
                }
            ],
            max_tokens=1000
        )
        texto_extraido = response.choices[0].message.content
        
        st.write("Texto extraído da imagem:")
        with st.expander("Ver texto completo"):
            st.write(texto_extraido)
        
        segunda_resposta = openai.chat.completions.create(
            model="gpt-4",
            messages=[
                {
                    "role": "system",
                    "content": "Você é um assistente que analisa documentos."
                },
                {
                    "role": "user",
                    "content": f"Com base no texto a seguir, extraia o nome completo da pessoa e o endereço completo em formato JSON com campos 'nome' e 'endereco':\n\n{texto_extraido}"
                }
            ]
        )
        resultado = segunda_resposta.choices[0].message.content
        
        st.write("Resposta da extração estruturada:")
        with st.expander("Ver resposta completa"):
            st.write(resultado)
        
        match = re.search(r'\{.*\}', resultado, re.DOTALL)
        if match:
            json_str = match.group(0)
            try:
                dados = json.loads(json_str)
                return dados.get('nome', ''), dados.get('endereco', '')
            except json.JSONDecodeError as e:
                st.error(f"Erro ao decodificar JSON: {e}")
                st.code(json_str)
                return None, None
        else:
            st.warning("Não foi possível encontrar um formato JSON válido na resposta")
            return None, None
            
    except Exception as e:
        st.error(f"Erro ao processar a imagem: {e}")
        import traceback
        st.code(traceback.format_exc())
        return None, None

def comparar_nomes(nome1, nome2):
    if not nome1 or not nome2:
        return False
        
    def normalizar_nome(nome):
        nome = nome.upper()
        nome = unicodedata.normalize('NFKD', nome).encode('ASCII', 'ignore').decode('ASCII')
        nome = re.sub(r'[^\w\s]', '', nome)
        return ' '.join(nome.split())
        
    nome1_norm = normalizar_nome(nome1)
    nome2_norm = normalizar_nome(nome2)
    
    if nome1_norm == nome2_norm:
        return True
    if nome1_norm in nome2_norm or nome2_norm in nome1_norm:
        return True
        
    palavras1 = set(nome1_norm.split())
    palavras2 = set(nome2_norm.split())
    palavras_comuns = palavras1.intersection(palavras2)
    min_palavras = min(len(palavras1), len(palavras2))
    
    if min_palavras > 0 and len(palavras_comuns) / min_palavras >= 0.7:
        return True
        
    return False

def comparar_faces(foto_cnh_bytes, foto_selfie_bytes, aws_access_id, aws_access_key, region):
    session = boto3.Session(aws_access_key_id=aws_access_id, aws_secret_access_key=aws_access_key)
    client = session.client("rekognition", region_name=region)
    
    try:
        response = client.compare_faces(
            SourceImage={'Bytes': foto_cnh_bytes},
            TargetImage={'Bytes': foto_selfie_bytes},
        )
        
        if len(response.get("FaceMatches", [])) > 0:
            similaridade = response["FaceMatches"][0]["Similarity"]
            return response, similaridade
        else:
            return response, 0
    except Exception as e:
        st.error(f"Erro ao comparar faces: {e}")
        return None, 0

def visualizar_face_cnh(image_bytes, response):
    image = Image.open(io.BytesIO(image_bytes))
    image.thumbnail((500, 500))
    
    imgWidth, imgHeight = image.size
    
    draw = ImageDraw.Draw(image)
    
    box = response["SourceImageFace"]["BoundingBox"]
    
    top = imgHeight * box['Top']
    left = imgWidth * box['Left']
    width = imgWidth * box['Width']
    height = imgHeight * box['Height']
    
    draw.rectangle([left, top, left + width, top + height], outline='#00d400', width=2)
    
    return image

def visualizar_face_selfie(image_bytes, response):
    image = Image.open(io.BytesIO(image_bytes))
    image.thumbnail((500, 500))
    
    imgWidth, imgHeight = image.size
    
    draw = ImageDraw.Draw(image)
    
    for item_match in response.get("FaceMatches", []):
        box = item_match["Face"]["BoundingBox"]
        
        top = imgHeight * box['Top']
        left = imgWidth * box['Left']
        width = imgWidth * box['Width']
        height = imgHeight * box['Height']
        
        draw.rectangle([left, top, left + width, top + height], outline='#00d400', width=2)
        
        font_size = 15
        draw.text((left, top - font_size - 5), f"Similaridade: {item_match['Similarity']:.2f}%", fill='#00d400')
    
    return image

tab1, tab2, tab3, tab4 = st.tabs(["Configuração", "Extração CNH", "Validação Comprovante", "Comparação Facial"])

with tab1:
    st.header("Configuração de Credenciais")
    
    st.subheader("Credenciais AWS")
    aws_access_id = st.text_input("AWS Access ID", type="password")
    aws_access_key = st.text_input("AWS Access Key", type="password")
    aws_region = st.text_input("AWS Region", value="us-east-1")
    
    st.subheader("Credencial OpenAI")
    openai_api_key = st.text_input("OpenAI API Key", type="password")
    
    if not openai_api_key:
        st.warning("⚠️ A chave da API da OpenAI é necessária para a etapa de validação do comprovante de residência.")
        st.info("""Para obter uma chave da API da OpenAI:
        1. Acesse https://platform.openai.com/signup
        2. Crie uma conta ou faça login
        3. Vá para 'API Keys' no menu
        4. Clique em 'Create new secret key'
        5. Copie a chave gerada e cole no campo acima
        """)
    
    st.info("Configure suas credenciais antes de prosseguir para as próximas etapas.")

with tab2:
    st.header("Extração de Dados da CNH")
    
    st.write("Faça upload da imagem da CNH para extrair nome e CPF.")
    uploaded_file_cnh = st.file_uploader("Escolha a imagem da CNH", type=["jpg", "jpeg", "png"], key="cnh_uploader")
    
    if uploaded_file_cnh is not None:
        st.image(uploaded_file_cnh, caption="CNH carregada", width=400)
        
        if st.button("Processar CNH"):
            with st.spinner("Processando a CNH..."):
                st.session_state.foto_cnh_bytes = uploaded_file_cnh.getvalue()
                
                texto_cnh = processar_cnh(uploaded_file_cnh, aws_access_id, aws_access_key, aws_region)
                
                dados_cnh = extrair_nome_cpf(texto_cnh)
                st.session_state.nome_cnh = dados_cnh["nome"]
                st.session_state.cpf_cnh = dados_cnh["cpf"]
                
                st.success("Extração concluída!")
                st.write(f"**Nome extraído:** {st.session_state.nome_cnh}")
                st.write(f"**CPF extraído:** {st.session_state.cpf_cnh}")
                
                with st.expander("Ver todo o texto extraído"):
                    st.text(texto_cnh)

    if st.session_state.nome_cnh and st.session_state.cpf_cnh:
        st.write("### Dados Extraídos:")
        st.write(f"**Nome:** {st.session_state.nome_cnh}")
        st.write(f"**CPF:** {st.session_state.cpf_cnh}")

with tab3:
    st.header("Validação de Comprovante/Conta")
    
    if not st.session_state.nome_cnh:
        st.warning("⚠️ Você precisa primeiro processar uma CNH na aba anterior.")
    else:
        st.write("Faça upload da imagem do comprovante/conta para validar o nome e extrair o endereço.")
        
        uploaded_file_conta = st.file_uploader("Escolha a imagem do comprovante/conta", type=["jpg", "jpeg", "png"], key="conta_uploader")
        
        if uploaded_file_conta is not None:
            st.image(uploaded_file_conta, caption="Comprovante/conta carregado", width=400)
            
            if not openai_api_key:
                st.error("⚠️ Você precisa fornecer uma chave da API da OpenAI na aba de Configuração.")
            else:
                if st.button("Processar Comprovante"):
                    with st.spinner("Processando o comprovante/conta..."):
                        st.info("Este processo pode demorar alguns segundos enquanto o GPT-4o analisa a imagem...")
                        
                        nome_conta, endereco_conta = extrair_texto_com_openai(uploaded_file_conta, openai_api_key)
                        
                        if nome_conta is not None and endereco_conta is not None:
                            st.session_state.nome_conta = nome_conta or "Não detectado"
                            st.session_state.endereco_conta = endereco_conta or "Não detectado"
                            
                            if nome_conta:
                                st.session_state.correspondencia = comparar_nomes(st.session_state.nome_cnh, nome_conta)
                            else:
                                st.session_state.correspondencia = False
                            
                            st.success("Extração concluída!")
                        else:
                            st.error("❌ Não foi possível extrair as informações. Por favor, tente com outra imagem ou verifique se a chave da API é válida.")

        if st.session_state.nome_conta:
            st.write("### Dados Extraídos:")
            st.write(f"**Nome na CNH:** {st.session_state.nome_cnh}")
            st.write(f"**Nome na Conta:** {st.session_state.nome_conta}")
            st.write(f"**Endereço:** {st.session_state.endereco_conta}")
            
            if st.session_state.correspondencia:
                st.success("✅ Os nomes correspondem!")
            else:
                st.error("❌ Os nomes NÃO correspondem!")

with tab4:
    st.header("Comparação Facial")
    
    if not st.session_state.foto_cnh_bytes:
        st.warning("⚠️ Você precisa primeiro processar uma CNH na segunda aba.")
    else:
        st.write("Faça upload de uma selfie para comparar com a foto da CNH.")
        
        uploaded_file_selfie = st.file_uploader("Escolha uma selfie", type=["jpg", "jpeg", "png"], key="selfie_uploader")
        
        if uploaded_file_selfie is not None:
            st.image(uploaded_file_selfie, caption="Selfie carregada", width=400)
            
            if st.button("Comparar Faces"):
                with st.spinner("Comparando faces..."):
                    st.session_state.foto_selfie_bytes = uploaded_file_selfie.getvalue()
                    
                    response, similaridade = comparar_faces(
                        st.session_state.foto_cnh_bytes,
                        st.session_state.foto_selfie_bytes,
                        aws_access_id,
                        aws_access_key,
                        aws_region
                    )
                    
                    st.session_state.similaridade = similaridade
                    
                    if response and similaridade > 0:
                        st.success(f"Comparação concluída! Similaridade: {similaridade:.2f}%")
                        
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            st.write("**Foto da CNH:**")
                            img_cnh = visualizar_face_cnh(st.session_state.foto_cnh_bytes, response)
                            st.image(img_cnh, width=400)
                            
                        with col2:
                            st.write("**Selfie:**")
                            img_selfie = visualizar_face_selfie(st.session_state.foto_selfie_bytes, response)
                            st.image(img_selfie, width=400)
                            
                        if similaridade >= 80:
                            st.success("✅ As faces correspondem com alta confiança!")
                        elif similaridade >= 60:
                            st.warning("⚠️ As faces têm alguma semelhança, mas a confiança não é alta.")
                        else:
                            st.error("❌ As faces provavelmente não correspondem à mesma pessoa.")
                            
                        st.session_state.processo_completo = True
                    else:
                        st.error("❌ Não foi possível encontrar correspondência entre as faces!")
                        
        if st.session_state.similaridade is not None:
            st.write(f"**Similaridade detectada:** {st.session_state.similaridade:.2f}%")

if st.session_state.processo_completo:
    st.header("Resultado Final da Validação")
    
    validacao_nome = "✅ VÁLIDO" if st.session_state.correspondencia else "❌ INVÁLIDO"
    validacao_face = "✅ VÁLIDO" if st.session_state.similaridade >= 80 else "❌ INVÁLIDO"
    
    resultado_final = "✅ VALIDAÇÃO COMPLETA" if (st.session_state.correspondencia and st.session_state.similaridade >= 80) else "❌ VALIDAÇÃO FALHOU"
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Verificação de Nome", validacao_nome)
    with col2:
        st.metric("Verificação Facial", validacao_face)
    with col3:
        st.metric("Resultado Final", resultado_final)
    
    st.write("### Resumo dos Dados")
    st.write(f"- **Nome da CNH:** {st.session_state.nome_cnh}")
    st.write(f"- **CPF:** {st.session_state.cpf_cnh}")
    st.write(f"- **Nome da Conta:** {st.session_state.nome_conta}")
    st.write(f"- **Endereço:** {st.session_state.endereco_conta}")
    st.write(f"- **Similaridade Facial:** {st.session_state.similaridade:.2f}%") 