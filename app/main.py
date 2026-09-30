"""
YeastPlate Analyzer - Interface Interativa de Bancada (Streamlit UI)
==================================================================
Aplicativo web local responsivo, acessível via navegador de desktop
ou smartphone, para contagem de colônias e ensaios de gota em leveduras.
"""

import os
import sys
import time
from datetime import datetime
import streamlit as st
import cv2
import numpy as np
import pandas as pd

# Adiciona diretório raiz do projeto ao path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from yeast_vision.contracts import (
    MediumType,
    ExperimentType,
    QCStatus,
    ImageMetadata,
)
from yeast_vision.qc import evaluate_image_quality
from yeast_vision.plate import detect_petri_dish
from yeast_vision.colony import run_colony_counting
from yeast_vision.spot import run_spot_assay_analysis, detect_grid_cells
from app.exporter import (
    export_colony_count_csv,
    export_spot_assay_csv,
    create_annotated_colony_image,
    create_annotated_spot_image,
)

# Configuração da página
st.set_page_config(
    page_title="YeastPlate Analyzer",
    page_icon="🔬",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.title("🔬 YeastPlate Analyzer")
st.caption("Bioanálise Automatizada de Leveduras (*S. cerevisiae*) — UFRJ | v2.1.0")

# --- BARRA LATERAL: PARÂMETROS E METADADOS ---
st.sidebar.header("⚙️ Configurações do Ensaio")

mode = st.sidebar.radio(
    "Modo de Operação:",
    [
        "Modo 2: Ensaio de Gota / Spotting Assay",
        "Modo 1: Contagem de Colônias (Spread Plate)",
    ],
    index=0,
)

st.sidebar.subheader("📋 Metadados da Amostra")
medium_str = st.sidebar.selectbox("Meio de Cultura:", ["YPD", "YPGal", "YPGLy"], index=0)
medium = MediumType(medium_str)

strain_id = st.sidebar.text_input("Linhagem de Levedura:", value="BY4741 (Grid 4x6)")
stressor = st.sidebar.text_input("Estressor (ou vazio):", value="LiCl")
stressor_conc = st.sidebar.number_input("Concentração do Estressor (mM):", min_value=0.0, value=300.0, step=10.0)
plate_id = st.sidebar.text_input("Identificador da Placa:", value="PLACA_01")

st.sidebar.subheader("📐 Geometria da Placa")
margin_pct = st.sidebar.slider("Exclusão Periférica Adaptativa (% raio):", 0.0, 20.0, 8.0, step=0.5)

if "Modo 1" in mode:
    st.sidebar.subheader("🧫 Parâmetros de Contagem")
    inoc_vol = st.sidebar.number_input("Volume Plaqueado (mL):", min_value=0.01, max_value=2.0, value=0.10, step=0.05)
    dil_factor = st.sidebar.number_input("Fator de Diluição (ex: 1000 para 10^-3):", min_value=1.0, value=1000.0, step=10.0)
    det_thresh = st.sidebar.slider("Sensibilidade do Limiar:", 0.05, 0.50, 0.20, step=0.02)
    min_area = st.sidebar.slider("Área Mínima da Colônia (px):", 5, 100, 12, step=1)
else:
    st.sidebar.subheader("🎯 Parâmetros da Grade de Spots")
    grid_rows = st.sidebar.number_input("Linhas da Matriz:", min_value=1, max_value=16, value=4, step=1)
    grid_cols = st.sidebar.number_input("Colunas da Matriz:", min_value=1, max_value=24, value=6, step=1)

# --- ÁREA PRINCIPAL: CARREGAMENTO DA IMAGEM ---
col_src1, col_src2 = st.columns([1, 1])

with col_src1:
    source_choice = st.radio(
        "Origem da Foto da Placa:",
        ["Amostra do Laboratório (Fotos de Controle)", "Fazer Upload de Nova Foto (Desktop / Smartphone)"],
        index=0,
    )

raw_samples_dir = os.path.join(BASE_DIR, "reference_dataset", "raw")
sample_files = [f for f in os.listdir(raw_samples_dir) if f.lower().endswith(('.jpg', '.jpeg', '.png'))] if os.path.exists(raw_samples_dir) else []

image_bgr = None
selected_filename = "upload.jpg"

if source_choice == "Amostra do Laboratório (Fotos de Controle)" and sample_files:
    selected_sample = st.selectbox("Selecione a Placa de Teste:", sample_files, index=0)
    selected_filename = selected_sample
    img_path = os.path.join(raw_samples_dir, selected_sample)
    image_bgr = cv2.imread(img_path)
else:
    uploaded_file = st.file_uploader("Envie a foto da placa de Petri:", type=["jpg", "jpeg", "png"])
    if uploaded_file is not None:
        file_bytes = np.asarray(bytearray(uploaded_file.read()), dtype=np.uint8)
        image_bgr = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)
        selected_filename = uploaded_file.name

