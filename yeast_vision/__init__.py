"""
YeastPlate Analyzer - Core Scientific Computer Vision Engine
============================================================
Pacote desacoplado para controle de qualidade, detecção de placas,
contagem de colônias e análise de ensaios de gota (spot assays) em
meios de cultura sólidos para leveduras (YPD, YPGal, YPGly).
"""

__version__ = "2.1.0"
__author__ = "Rodrigo de Carvalho"

from yeast_vision.contracts import (
    MediumType,
    ExperimentType,
    QCStatus,
    ImageMetadata,
    QCResult,
    PlateROIResult,
    SingleColony,
    ColonyCountResult,
    SingleSpotMeasurement,
    SpotAssayResult,
)

__all__ = [
    "MediumType",
    "ExperimentType",
    "QCStatus",
    "ImageMetadata",
    "QCResult",
    "PlateROIResult",
    "SingleColony",
    "ColonyCountResult",
    "SingleSpotMeasurement",
    "SpotAssayResult",
]
