"""
Contratos formais de dados e schemas Pydantic para o YeastPlate Analyzer.
Conforme especificado em SPEC.md v2.1.0.
"""

from datetime import datetime
from enum import Enum
from typing import Optional, List, Dict
from pydantic import BaseModel, Field, ConfigDict


class MediumType(str, Enum):
    """Meios de cultura suportados para leveduras."""
    YPD = "YPD"
    YPGAL = "YPGal"
    YPGLY = "YPGly"


class ExperimentType(str, Enum):
    """Tipos de ensaios microbiológicos."""
    COLONY_COUNT = "colony_count"
    SPOT_ASSAY = "spot_assay"


class QCStatus(str, Enum):
    """Status consolidado do controle de qualidade da imagem."""
    PASSED = "passed"
    WARNING_REVIEW_REQUIRED = "warning_review_required"
    REJECTED_UNQUANTIFIABLE = "rejected_unquantifiable"


class ImageMetadata(BaseModel):
    """Metadados de contexto experimental e proveniência da amostra."""
    model_config = ConfigDict(frozen=True)

    image_id: str = Field(..., description="Identificador único (UUID ou hash SHA-256)")
    filename: str = Field(..., description="Nome do arquivo da imagem")
    timestamp_capture: datetime = Field(..., description="Data/hora de captura")
    medium: MediumType = Field(..., description="Meio de cultura")
    carbon_source_concentration_pct: float = Field(2.0, ge=0.1, le=10.0, description="Concentração de fonte de C em %")
    stressor: Optional[str] = Field(None, description="Composto químico ou agente de estresse")
    stressor_concentration_mM: Optional[float] = Field(None, ge=0.0, description="Concentração do estressor em mM")
    incubation_time_hours: Optional[float] = Field(None, ge=0.0, le=168.0, description="Tempo de incubação em horas")
    temperature_celsius: float = Field(30.0, ge=15.0, le=45.0, description="Temperatura de incubação em °C")
    strain_id: str = Field(..., description="Identificador da linhagem de levedura")
    plate_id: str = Field(..., description="Identificador físico da placa")
    experiment_type: ExperimentType = Field(..., description="Tipo de ensaio realizado")
    partition: str = Field("stress_test", description="Divisão do dataset: train, validation, test_frozen, stress_test")
    operator_id: Optional[str] = Field(None, description="Nome ou código do operador")
    has_artifacts: bool = Field(False, description="True se contiver anotações, fita ou artefatos severos")


class QCResult(BaseModel):
    """Resultado da avaliação de Controle de Qualidade (QC Camada 1)."""
    model_config = ConfigDict(frozen=True)

    status: QCStatus = Field(..., description="Status consolidado do QC")
    blur_score_laplacian: float = Field(..., description="Variância do operador Laplaciano (foco)")
    fraction_saturated_pixels: float = Field(..., ge=0.0, le=1.0, description="Fração de pixels superexpostos (>=250)")
    fraction_underexposed_pixels: float = Field(..., ge=0.0, le=1.0, description="Fração de pixels subexpostos (<=15)")
    resolution_width_px: int = Field(..., ge=400, description="Largura em pixels da imagem")
    resolution_height_px: int = Field(..., ge=400, description="Altura em pixels da imagem")
    is_plate_fully_visible: bool = Field(..., description="True se a circunferência estiver totalmente contida")
    rejection_reasons: List[str] = Field(default_factory=list, description="Lista de códigos de erro ou avisos de QC")


class PlateROIResult(BaseModel):
    """Geometria da placa de Petri detectada e máscara de análise."""
    model_config = ConfigDict(frozen=True)

    center_x_px: float = Field(..., description="Coordenada X do centro da placa")
    center_y_px: float = Field(..., description="Coordenada Y do centro da placa")
    radius_px: float = Field(..., gt=0.0, description="Raio da borda física da placa")
    exclusion_margin_pct: float = Field(8.0, ge=0.0, le=25.0, description="Margem periférica adaptativa excluída")
    analyzable_area_px: int = Field(..., gt=0, description="Área interna válida para quantificação em pixels")
    excluded_peripheral_area_px: int = Field(..., ge=0, description="Área da coroa circular do menisco excluída")


