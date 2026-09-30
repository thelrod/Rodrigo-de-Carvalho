"""
Módulo de Benchmark e Avaliação dos Baselines da Etapa 2
========================================================
Executa o pipeline em todas as imagens catalogadas no dataset_manifest.json,
mede tempos de processamento, extrai métricas de QC, plate detection e spot assay,
e gera o relatório estruturado em benchmarks/report_baseline.json.
"""

import os
import sys
import json
import time
import cv2
import numpy as np

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from yeast_vision.qc import evaluate_image_quality
from yeast_vision.plate import detect_petri_dish
from yeast_vision.spot import run_spot_assay_analysis
from yeast_vision.colony import run_colony_counting

MANIFEST_PATH = os.path.join(BASE_DIR, "reference_dataset", "dataset_manifest.json")
REPORT_PATH = os.path.join(BASE_DIR, "benchmarks", "report_baseline.json")
DIAGNOSTICS_DIR = os.path.join(BASE_DIR, "output", "diagnostics")


def run_benchmark():
    os.makedirs(DIAGNOSTICS_DIR, exist_ok=True)

    with open(MANIFEST_PATH, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    results = {
        "benchmark_timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "pipeline_version": "2.1.0",
        "total_images_evaluated": len(manifest["images"]),
        "images_summary": [],
        "overall_metrics": {
            "avg_qc_time_ms": 0.0,
            "avg_plate_detection_time_ms": 0.0,
            "avg_spot_analysis_time_ms": 0.0,
            "qc_passed_count": 0,
            "qc_warning_count": 0,
            "qc_rejected_count": 0,
        }
    }

    qc_times = []
    plate_times = []
    spot_times = []

    for img_meta in manifest["images"]:
        img_rel_path = img_meta["relative_path"]
        img_full_path = os.path.join(BASE_DIR, "reference_dataset", img_rel_path)

        if not os.path.exists(img_full_path):
            print(f"Aviso: Arquivo {img_full_path} não encontrado, pulando.")
            continue

        img_bgr = cv2.imread(img_full_path)
        h, w = img_bgr.shape[:2]

        # 1. Detecção da Placa & Medição de Tempo
        t0 = time.perf_counter()
        plate_roi, mask = detect_petri_dish(img_bgr, exclusion_margin_pct=8.0)
        t_plate = (time.perf_counter() - t0) * 1000.0
        plate_times.append(t_plate)

        # 2. Avaliação de QC & Medição de Tempo
        t0 = time.perf_counter()
        qc = evaluate_image_quality(
            img_bgr,
            plate_circle=(plate_roi.center_x_px, plate_roi.center_y_px, plate_roi.radius_px)
        )
        t_qc = (time.perf_counter() - t0) * 1000.0
        qc_times.append(t_qc)

        if qc.status.value == "passed":
            results["overall_metrics"]["qc_passed_count"] += 1
        elif qc.status.value == "warning_review_required":
            results["overall_metrics"]["qc_warning_count"] += 1
        else:
            results["overall_metrics"]["qc_rejected_count"] += 1

        # 3. Análise do Ensaio de Gota (Spot Assay)
        t0 = time.perf_counter()
        spot_res = run_spot_assay_analysis(img_bgr, mask, grid_rows=4, grid_cols=6)
        t_spot = (time.perf_counter() - t0) * 1000.0
        spot_times.append(t_spot)

        # 4. Geração de Imagem Diagnóstica com Anotações Visuais
        annotated = img_bgr.copy()
        # Desenha círculo da placa e área útil
        cx, cy, r = int(plate_roi.center_x_px), int(plate_roi.center_y_px), int(plate_roi.radius_px)
        r_inner = int(r * 0.92)
        cv2.circle(annotated, (cx, cy), r, (0, 0, 255), 2)  # Borda externa (vermelha)
        cv2.circle(annotated, (cx, cy), r_inner, (0, 255, 255), 2)  # Borda interna de análise (amarela)

        # Desenha os spots detectados
        spots_growth_count = 0
        for s in spot_res.spots:
            if s.growth_detected:
                spots_growth_count += 1

        diag_filename = f"annotated_{img_meta['filename']}"
        diag_path = os.path.join(DIAGNOSTICS_DIR, diag_filename)
        cv2.imwrite(diag_path, annotated)

        img_report = {
            "image_id": img_meta["image_id"],
            "filename": img_meta["filename"],
            "medium": img_meta["medium"],
            "stressor": img_meta.get("stressor"),
            "resolution": f"{w}x{h}",
            "qc_status": qc.status.value,
            "blur_score": qc.blur_score_laplacian,
            "qc_reasons": qc.rejection_reasons,
            "plate_detected": {
                "center": [plate_roi.center_x_px, plate_roi.center_y_px],
                "radius_px": plate_roi.radius_px,
                "analyzable_area_px": plate_roi.analyzable_area_px,
            },
            "spot_assay": {
                "total_spots": len(spot_res.spots),
                "spots_with_growth": spots_growth_count,
                "max_dilution_by_strain": spot_res.max_dilution_with_growth_by_strain,
            },
            "timings_ms": {
                "qc": round(t_qc, 2),
                "plate_detection": round(t_plate, 2),
                "spot_analysis": round(t_spot, 2),
                "total": round(t_qc + t_plate + t_spot, 2),
            },
            "diagnostic_image": diag_filename,
        }
        results["images_summary"].append(img_report)

    if qc_times:
        results["overall_metrics"]["avg_qc_time_ms"] = round(float(np.mean(qc_times)), 2)
        results["overall_metrics"]["avg_plate_detection_time_ms"] = round(float(np.mean(plate_times)), 2)
        results["overall_metrics"]["avg_spot_analysis_time_ms"] = round(float(np.mean(spot_times)), 2)

    with open(REPORT_PATH, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    print(f"Benchmark concluído com sucesso!")
    print(f"Relatório gerado em: {REPORT_PATH}")
    print(f"Imagens diagnósticas em: {DIAGNOSTICS_DIR}")
    return results


if __name__ == "__main__":
    run_benchmark()
