# PROTOCOL.md — Protocolo Padronizado de Aquisição Fotográfica de Bancada
*Projeto:* YeastPlate Analyzer  
*Aplicação:* Fotografia de placas de Petri para leveduras em meios sólidos (YPD, YPGal, YPGly)  
*Objetivo:* Minimizar variabilidade pré-analítica e garantir a conformidade com o Controle de Qualidade (QC)

---

## 1. Preparação da Bancada e Geometria

1. **Fundo Padronizado:**
   * Utilizar uma superfície **preta fosca e não reflexiva** (ex.: folha de EVA preto, cartolina preta fosca ou base de caixa de documentação fotográfica).
   * Limpar a superfície antes de posicionar a placa para remover resíduos de poeira ou partículas brancas.
2. **Posicionamento da Câmera / Smartphone:**
   * O sensor da câmera deve estar **rigorosamente perpendicular ($90^\circ$)** ao plano do ágar.
   * Evitar fotografar com inclinação angular (perspectiva), pois distorce a área dos spots e o contorno circular da placa.
   * Recomenda-se o uso de um suporte estático (tripé de bancada, braço articulado ou gabarito de altura fixa a aproximadamente $15\text{ a }25\text{ cm}$ da placa).
3. **Enquadramento:**
   * A placa de Petri deve ocupar entre **$70\%$ e $85\%$** da largura do quadro fotográfico.
   * A borda plástica externa inteira deve estar visível (placas cortadas são rejeitadas pelo QC com o erro `QC_PLATE_CLIPPED`).

---

## 2. Iluminação e Manipulação da Placa

1. **Iluminação Difusa:**
   * A iluminação deve ser uniforme em toda a extensão do ágar.
   * **Proibido usar flash direto da câmera:** o flash em plástico ou ágar úmido gera reflexos especulares intensos que cegam o algoritmo.
   * Evitar luzes pontuais de teto posicionadas diretamente acima da placa. A melhor iluminação é lateral difusa ou luz indireta de laboratório.
2. **Manipulação da Tampa:**
   * **Retirar a tampa plástica antes de fotografar:** A tampa acumula microgotículas de condensação e reflete a luz do ambiente. Fotografar a placa aberta por alguns segundos sobre a bancada limpa elimina a grande maioria dos reflexos.
   * Caso a placa esteja muito condensada na borda interna, deixe-a entreaberta por 1 minuto em fluxo laminar ou limpe a borda externa antes do registro.
3. **Placa Limpa (Caso-Padrão):**
   * Escrever dados de identificação na **lateral da borda** ou na **fita na base inferior da placa**, evitando ao máximo anotações com caneta marcadora sobre a área útil do ágar onde colônias serão contadas.

---

## 3. Configurações da Câmera (Smartphone / Câmera Digital)

Antes de capturar a série de imagens:

| Configuração | Instrução Obrigatória | Justificativa Científica |
| :--- | :--- | :--- |
| **Flash** | ❌ **Desativado** | Evita saturação de pixels por reflexo especular. |
| **HDR (High Dynamic Range)** | ❌ **Desativado** | Algoritmos de HDR mesclam exposições e alteram artificialmente o contraste local das colônias. |
| **Filtros / Modo Retrato / IA** | ❌ **Desativados** | Modos de embelezamento e otimizadores de cena aplicam suavizações não lineares que apagam microcolônias. |
| **Formato de Arquivo** | 🟢 **RAW (DNG) ou JPEG Alta Qualidade** | Preserva a faixa dinâmica real e minimiza artefatos de compressão por blocos de 8x8 pixels. |
| **Trava de Foco (AF-Lock)** | 🔒 **Travado no centro da placa** | Toque na tela sobre o ágar e mantenha pressionado para travar o foco em toda a série. |
| **Trava de Exposição e Balanço de Branco** | 🔒 **Travados (AE/WB-Lock)** | Garante que placas controle e estresse fotografadas em sequência compartilhem a mesma escala de intensidade luminosa. |

---

## 4. Marcador de Escala e Registro de Metadados

1. **Calibração Espacial:**
   * Placas de Petri plásticas descartáveis de bancada possuem diâmetro padrão nominal de **$90\text{ mm}$**. O software utiliza esse valor por padrão para conversões relativas.
   * Opcionalmente, posicione uma pequena escala milimetrada limpa no canto inferior da bancada fora da placa.
2. **Metadados Mínimos Imediatos:**
   Para cada foto capturada, anote no caderno de laboratório ou planilha vinculada:
   * Identificador do arquivo da foto (ex.: `IMG_20260206_001.jpg`).
   * Meio de cultura: `YPD`, `YPGal` ou `YPGly`.
   * Estressor e concentração (ex.: `300 mM LiCl`, `Controle`).
   * Linhagem de levedura (ex.: `BY4741`, `WT`, `mutante X`).
   * Tipo de ensaio: `Colony Count` (Spread plate) ou `Spot Assay` (Grade de gotas).
