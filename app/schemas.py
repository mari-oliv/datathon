#Schemas Pydantic para validação de entrada e saída da API.

from __future__ import annotations

from pydantic import BaseModel, Field


class StudentInput(BaseModel):
    """
    Dados de um estudante para predição de risco de defasagem.

    Todos os campos numéricos aceitam None.
    """

    nivel_defasagem: float | None = Field(
        default=None,
        alias="Nível de Defasagem",
        description="Nível de defasagem do aluno (negativo = defasado)",
        examples=[-1],
    )
    fase: float | None = Field(
        default=None,
        alias="Fase",
        description="Fase atual do aluno no programa",
        examples=[7],
    )
    fase_ideal: str | None = Field(
        default=None,
        alias="Fase ideal",
        description="Fase ideal esperada (string, ex: 'Fase 8 (Universitários)')",
        examples=["Fase 8 (Universitários)"],
    )
    atingiu_ponto_de_virada: str | None = Field(
        default=None,
        alias="Atingiu Ponto de Virada",
        description="'Sim' ou 'Não'",
        examples=["Não"],
    )
    indicador_aprendizagem: float | None = Field(
        default=None,
        alias="Indicador de Aprendizagem",
        description="IDA — nota de 0 a 10",
        examples=[4.0],
    )
    indicador_engajamento: float | None = Field(
        default=None,
        alias="Indicador de Engajamento",
        description="IEG — nota de 0 a 10",
        examples=[4.1],
    )
    indicador_psicossocial: float | None = Field(
        default=None,
        alias="Indicador Psicossocial",
        description="IPS — nota de 0 a 10",
        examples=[5.6],
    )
    indicador_adequacao: float | None = Field(
        default=None,
        alias="Indicador de Adequação ao Nível",
        description="IAN — nota de 0 a 10",
        examples=[5.0],
    )
    indicador_ponto_virada: float | None = Field(
        default=None,
        alias="Indicador de Ponto de Virada",
        description="IPV — nota de 0 a 10",
        examples=[7.278],
    )
    inde: float | None = Field(
        default=None,
        alias="Índice de Desenvolvimento Educacional (INDE)",
        description="INDE — índice geral de desenvolvimento",
        examples=[5.783],
    )

    model_config = {"populate_by_name": True}


class PredictionOutput(BaseModel):
    """Resultado da predição para um único estudante."""

    cluster: int = Field(description="Cluster de risco atribuído (0 a 4)")
    risk_score: float = Field(description="Score de risco calculado (maior = mais risco)")
    risk_level: str = Field(description="Nível de risco: Baixo | Médio | Alto | Crítico")
    gap_fase: float | None = Field(description="Diferença entre fase atual e fase ideal")


class BatchStudentInput(BaseModel):
    """Payload para predição em lote."""

    students: list[StudentInput] = Field(
        description="Lista de estudantes para predição",
        min_length=1,
    )


class BatchPredictionOutput(BaseModel):
    """Resultado da predição em lote."""

    predictions: list[PredictionOutput]
    total: int


class HealthOutput(BaseModel):
    status: str
    model_loaded: bool
    model_k: int | None = None
    features: list[str] | None = None
