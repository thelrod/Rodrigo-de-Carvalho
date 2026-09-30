# DECISIONS.md — Architecture Decision Records (ADRs)
*Projeto:* YeastPlate Analyzer  
*Padrão:* Michael Nygard / ADR simplificado com evidências científicas

---

## Índice de Decisões

- [ADR-0001: Desacoplamento Estrito entre Motor Científico e Interfaces](#adr-0001-desacoplamento-estrito-entre-motor-científico-e-interfaces)
- [ADR-0002: Caso-Padrão como Placa Limpa e Isolamento de Artefatos em Testes de Estresse](#adr-0002-caso-padrão-como-placa-limpa-e-isolamento-de-artefatos-em-testes-de-estresse)
- [ADR-0003: Rigor Terminológico no Spot Assay — Sinal Integrado (a.u.) e Maior Diluição](#adr-0003-rigor-terminológico-no-spot-assay--sinal-integrado-au-e-maior-diluição)
- [ADR-0004: Representação Numérica em float32 e Prevenção de Overflow](#adr-0004-representação-numérica-em-float32-e-prevenção-de-overflow)
- [ADR-0005: Controle de Qualidade (QC) em Duas Camadas e Veto ao Inpainting](#adr-0005-controle-de-qualidade-qc-em-duas-camadas-e-veto-ao-inpainting)
- [ADR-0006: Mitigação de Travamentos e Conflitos de Sincronização no Microsoft OneDrive](#adr-0006-mitigação-de-travamentos-e-conflitos-de-sincronização-no-microsoft-onedrive)

---

### ADR-0001: Desacoplamento Estrito entre Motor Científico e Interfaces
* **Data:** 2026-09-30
* **Status:** Aprovado
* **Contexto:** O projeto necessita de uma interface rápida e acessível pelo navegador do smartphone na bancada (Streamlit), mas com planos futuros de migração para PWA ou API FastAPI, além de permitir testes automatizados headless e orquestração por agentes assíncronos (Google Jules).
* **Decisão:** O motor científico será empacotado como uma biblioteca pura em Python chamada `yeast_vision`, sem nenhuma importação ou dependência do Streamlit. A interface em `app/` apenas consome `yeast_vision` através de contratos Pydantic estritos.
* **Consequências:**
  * *Positivas:* Alta testabilidade via `pytest`, reutilização completa do código, zero acoplamento de estado da UI com a lógica bioestatística.
  * *Negativas:* Necessidade de serializar estruturas de dados e manter contratos formais de interface.

---

### ADR-0002: Caso-Padrão como Placa Limpa e Isolamento de Artefatos em Testes de Estresse
* **Data:** 2026-09-30
* **Status:** Aprovado (Revisão 2)
* **Contexto:** As fotos iniciais enviadas continham fita crepe e escrita de marcador ("300mM LiCl", "06/02"). Projetar o pipeline central para remover caneta de forma fixa corria o risco de causar *overfitting* de pré-processamento, degradando a performance no uso cotidiano de placas limpas.
* **Decisão:** O pipeline principal assume **placas limpas** como o caso de uso prioritário e nominal. A remoção de caneta piloto e fitas adesivas é classificada como **cenário de robustez secundário**, alocada na suíte de testes de estresse.
* **Consequências:**
  * *Positivas:* Algoritmo mais limpo, rápido e menos suscetível a remover colônias escuras ou pigmentadas por engano.
  * *Negativas:* Placas de rotina com escrita excessiva sobre o ágar serão encaminhadas para revisão humana pelo QC.

---

### ADR-0003: Rigor Terminológico no Spot Assay — Sinal Integrado (a.u.) e Maior Diluição
* **Data:** 2026-09-30
* **Status:** Aprovado (Revisão 2)
* **Contexto:** Fotografias tiradas por câmeras de celular com iluminação ambiente e reflexos não possuem calibração fotométrica de transmitância para serem chamadas de "Densidade Óptica (OD)" ou "biomassa absoluta".
* **Decisão:** O termo "IOD/OD" fica terminantemente substituído por **Sinal Integrado Corrigido pelo Fundo**, expresso explicitamente em unidades arbitrárias (a.u.). A métrica primária do ensaio de gota passa a ser a **maior diluição seriada com crescimento detectável**, acompanhada da área em pixels e sinal integrado como variáveis complementares.
* **Consequências:**
  * *Positivas:* Integridade científica publication-grade; evita rejeição metodológica em artigos científicos de periódicos de microbiologia e genética.
  * *Negativas:* Exige que a UI explique a natureza semiquantitativa da medida ao usuário.

---

### ADR-0004: Representação Numérica em float32 e Prevenção de Overflow
* **Data:** 2026-09-30
* **Status:** Aprovado (Revisão 2)
* **Contexto:** Imagens do OpenCV são carregadas por padrão como inteiros não sinalizados de 8 bits (`np.uint8`, intervalo 0–255). Operações como $L \times (255 - S)$ causam *integer overflow* silencioso (ex.: $200 \times 100 = 20000 \implies 20000 \pmod{256} = 32$).
* **Decisão:** Todas as operações aritméticas espaciais e espectrais devem converter as imagens para `np.float32` normalizado no intervalo $[0.0, 1.0]$ antes de qualquer multiplicação ou combinação linear, retornando a `uint8` apenas para renderização visual.
* **Consequências:**
  * *Positivas:* Eliminação de 100% dos bugs de *overflow/underflow* numérico em máscaras de segmentação.
  * *Negativas:* Leve aumento transitório no consumo de memória RAM (4x por frame), plenamente aceitável em computadores modernos e celulares.

---

### ADR-0005: Controle de Qualidade (QC) em Duas Camadas e Veto ao Inpainting
* **Data:** 2026-09-30
* **Status:** Aprovado (Revisão 2)
* **Contexto:** Detectar simultaneamente todos os artefatos visuais (desfoque, condensação, reflexos poliestireno, perspectiva) pode atrasar o desenvolvimento e gerar heurísticas não testadas. Além disso, reconstruir áreas danificadas por algoritmos generativos/inpainting compromete a integridade científica.
* **Decisão:**
  1. O QC é dividido em **Camada 1** (determinística imediata: desfoque Laplaciano, saturação do histograma, corte de borda e resolução) e **Camada 2** (refinada na Etapa 2: condensação, anéis de reflexo).
  2. É **expressamente vetado o uso de inpainting** para preencher ou inventar colônias em regiões obstruídas. Regiões comprometidas são marcadas como `UNQUANTIFIABLE`.
* **Consequências:**
  * *Positivas:* Rigor bioético inquestionável e desenvolvimento pragmático por fases.
  * *Negativas:* Placas com condensação massiva não terão suas áreas afetadas computadas automaticamente.

---

### ADR-0006: Mitigação de Travamentos e Conflitos de Sincronização no Microsoft OneDrive
* **Data:** 2026-09-30
* **Status:** Aprovado
* **Contexto:** O workspace está localizado em uma pasta sincronizada pelo Microsoft OneDrive (`OneDrive\Documents\UFRJ\...`). O OneDrive frequentemente causa *file locks*, lentidão em suítes de testes (`pytest`), conflitos de nomes em branches do git e corrupção de caches do Python.
* **Decisão:**
  1. O arquivo `.gitignore` isola estritamente `.venv/`, `__pycache__/`, `.pytest_cache/`, pastas temporárias e saídas intermediárias.
  2. Recomendação explícita para que o ambiente virtual seja mantido localmente sem sincronização ou instalado via `uv`/`virtualenv` apontando para pastas locais não bloqueadas.
* **Consequências:**
  * *Positivas:* Execução rápida de testes, zero conflitos de sincronização no OneDrive e repositório Git limpo.