if image_bgr is None:
    st.info("👆 Selecione uma amostra de teste acima ou faça upload de uma foto da placa de Petri para iniciar a análise.")
    st.stop()

# --- EXECUÇÃO DO PIPELINE DE VISÃO COMPUTACIONAL ---
with st.spinner("Processando placa e executando controle de qualidade..."):
    # 1. Detecção da Placa e ROI
    plate_roi, mask = detect_petri_dish(image_bgr, exclusion_margin_pct=margin_pct)

    # 2. Avaliação de Controle de Qualidade (QC)
    qc = evaluate_image_quality(
        image_bgr,
        plate_circle=(plate_roi.center_x_px, plate_roi.center_y_px, plate_roi.radius_px),
    )

    # Constrói metadados
    metadata = ImageMetadata(
        image_id=f"IMG_{int(time.time())}",
        filename=selected_filename,
        timestamp_capture=datetime.now(),
        medium=medium,
        carbon_source_concentration_pct=2.0,
        stressor=stressor if stressor else None,
        stressor_concentration_mM=stressor_conc if stressor else None,
        strain_id=strain_id,
        plate_id=plate_id,
        experiment_type=ExperimentType.COLONY_COUNT if "Modo 1" in mode else ExperimentType.SPOT_ASSAY,
        partition="analysis_session",
    )

# --- PAINEL DE CONTROLE DE QUALIDADE (QC DASHBOARD) ---
st.markdown("### 🛡️ Controle de Qualidade da Imagem (QC)")

q1, q2, q3, q4 = st.columns(4)

status_color = "green" if qc.status == QCStatus.PASSED else ("orange" if qc.status == QCStatus.WARNING_REVIEW_REQUIRED else "red")
q1.metric("Status da Aquisição", qc.status.value.upper())
q2.metric("Nitidez / Foco (Laplaciano)", f"{qc.blur_score_laplacian:.1f}", delta="OK (Foco Nítido)" if qc.blur_score_laplacian >= 100 else "Alerta Desfoque")
q3.metric("Saturação de Pixels", f"{qc.fraction_saturated_pixels * 100:.2f}%", delta="Normal" if qc.fraction_saturated_pixels < 0.05 else "Alerta Reflexo", delta_color="inverse")
q4.metric("Resolução", f"{qc.resolution_width_px} x {qc.resolution_height_px} px")

if qc.rejection_reasons:
    st.warning(f"⚠️ **Avisos do QC:** {', '.join(qc.rejection_reasons)}")
else:
    st.success("✅ **Imagem aprovada pelo Controle de Qualidade com conformidade fotométrica plena.**")

st.markdown("---")

