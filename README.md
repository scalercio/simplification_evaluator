# Avaliador de Textos Simplificados

Aplicação web simples em **Streamlit** com backend em Python para avaliação de documentos simplificados, especialmente bulas.

O app possui dois módulos:

1. **Revisor Linguístico**
2. **Revisor Técnico**

Cada módulo carrega um arquivo `.parquet` com as colunas:

- `docs`: documento original
- `simple_doc`: documento simplificado

O usuário avalia cada par de textos respondendo a cinco perguntas com notas de 1 a 5.

## Regras dos módulos

### Revisor Linguístico

Perguntas habilitadas:

- P1: simplicidade geral com qualidade
- P2: simplificação lexical
- P3: simplificação estrutural
- P4: gramaticalidade e fluência

Pergunta desabilitada:

- P5: preservação do significado principal

### Revisor Técnico

Perguntas habilitadas:

- P1: simplicidade geral com qualidade
- P5: preservação do significado principal

Perguntas desabilitadas:

- P2: simplificação lexical
- P3: simplificação estrutural
- P4: gramaticalidade e fluência

## Rodar localmente

Crie um ambiente virtual:

```bash
python3.10 -m venv .venv
source .venv/bin/activate
```

Instale as dependências:

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

Rode o app:

```bash
streamlit run app.py
```

## Deploy gratuito com Streamlit Community Cloud

1. Crie um repositório no GitHub.
2. Envie estes arquivos para o repositório:
   - `app.py`
   - `requirements.txt`
   - `README.md`
3. Acesse o Streamlit Community Cloud.
4. Clique em **New app**.
5. Selecione o repositório.
6. Escolha `app.py` como arquivo principal.
7. Faça o deploy.

## Uso no deploy online

No deploy online, o app não consegue acessar arquivos diretamente do seu computador por caminho local.

Por isso, use a aba **Upload do parquet**.

Depois de avaliar os registros, use o botão permanente no topo:

```text
⬇️ Baixar respostas
```

O arquivo baixado será um `.parquet` contendo:

- `record_id`
- `docs`
- `simple_doc`
- `linguistic_q1`
- `linguistic_q2`
- `linguistic_q3`
- `linguistic_q4`
- `linguistic_q5`
- `technical_q1`
- `technical_q2`
- `technical_q3`
- `technical_q4`
- `technical_q5`

As perguntas desabilitadas e os registros ainda não respondidos ficam em branco.

## Observação importante

O app mantém as respostas em memória durante a sessão. Em deploy online, baixe o arquivo periodicamente para evitar perda de dados caso a sessão seja reiniciada.
