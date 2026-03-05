import pandas as pd


def clean_discovery_data(df):
    rename_columns = {
        "Ano nasc": "Ano de Nascimento do Aluno",
        "Idade 22": "Idade do Aluno",
        "Ano ingresso": "Ano de Ingresso na Passos Mágicos",
        "INDE 22": "Índice de Desenvolvimento Educacional (INDE)",
        "Cg": "Classificação Geral (Ranking Geral)",
        "Cf": "Classificação na Fase (Ranking por Fase)",
        "Ct": "Classificação na Turma (Ranking por Turma)",
        "Pedra 20": "Pedra 2020",
        "Pedra 21": "Pedra 2021",
        "Pedra 22": "Pedra 2022",
        "Nº Av": "Quantidade de Avaliações",
        "Avaliador1": "Equipe Avaliadora 1",
        "Rec Av1": "Recomendação da Equipe Avaliadora 1",
        "Avaliador2": "Equipe Avaliadora 2",
        "Rec Av2": "Recomendação da Equipe Avaliadora 2",
        "Avaliador3": "Equipe Avaliadora 3",
        "Rec Av3": "Recomendação da Equipe Avaliadora 3",
        "Avaliador4": "Equipe Avaliadora 4",
        "Rec Av4": "Recomendação da Equipe Avaliadora 4",
        "IAA": "Indicador de Autoavaliação",
        "IEG": "Indicador de Engajamento",
        "IPS": "Indicador Psicossocial",
        "Rec Psicologia": "Recomendação da Equipe de Psicologia",
        "IDA": "Indicador de Aprendizagem",
        "Matem": "Nota Média de Matemática",
        "Portug": "Nota Média de Português",
        "Inglês": "Nota Média de Inglês",
        "Indicado": "Indicado para Bolsa",
        "Atingiu PV": "Atingiu Ponto de Virada",
        "IPV": "Indicador de Ponto de Virada",
        "IAN": "Indicador de Adequação ao Nível",
        "Defas": "Nível de Defasagem",
        "Destaque IEG": "Observações sobre Indicador de Engajamento",
        "Destaque IDA": "Observações sobre Indicador de Aprendizagem",
        "Destaque IPV": "Observações sobre Indicador de Ponto de Virada",
    }

    df_clean = df.rename(columns=rename_columns)

    df_clean.drop(columns=["Nome"], inplace=True)

    return df_clean
