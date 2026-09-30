# 🔬 YeastPlate Analyzer
**Sistema Científico Automatizado para Bioanálise de Leveduras (*Saccharomyces cerevisiae*)**  
*Desenvolvido para laboratórios de bancada (UFRJ) | Versão: 2.1.0 | Licença: MIT*

---

## 🚀 Como Executar o Aplicativo

O aplicativo possui uma interface web responsiva construída em Streamlit, acessível tanto no computador do laboratório quanto no navegador do smartphone conectado à mesma rede Wi-Fi.

### 1. Pré-requisitos
Certifique-se de ter o Python 3.10+ e o gerenciador `uv` ou `pip` instalados.

### 2. Iniciar a Aplicação
No diretório do projeto, execute:

```bash
uv run --with streamlit --with opencv-python-headless --with scipy --with numpy --with pandas --with pydantic streamlit run app/main.py
```

O terminal exibirá:
* **Local URL:** `http://localhost:8501` (para uso no computador)
* **Network URL:** `http://192.168.x.x:8501` (para acessar direto pelo celular na bancada)

---

## 🧫 Modos de Operação

### Modo 1: Contagem de Colônias (Spread Plate)
* **Finalidade:** Placas de isolamento ou plaqueamento em volume conhecido (ex.: $100\,\mu\text{L}$).
* **Algoritmo:** Desacoplamento espectral em `float32` (Luminosidade Lab $\times$ Inverso da Saturação HSV), transformada de distância euclidiana, máximos locais e **Watershed com marcadores** para desmembrar colônias confluentes.
* **Saídas:** Contagem total, identificação de faixa estatística válida ($30 \le N \le 300$, conforme ISO 7218), cálculo formal de $\text{UFC/mL}$ e tabela morfométrica (área, circularidade e solidez).

### Modo 2: Ensaio de Gota / Spotting Assay (Diluição Seriada)
* **Finalidade:** Screening de sensibilidade ao estresse (ex.: LiCl, NaCl, temperatura) e fontes de carbono (YPD, YPGal, YPGly).
* **Algoritmo:** Detecção automática da grade retangular (ex.: $4 \times 6$), medição de intensidade líquida com correção do fundo local do ágar.
* **Saídas:** **Sinal Integrado Corrigido pelo Fundo (a.u.)**, detecção de saturação e a métrica primária: **Maior Diluição com Crescimento Detectado** por linhagem.

---

## 🛡️ Controle de Qualidade (QC Camada 1)

Antes de qualquer quantificação biológica, cada foto é avaliada contra critérios determinísticos:
1. **Nitidez / Foco:** Variância do operador Laplaciano ($\ge 100.0$ para imagem nítida).
2. **Saturação de Pixels:** Alerta de reflexo se pixels $\ge 250$ ultrapassarem $5\%$.
3. **Enquadramento da Placa:** Rejeita fotos onde a circunferência da placa foi cortada na borda (`QC_PLATE_CLIPPED`).
4. **Resolução:** Alerta imagens abaixo de $1200 \times 1200\text{ px}$.

---

## 🧪 Suíte de Testes Automatizados

Para executar os testes unitários e de integração sobre as imagens reais de controle:

```bash
uv run --with pytest --with pydantic --with opencv-python-headless --with scipy --with numpy pytest -v
```

---

## 📊 Execução de Benchmarks

Para avaliar o tempo de processamento e métricas de todas as imagens catalogadas no manifesto de referência:

```bash
uv run --with opencv-python-headless --with scipy --with numpy --with pydantic python benchmarks/evaluate_baseline.py
```

O relatório consolidado será gravado em `benchmarks/report_baseline.json` e as imagens anotadas em `output/diagnostics/`.

---

## 📱 Aplicativo Mobile & API Backend

O sistema possui agora um aplicativo móvel (React Native / Expo) e uma API FastAPI dedicada para integrar os algoritmos ao smartphone do laboratório.

### 1. Iniciar o Backend FastAPI

O backend recebe fotos do aplicativo e retorna resultados estruturados em JSON e Base64.
Na raiz do repositório, inicie o servidor:

```bash
uv run --with fastapi --with uvicorn --with python-multipart --with pydantic --with opencv-python-headless --with scipy --with numpy uvicorn api.server:app --host 0.0.0.0 --port 8000 --reload
```

### 2. Iniciar o Aplicativo Expo Mobile

O app Mobile conecta com a API para realizar a análise a partir da câmera do celular.

```bash
cd mobile
# Instalar dependências se for a primeira vez
npm install

# (Opcional) Configurar o IP do servidor FastAPI se estiver rodando em dispositivo físico
# export EXPO_PUBLIC_API_URL=http://<IP_DA_MAQUINA>:8000/api/v1

# Iniciar o Expo Dev Server
npx expo start
```
