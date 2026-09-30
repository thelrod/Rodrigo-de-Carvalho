# INVENTORY.md — Inventário de Recursos, Dependências e Licenças
*Projeto:* YeastPlate Analyzer  
*Requisito:* Seção 7 da Revisão 2

---

## 1. Licença do Projeto YeastPlate Analyzer
* **Código-fonte:** MIT License (Permissiva, permitindo reutilização acadêmica, institucional e comercial livre com atribuição).
* **Dados, Anotações e Imagens do Conjunto de Referência:** Creative Commons Attribution 4.0 International (CC-BY 4.0).

---

## 2. Inventário de Recursos Externos e Repositórios Analisados

| Recurso / Repositório | Organismo / Escopo | Licença Original | Compatibilidade | Utilização no Projeto |
| :--- | :--- | :--- | :--- | :--- |
| **AGAR Dataset** (`agar.neurosys.com`) | 5 microrganismos (inclui *Candida albicans*), 18k placas | CC-BY-NC-SA 4.0 | ⚠️ Não-comercial | **Apenas benchmark comparativo externo.** Não utilizaremos pesos treinados diretamente se houver restrição comercial futura. |
| **OpenCFU** (`opencfu.sourceforge.net`) | Colônias bacterianas e fúngicas | GPL v3.0 | ⚠️ Copyleft | **Inspiração algorítmica apenas** (regras de exclusão de menisco e convex hull). Nenhum código C++ será copiado para preservar a licença MIT do nosso projeto. |
| **`majsylw/microbial-counting-review`** | Curadoria de papers e datasets | MIT License | 🟢 Total | Guia bibliográfico e de benchmarks. |
| **`Sri-Karthik-Avala/Bacterial-Colony-Counting...`** | Generalização a meios não vistos | MIT License | 🟢 Total | Referência para técnicas de normalização e invariância de substrato. |
| **`NeuroSYS-pl/objects_counting_dmap`** | Mapas de densidade contínua | MIT License | 🟢 Total | Candidato para expansão na Etapa 4 (densitometria avançada de spots confluentes). |

---

## 3. Inventário de Dependências Diretas em Python

| Biblioteca | Versão Alvo | Licença | Propósito no YeastPlate Analyzer |
| :--- | :--- | :--- | :--- |
| `numpy` | `^1.26.0` | BSD-3-Clause | Operações matriciais vetorizadas e representação `float32` |
| `scipy` | `^1.12.0` | BSD-3-Clause | Transformada de distância, morfologia e estatística descritiva |
| `opencv-python-headless` | `^4.9.0` | Apache 2.0 | Visão computacional determinística (Hough, Watershed, Lab/HSV) |
| `scikit-image` | `^0.22.0` | BSD-3-Clause | Filtros locais de textura, Sauvola thresholding e rotulagem |
| `pandas` | `^2.2.0` | BSD-3-Clause | Estruturação de dados tabulares e exportação CSV/Excel |
| `pydantic` | `^2.6.0` | MIT License | Validação rigorosa de contratos de I/O e metadados |
| `streamlit` | `^1.32.0` | Apache 2.0 | Interface web local responsiva (acesso desktop/mobile) |
| `pytest` | `^8.0.0` | MIT License | Suíte de testes automatizados unitários e de integração |
| `pillow` | `^10.2.0` | HPND | Leitura de metadados EXIF e manipulação de arquivos de imagem |

Todas as dependências diretas possuem licenças permissivas (BSD, MIT, Apache 2.0), garantindo conformidade jurídica completa com a licença MIT do YeastPlate Analyzer.
