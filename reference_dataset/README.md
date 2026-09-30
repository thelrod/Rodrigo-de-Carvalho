# Conjunto de Dados de Referência (Reference Dataset)
*Projeto:* YeastPlate Analyzer  
*Licença:* Creative Commons Attribution 4.0 International (CC-BY 4.0)

---

## 1. Estrutura do Diretório

```
reference_dataset/
├── README.md               # Este documento de proveniência e governança
├── metadata_template.json  # Esquema modelo para anotação estruturada
├── dataset_manifest.json   # Registro completo de todas as imagens e suas divisões
├── raw/                    # Imagens originais imutáveis (nunca editadas)
└── annotations/            # Anotações manuais revisadas (JSON com centróides ou grades)
```

---

## 2. Política de Particionamento e Validação Independente

Para evitar **vazamento de dados (data leakage)** e assegurar validação científica honesta:
1. **Divisão Estrita por Placa/Experimento:** Todas as amostras de uma mesma placa ou sessão de bancada pertencem exclusivamente a uma partição:
   * **Treino/Calibração (Train/Calibration):** 60% das placas.
   * **Validação/Sintonia (Validation/Tuning):** 20% das placas.
   * **Teste Independente Congelado (Frozen Test Set):** 20% das placas.
2. **Critérios Congelados:** Os parâmetros finais e limites de corte do algoritmo devem ser fixados antes da avaliação final no conjunto de teste independente. O conjunto de teste nunca deve ser usado para sintonizar thresholds.

---

## 3. Classificação das Imagens Iniciais

As imagens iniciais fornecidas são catalogadas como amostras da suíte de **teste de robustez/estresse**:
* `SAMPLE_YPD_300mM_LiCl.jpg`: Ensaio de gota em meio YPD com estresse osmótico/iônico (LiCl 300 mM). Contém artefatos de bancada (caneta marcadora no poliestireno e fita crepe).
* `SAMPLE_YPGAL_20mM_LiCl.jpg`: Ensaio de gota em meio YPGal (galactose) com estresse iônico (LiCl 20 mM).
