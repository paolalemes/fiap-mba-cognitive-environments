# Validação de Dados com AWS e OpenAI

## Descrição do Projeto
Este projeto tem como objetivo realizar a **validação de dados a partir de imagens** utilizando serviços em nuvem da **AWS** e **OpenAI**. O código implementado no **Jupyter Notebook** permite:

1. **Extração de Nome e CPF** de uma CNH (Carteira Nacional de Habilitação) utilizando **AWS Textract**.
2. **Comparar a foto da CNH com uma foto do usuário** para verificação de identidade utilizando **AWS Rekognition**.
3. **Extrair o Nome e Endereço** de um comprovante de residência com **OpenAI GPT-4o**.
4. **Comparar os nomes da CNH e do comprovante de endereço** para verificar a correspondência.

## Requisitos
Antes de executar o código, é necessário possuir:

- **Credenciais da AWS** (ACCESS_ID e ACCESS_KEY) para utilizar os serviços Textract e Rekognition.
- **Chave de API da OpenAI** para extrair informações do comprovante de endereço.
- **Jupyter Notebook** configurado para execução do script.

## Como Executar
1. Clone este repositório:
   ```sh
   git clone https://github.com/seu-usuario/nome-do-repositorio.git
   ```
2. Instale as dependências necessárias (caso ainda não tenha):
   ```sh
   pip install boto3 Pillow openai requests matplotlib
   ```
3. Execute o **Jupyter Notebook** e siga as instruções no próprio código.

## Importante: Carregamento de Arquivos
Por questões de **privacidade e segurança de dados**, este repositório **não inclui imagens de CNHs, fotos pessoais ou comprovantes de endereço**.

Para executar a validação, você deverá **carregar manualmente** os arquivos quando solicitado pelo código.

Os arquivos necessários são:
- **Imagem da CNH** (PNG, JPEG, etc.)
- **Foto do rosto do usuário** (selfie)
- **Imagem do comprovante de endereço**

## Estrutura do Código
- **Extração de texto da CNH** usando **AWS Textract**
- **Extração de Nome e CPF** da CNH com expressões regulares
- **Comparacão de faces** entre CNH e foto do usuário usando **AWS Rekognition**
- **Extração de Nome e Endereço** do comprovante usando **OpenAI GPT-4o**
- **Verificação de correspondência** entre os nomes extraídos

## Contribuição
Caso queira contribuir para este projeto, sinta-se à vontade para abrir um **pull request** ou relatar problemas na seção de **issues**.

## Autor
[Seu Nome]

---
Este repositório foi criado como parte de um trabalho acadêmico para a disciplina de **Cognitive Environments**.

