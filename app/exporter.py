"""
Utilitário de Exportação Auditável de Relatórios e Imagens Anotadas
=================================================================
Gera CSVs padronizados com metadados experimentais e imagens PNG
em alta resolução com carimbos de versão e rastreabilidade.
"""

import io
import time
import pandas as pd
import cv2
import numpy as np

from yeast_vision.contracts import (
    ImageMetadata,
    QCResult,
    ColonyCountResult,
    SpotAssayResult,
)


def export_colony_count_csv(
    metadata: ImageMetadata,
    qc_result: QCResult,
    count_result: ColonyCountResult,
) -> str:
    """Gera o conteúdo em texto CSV estruturado para contagem de colônias."""
    rows = []
    for col in count_result.colonies:
        rows.append({
            "image_id": metadata.image_id,
            "filename": metadata.filename,
            "plate_id": metadata.plate_id,
            "medium": metadata.medium.value,
            "strain_id": metadata.strain_id,
            "stressor": metadata.stressor or "Nenhum",
            "stressor_concentration_mM": metadata.stressor_concentration_mM or 0.0,
            "qc_status": qc_result.status.value,
            "qc_blur_score": qc_result.blur_score_laplacian,
            "colony_id": col.colony_id,
            "centroid_x_px": col.centroid_x_px,
            "centroid_y_px": col.centroid_y_px,
            "area_px": col.area_px,
            "circularity": col.circularity,
            "solidity": col.solidity,
            "mean_intensity": col.mean_intensity,
            "is_manual_override": col.is_manual_override,
            "total_colonies_plate": count_result.total_colonies_final,
            "inoculated_volume_ml": count_result.inoculated_volume_ml,
            "dilution_factor": count_result.dilution_factor,
            "cfu_per_ml": count_result.cfu_per_ml,
            "in_valid_30_300_range": count_result.is_in_valid_counting_range,
            "pipeline_version": count_result.execution_version,
            "timestamp_export": time.strftime("%Y-%m-%d %H:%M:%S"),
        })

    df = pd.DataFrame(rows)
    return df.to_csv(index=False)


def export_spot_assay_csv(
    metadata: ImageMetadata,
    qc_result: QCResult,
    spot_result: SpotAssayResult,
) -> str:
    """Gera o conteúdo em texto CSV estruturado para ensaio de gota (spotting)."""
    rows = []
    for s in spot_result.spots:
        rows.append({
            "image_id": metadata.image_id,
            "filename": metadata.filename,
            "plate_id": metadata.plate_id,
            "medium": metadata.medium.value,
            "stressor": metadata.stressor or "Controle",
            "stressor_concentration_mM": metadata.stressor_concentration_mM or 0.0,
            "qc_status": qc_result.status.value,
            "qc_blur_score": qc_result.blur_score_laplacian,
            "row_idx": s.row_idx,
            "col_idx": s.col_idx,
            "strain_id": s.strain_id,
            "dilution_factor": s.dilution_factor,
            "growth_detected": s.growth_detected,
            "area_growth_px": s.area_growth_px,
            "background_corrected_signal_au": s.background_corrected_signal,
            "is_saturated": s.is_saturated,
            "confidence_score": s.confidence_score,
            "max_dilution_strain": spot_result.max_dilution_with_growth_by_strain.get(s.strain_id, 0.0),
            "pipeline_version": spot_result.execution_version,
            "timestamp_export": time.strftime("%Y-%m-%d %H:%M:%S"),
        })

    df = pd.DataFrame(rows)
    return df.to_csv(index=False)


def create_annotated_colony_image(
    image_bgr: np.ndarray,
    plate_roi,
    count_result: ColonyCountResult,
) -> np.ndarray:
    """Desenha sobreposições gráficas das colônias detectadas."""
    out = image_bgr.copy()
    cx, cy, r = int(plate_roi.center_x_px), int(plate_roi.center_y_px), int(plate_roi.radius_px)
    r_inner = int(r * (1.0 - plate_roi.exclusion_margin_pct / 100.0))

    # Desenha borda da placa e ROI
    cv2.circle(out, (cx, cy), r, (0, 0, 255), 2)
    cv2.circle(out, (cx, cy), r_inner, (0, 255, 255), 2)

    # Desenha colônias
    for col in count_result.colonies:
        x, y = int(col.centroid_x_px), int(col.centroid_y_px)
        radius = max(3, int(np.sqrt(col.area_px / np.pi)))
        cv2.circle(out, (x, y), radius + 2, (0, 255, 0), 2)
        cv2.circle(out, (x, y), 2, (0, 0, 255), -1)

    return out


def create_annotated_spot_image(
    image_bgr: np.ndarray,
    plate_roi,
    spot_cells,
    spot_result: SpotAssayResult,
) -> np.ndarray:
    """Desenha sobreposições gráficas da grade do spot assay."""
    out = image_bgr.copy()
    cx, cy, r = int(plate_roi.center_x_px), int(plate_roi.center_y_px), int(plate_roi.radius_px)
    r_inner = int(r * (1.0 - plate_roi.exclusion_margin_pct / 100.0))

    cv2.circle(out, (cx, cy), r, (0, 0, 255), 2)
    cv2.circle(out, (cx, cy), r_inner, (0, 255, 255), 2)

    spot_lookup = {(s.row_idx, s.col_idx): s for s in spot_result.spots}

    for r_idx, c_idx, (x1, y1, x2, y2) in spot_cells:
        s_data = spot_lookup.get((r_idx, c_idx))
        if s_data and s_data.growth_detected:
            color = (0, 255, 0)  # Verde = Crescimento detectado
            thickness = 2
        else:
            color = (150, 150, 150)  # Cinza = Sem crescimento
            thickness = 1

        cv2.rectangle(out, (x1, y1), (x2, y2), color, thickness)

    return out
