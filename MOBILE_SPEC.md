# MOBILE_SPEC.md — Mobile Application Specification for Jules
*Projeto:* YeastPlate Analyzer Mobile Client  
*Target:* Mobile Application (React Native / Expo ou Flutter / PWA)  
*Status:* Ready for Jules Cloud Implementation

---

## 1. Visão Geral do Aplicativo Mobile

O **YeastPlate Analyzer Mobile** é um aplicativo móvel voltado para microbiologistas e geneticistas na bancada de laboratório. O objetivo é permitir que o pesquisador aponte a câmera do smartphone diretamente para a placa de Petri, fotografe a cultura de leveduras (*Saccharomyces cerevisiae*) e obtenha imediatamente:
1. **Contagem de Colônias (Modo 1):** UFC/mL, identificação de colônias e validação da faixa ISO 7218 (30 a 300 colônias).
2. **Ensaio de Gota / Spot Assay (Modo 2):** Densitometria relativa (sinal integrado líquido em a.u.) e identificação da **maior diluição seriada com crescimento** por linhagem.

---

## 2. Requisitos de Interface e Experiência do Usuário (Mobile UX)

### Tela 1: Câmera de Bancada com Guia Visual (Petri Dish Guide)
* **Visor da Câmera em Tempo Real:** Utiliza a câmera traseira do smartphone.
* **Gabarito Visual de Enquadramento:** Círculo semitransparente na tela para orientar o pesquisador a centralizar a placa de Petri de 90 mm, ocupando entre 70% e 85% do quadro.
* **Sensor de Nivelamento (Giroscópio):** Indicador visual (verde/amarelo) que avisa se o smartphone está perpendicular ($90^\circ$) ao plano da placa, conforme exigido em `PROTOCOL.md`.
* **Botão de Captura Rápida:** Dispara o foco contínuo e captura em alta resolução sem flash.
* **Alternativa de Galeria:** Botão secundário para importar foto já salva no dispositivo.

### Tela 2: Controle de Qualidade e Processamento Imediato
* **Cards de QC:**
  * Foco / Nitidez (Laplaciano)
  * Saturação de Pixels (alerta se houver reflexos especulares)
  * Resolução e Enquadramento da Placa
* Se a foto tiver reflexo ou corte, exibe aviso suave recomendando nova captura.

### Tela 3: Dashboard de Bioanálise e Sobreposição Gráfica (Overlay)
* **Modo 1 (Colônias):**
  * Imagem da placa com círculos verdes sobre cada colônia detectada e ponto vermelho no centroide.
  * Card com contagem total de colônias e selo de conformidade ISO 7218 (30–300).
  * Entrada rápida de volume plaqueado ($V$, ex: $0.1\text{ mL}$) e fator de diluição ($d$, ex: $10^3$) para cálculo instantâneo de $\text{UFC/mL}$.
* **Modo 2 (Spot Assay):**
  * Grade matricial sobreposta ($4 \times 6$ ajustável com pinça de toque).
  * Caixas verdes para gotas com crescimento e cinzas para gotas sem crescimento.
  * Tabela sintética da **Maior Diluição com Crescimento por Linhagem**.
* **Ajuste Automático:**
  * Exclusão periférica do menisco (OpenCFU) e área mínima da colônia calibradas automaticamente pela escala de 90 mm.

### Tela 4: Compartilhamento e Exportação
* Botão para exportar relatório CSV padronizado (compatível com `app/exporter.py`).
* Botão para salvar imagem diagnóstica anotada na galeria ou compartilhar via e-mail / WhatsApp / Nuvem.

---

## 3. Arquitetura Técnica e Conexão com o Motor `yeast_vision`

O aplicativo mobile pode ser estruturado em duas abordagens compatíveis:
1. **Cliente Mobile + API Backend:**
   * O aplicativo React Native / Expo se comunica via requisições HTTP REST (multipart/form-data) com uma API FastAPI leve que executa o pacote `yeast_vision` já testado em `yeast_vision/`.
   * Endpoints principais:
     * `POST /api/v1/qc`: Recebe imagem e retorna `QCResult`.
     * `POST /api/v1/colony-count`: Recebe imagem + máscara e retorna `ColonyCountResult`.
     * `POST /api/v1/spot-assay`: Recebe imagem + parâmetros de grade e retorna `SpotAssayResult`.
2. **Progressive Web App (PWA Mobile-First) ou React Native / Expo:**
   * Código moderno em TypeScript / JavaScript com Tailwind ou componentes nativos táteis.

---

## 4. Instruções para o Google Jules

1. Implemente a estrutura do cliente mobile dentro do repositório (diretório `mobile/` ou `client-mobile/`).
2. Implemente a API FastAPI correspondente em `api/server.py` que importa diretamente os contratos e funções de `yeast_vision`.
3. Garanta que o botão de câmera capture a foto em resolução nativa do sensor e envie para processamento.
4. Adicione testes para os novos endpoints da API e instruções no `README.md`.