class SingleColony(BaseModel):
    """Morfometria e posição de uma colônia individual de levedura."""
    model_config = ConfigDict(frozen=True)

    colony_id: int = Field(..., description="Identificador numérico ordinal da colônia")
    centroid_x_px: float = Field(..., description="Centroide X em pixels")
    centroid_y_px: float = Field(..., description="Centroide Y em pixels")
    area_px: int = Field(..., gt=0, description="Área da colônia em pixels")
    circularity: float = Field(..., ge=0.0, le=1.0, description="Métrica 4*pi*A/P^2")
    solidity: float = Field(..., ge=0.0, le=1.0, description="Razão área / convex_hull")
    mean_intensity: float = Field(..., ge=0.0, le=255.0, description="Intensidade média no canal de luminância")
    is_manual_override: bool = Field(False, description="True se inserida ou ajustada manualmente pelo usuário")


class ColonyCountResult(BaseModel):
    """Resultado consolidado do Modo 1 (Contagem de Colônias em Spread Plate)."""
    model_config = ConfigDict(frozen=True)

    total_colonies_auto: int = Field(..., ge=0, description="Contagem puramente algorítmica")
    total_colonies_final: int = Field(..., ge=0, description="Contagem final após revisões por exceção")
    colonies: List[SingleColony] = Field(default_factory=list, description="Lista de colônias detectadas")
    inoculated_volume_ml: Optional[float] = Field(None, gt=0.0, description="Volume plaqueado em mL (ex: 0.1)")
    dilution_factor: Optional[float] = Field(None, ge=1.0, description="Fator de diluição inverso (ex: 1000.0 para 10^-3)")
    cfu_per_ml: Optional[float] = Field(None, ge=0.0, description="Concentração microbiológica calculada em UFC/mL")
    is_in_valid_counting_range: bool = Field(..., description="True se 30 <= N <= 300 (ISO 7218)")
    execution_version: str = Field("2.1.0", description="Versão do pipeline executor")
    random_seed: int = Field(42, description="Semente aleatória determinística")


class SingleSpotMeasurement(BaseModel):
    """Quantificação de uma única gota/spot em ensaio de diluição seriada."""
    model_config = ConfigDict(frozen=True)

    row_idx: int = Field(..., ge=0, description="Índice da linha da grade (0-indexed)")
    col_idx: int = Field(..., ge=0, description="Índice da coluna da grade (0-indexed)")
    strain_id: str = Field(..., description="Linhagem de levedura correspondente")
    dilution_factor: float = Field(..., ge=1.0, description="Fator de diluição desta coluna (ex: 1, 10, 100, 1000)")
    growth_detected: bool = Field(..., description="Métrica primária semiquantitativa: crescimento detectado")
    area_growth_px: int = Field(..., ge=0, description="Área da biomassa do spot em pixels")
    background_corrected_signal: float = Field(..., description="Sinal integrado corrigido pelo fundo em a.u.")
    is_saturated: bool = Field(..., description="True se houver saturação de pixels no spot")
    confidence_score: float = Field(..., ge=0.0, le=1.0, description="Confiança na detecção do spot")


class SpotAssayResult(BaseModel):
    """Resultado consolidado do Modo 2 (Spot Assay / Ensaio de Gota)."""
    model_config = ConfigDict(frozen=True)

    grid_rows: int = Field(..., gt=0, description="Número de linhas da matriz")
    grid_cols: int = Field(..., gt=0, description="Número de colunas da matriz")
    spots: List[SingleSpotMeasurement] = Field(default_factory=list, description="Medições individuais de cada spot")
    max_dilution_with_growth_by_strain: Dict[str, float] = Field(
        default_factory=dict,
        description="Mapeamento da maior diluição com crescimento detectado por linhagem"
    )
    execution_version: str = Field("2.1.0", description="Versão do pipeline executor")
    random_seed: int = Field(42, description="Semente aleatória determinística")