# --- RESULTADOS ESPECÍFICOS POR MODO ---
if "Modo 1" in mode:
    # MODO 1: CONTAGEM DE COLÔNIAS
    with st.spinner("Segmentando colônias via Watershed com marcadores..."):
        count_res = run_colony_counting(
            image_bgr,
            mask,
            inoculated_volume_ml=inoc_vol,
            dilution_factor=dil_factor,
            detection_threshold=det_thresh,
            min_area_px=min_area,
        )

    # Métricas principais
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Colônias Detectadas", count_res.total_colonies_auto)
    m2.metric("Faixa Válida (30–300)", "SIM (Confiável)" if count_res.is_in_valid_counting_range else "NÃO (Fora da Faixa)")
    m3.metric("UFC/mL Estimado", f"{count_res.cfu_per_ml:,.0f} UFC/mL" if count_res.cfu_per_ml else "N/A")
    m4.metric("Área Útil Analisada", f"{plate_roi.analyzable_area_px:,} px")

    # Visualização
    annotated_img = create_annotated_colony_image(image_bgr, plate_roi, count_res)

    tab_vis1, tab_vis2, tab_data = st.tabs(["🖼️ Imagem Anotada com Centróides", "⚪ Máscara Binária da Placa", "📊 Tabela Morfométrica"])

    with tab_vis1:
        st.image(cv2.cvtColor(annotated_img, cv2.COLOR_BGR2RGB), caption=f"Colônias identificadas (Total: {count_res.total_colonies_final})", use_column_width=True)

    with tab_vis2:
        st.image(mask, caption="Máscara da Área Útil (Exclusão periférica do menisco)", use_column_width=True)

    with tab_data:
        if count_res.colonies:
            df_col = pd.DataFrame([c.model_dump() for c in count_res.colonies])
            st.dataframe(df_col, use_container_width=True)
            csv_data = export_colony_count_csv(metadata, qc, count_res)
            st.download_button("📥 Baixar Relatório Completo (CSV)", data=csv_data, file_name=f"colony_count_{selected_filename}.csv", mime="text/csv")
        else:
            st.info("Nenhuma colônia detectada com os parâmetros atuais.")

else:
    # MODO 2: SPOT ASSAY / ENSAIO DE GOTA
    with st.spinner("Analisando grade de diluição seriada e sinal integrado..."):
        spot_res = run_spot_assay_analysis(image_bgr, mask, grid_rows=int(grid_rows), grid_cols=int(grid_cols))
        spot_cells = detect_grid_cells(image_bgr, mask, grid_rows=int(grid_rows), grid_cols=int(grid_cols))

    # Métricas principais
    s1, s2, s3, s4 = st.columns(4)
    total_spots = len(spot_res.spots)
    growth_spots = sum(1 for s in spot_res.spots if s.growth_detected)

    s1.metric("Gotas na Grade", total_spots)
    s2.metric("Gotas com Crescimento", f"{growth_spots} / {total_spots}")
    s3.metric("Linhagens Avaliadas", len(spot_res.max_dilution_with_growth_by_strain))
    s4.metric("Métrica Primária", "Maior Diluição Detectada")

    annotated_spot = create_annotated_spot_image(image_bgr, plate_roi, spot_cells, spot_res)

    tab_vis1, tab_dil, tab_data = st.tabs(["🎯 Grade de Diluição Sobreposta", "📈 Maior Diluição por Linhagem", "📊 Medições Detalhadas de Sinal"])

    with tab_vis1:
        st.image(cv2.cvtColor(annotated_spot, cv2.COLOR_BGR2RGB), caption="Grade de spots (Verde = Crescimento detectado, Cinza = Sem crescimento)", use_column_width=True)

    with tab_dil:
        st.subheader("Métrica Primária: Maior Diluição com Crescimento")
        df_dil = pd.DataFrame(
            [{"Linhagem": k, "Maior Diluição Detectada": f"10^{int(np.log10(v))}" if v > 1.0 else ("1 (Puro)" if v == 1.0 else "Nenhum Crescimento")}
             for k, v in spot_res.max_dilution_with_growth_by_strain.items()]
        )
        st.table(df_dil)

    with tab_data:
        df_spots = pd.DataFrame([s.model_dump() for s in spot_res.spots])
        st.dataframe(df_spots, use_container_width=True)
        csv_spot_data = export_spot_assay_csv(metadata, qc, spot_res)
        st.download_button("📥 Baixar Relatório de Densitometria do Spot Assay (CSV)", data=csv_spot_data, file_name=f"spot_assay_{selected_filename}.csv", mime="text/csv")

st.markdown("---")
st.caption("YeastPlate Analyzer • Desenvolvido para o Laboratório de Leveduras da UFRJ • Conformidade com SPEC.md v2.1.0 e ADRs 1–6")
