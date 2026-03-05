import numpy as np
import pandas as pd
from src.processing_and_models import (
    parse_fase_ideal,
    normalize_bool_sim_nao,
    standardize_numpy,
    kmeans_numpy,
    simulate_cluster_impact,
    predict_kmeans_model,
)


class TestParseFaseIdeal:
    def test_extracts_number_from_string(self):
        # GIVEN - WHEN - THEN
        assert parse_fase_ideal("3ª série") == 3.0

    def test_returns_nan_for_null_cell(self):
        # GIVEN - WHEN - THEN
        assert np.isnan(parse_fase_ideal(np.nan))


class TestNormalizeBoolSimNao:
    def test_normalizes_positive_values_to_true(self):
        # GIVEN
        s = pd.Series(["Sim", "1", "yes"])
        # WHEN
        result = normalize_bool_sim_nao(s)
        # THEN
        assert result.tolist() == [True, True, True]

    def test_non_positive_values_are_false(self):
        # GIVEN
        s = pd.Series(["não", "false", "no", None])
        # WHEN
        result = normalize_bool_sim_nao(s)
        # THEN
        assert result.tolist() == [False, False, False, False]


class TestStandardizeNumpy:
    def test_calculates_correct_mean_and_std(self):
        # GIVEN
        X = np.array([[1.0], [3.0], [5.0]])
        # WHEN
        _, mu, sigma = standardize_numpy(X)
        # THEN
        assert np.allclose(mu, [3.0])
        assert np.allclose(sigma, [1.63299316])

    def test_standardized_data_has_zero_mean_and_unit_variance(self):
        # GIVEN
        X = np.array([[1.0], [3.0], [5.0]])
        # WHEN
        X_pad, _, _ = standardize_numpy(X)
        # THEN
        assert np.allclose(X_pad.mean(axis=0), [0.0])
        assert np.allclose(X_pad.std(axis=0), [1.0])


class TestKmeansNumpy:
    def test_returns_labels_and_centroids_with_correct_shapes_and_positive_inertia(
        self,
    ):
        # GIVEN
        X = np.array([[1.0, 1.0], [1.1, 1.1], [9.0, 9.0], [9.1, 9.1]])
        # WHEN
        labels, centroids, inertia = kmeans_numpy(X, k=2, n_init=1, max_iter=10)
        # THEN
        assert len(labels) == 4
        assert centroids.shape == (2, 2)
        assert inertia > 0

    def test_groups_similar_data_together(self):
        # GIVEN
        X = np.array([[1.0, 1.0], [1.1, 1.1], [9.0, 9.0], [9.1, 9.1]])
        # WHEN
        labels, _, _ = kmeans_numpy(X, k=2, n_init=1, max_iter=10)
        # THEN
        assert labels[0] == labels[1]  # Cluster das notas baixas
        assert labels[2] == labels[3]  # Cluster das notas altas
        assert labels[0] != labels[2]  # Clusters devem ser diferentes


class TestSimulateClusterImpact:
    def test_calculates_new_inde_correctly(self):
        # GIVEN
        cluster_card_falso = pd.DataFrame(
            {"inde_medio": [5.0], "ida_media": [4.0]}, index=[1]
        )
        new_values = {"Indicador de Aprendizagem": 6.0}
        weights = {"Indicador de Aprendizagem": 0.5}

        # WHEN
        inde_base, inde_new, _ = simulate_cluster_impact(
            cluster_id=1,
            new_values=new_values,
            weights=weights,
            cluster_card=cluster_card_falso,
        )

        # THEN
        assert inde_base == 5.0
        assert inde_new == 6.0

    def test_applies_zero_weight_fallback_and_ignores_ghosts(self):
        # GIVEN
        cluster_card_falso = pd.DataFrame(
            {"inde_medio": [5.0], "ieg_media": [7.0]}, index=[1]
        )
        new_values = {
            "Indicador de Engajamento": 8.0,  # Faltou o peso deste
            "Indicador Fantasma": 10.0,  # Não existe
        }
        weights = {}  # Sem pesos aqui

        # WHEN
        _, _, details = simulate_cluster_impact(
            cluster_id=1,
            new_values=new_values,
            weights=weights,
            cluster_card=cluster_card_falso,
        )

        # THEN
        assert len(details) == 1  # O indicador fantasma foi ignorado
        peso_do_engajamento = details[0][4]
        assert peso_do_engajamento == 0.0  # Fallback de peso 0.0 funcionou


class TestPredictKmeansModel:
    def test_assigns_distant_points_to_different_clusters(self):
        # GIVEN
        model_falso = {
            "risk_cols": ["colA", "colB"],
            "mu": [5.0, 5.0],
            "sigma": [1.0, 1.0],
            "centroids": [[-5.0, -5.0], [5.0, 5.0]],
        }
        df_new = pd.DataFrame({"colA": [0.1, 9.9], "colB": [0.1, 9.9]})

        # WHEN
        labels = predict_kmeans_model(df_new, model_falso)

        # THEN
        assert len(labels) == 2  # Dois alunos
        assert labels[0] != labels[1]  # Diferentes clusters

    def test_handles_missing_and_invalid_data(self):
        # GIVEN
        model_falso = {
            "risk_cols": ["colA", "colB"],
            "mu": [5.0, 5.0],
            "sigma": [1.0, 1.0],
            "centroids": [[-5.0, -5.0], [5.0, 5.0]],
        }
        df_new = pd.DataFrame(
            {
                "colA": [np.nan],  # Dado faltando
                "colB": ["texto_errado"],  # Dado corrompido
                "coluna_extra": ["X"],  # Coluna extra
            }
        )

        # WHEN
        labels = predict_kmeans_model(df_new, model_falso)

        # THEN
        assert len(labels) == 1  # Limpou a sujeira e não
        # excluiu o aluno com dados corrompidos, devolvendo 1 previsão
        assert labels[0] in [0, 1]  # Não quebrou e alocou em um cluster válido
