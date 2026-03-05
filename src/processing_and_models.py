import numpy as np
import pandas as pd
import re


def parse_fase_ideal(x):
    """
    (Aluno) Tento extrair um número da string 'Fase ideal'.
    - Se a célula estiver vazia retorna np.nan.
    - Uso regex para pegar o primeiro número encontrado.
    Exemplo: '6ª série' -> 6.0
    """
    if pd.isna(x):
        return np.nan
    s = str(x).strip()
    m = re.search(r"\d+", s)
    return float(m.group()) if m else np.nan


def normalize_bool_sim_nao(series):
    """
    (Aluno) Normaliza respostas tipo 'sim'/'não' para booleanos.
    - Converte tudo para string, tira espaços e deixa em minúsculas.
    - Considera várias formas de 'sim' como verdadeiras.
    Retorna uma Series booleana.
    """
    s = series.astype(str).str.strip().str.lower()
    return s.isin(["sim", "s", "true", "1", "yes", "y"])


def standardize_numpy(X):
    """
    (Aluno) Padroniza um array numpy por coluna.
    - Calcula média (mu) e desvio padrão (sigma) por coluna.
    - Se sigma == 0 substitui por 1.0 para evitar divisão por zero.
    Retorna: (X_padronizado, mu, sigma)
    """
    mu = X.mean(axis=0)
    sigma = X.std(axis=0)
    sigma[sigma == 0] = 1.0
    return (X - mu) / sigma, mu, sigma


def kmeans_numpy(X, k, n_init=30, max_iter=600, seed=42):
    """
    (Aluno) Implementação simplificada do KMeans usando apenas numpy.

    Parâmetros:
    - X: array shape (n_samples, n_features)
    - k: número de clusters
    - n_init: quantas inicializações aleatórias tentar
    - max_iter: iterações por inicialização
    - seed: semente para reprodutibilidade

    Retorna: (labels, centroids, inertia)
    - labels: array com rótulo de cluster por amostra
    - centroids: array (k, n_features) com centroides finais
    - inertia: soma dos quadrados dentro dos clusters (menor = melhor)
    """
    rng = np.random.default_rng(seed)
    best_inertia = np.inf
    best_labels = None
    best_centroids = None
    n = X.shape[0]

    for _ in range(n_init):
        idx = rng.choice(n, size=k, replace=False)
        centroids = X[idx].copy()

        for _ in range(max_iter):
            d2 = ((X[:, None, :] - centroids[None, :, :]) ** 2).sum(axis=2)
            labels = d2.argmin(axis=1)

            new_centroids = centroids.copy()
            for j in range(k):
                pts = X[labels == j]
                if len(pts) == 0:
                    new_centroids[j] = X[rng.integers(0, n)]
                else:
                    new_centroids[j] = pts.mean(axis=0)

            if np.allclose(new_centroids, centroids, atol=1e-6):
                centroids = new_centroids
                break
            centroids = new_centroids

        inertia = ((X - centroids[labels]) ** 2).sum()
        if inertia < best_inertia:
            best_inertia = inertia
            best_labels = labels.copy()
            best_centroids = centroids.copy()

    return best_labels, best_centroids, best_inertia


def simulate_cluster_impact(cluster_id, new_values, weights, cluster_card):
    """
    (Aluno) Simula impacto aproximado no INDE médio de um cluster se alterarmos indicadores.

    Parâmetros:
    - cluster_id: id do cluster no `cluster_card5`
    - new_values: dict com valores alvo por indicador, ex: {"Indicador de Aprendizagem": 6.0}
    - weights: pesos que traduzem mudança no indicador para mudança no INDE (aproximação)

    Retorna: (inde_base, inde_new, details)
    - inde_base: valor médio atual do INDE no cluster
    - inde_new: INDE estimado após aplicar mudanças ponderadas
    - details: lista de tuplas (feat, current, target, delta, w, contrib) com contribuições
    """
    base = cluster_card.loc[cluster_id].copy()
    inde_base = base["inde_medio"]

    delta_inde = 0.0
    details = []

    for feat, target in new_values.items():
        current = base.get(
            {
                "Indicador de Aprendizagem": "ida_media",
                "Indicador de Engajamento": "ieg_media",
                "Indicador Psicossocial": "ips_media",
                "Indicador de Adequação ao Nível": "ian_media",
                "Indicador de Ponto de Virada": "ipv_medio",
            }.get(feat, feat),
            None,
        )

        if current is None:
            continue

        delta = target - current
        w = weights.get(feat, 0.0)
        delta_inde += delta * w
        details.append((feat, current, target, delta, w, delta * w))

    inde_new = inde_base + delta_inde
    return inde_base, inde_new, details


def predict_kmeans_model(df_new, model):
    X_df_new = df_new[model["risk_cols"]].copy()
    X_df_new = X_df_new.apply(pd.to_numeric, errors="coerce")
    mu_arr = np.array(model["mu"])
    sigma_arr = np.array(model["sigma"])
    X_df_new = X_df_new.fillna(pd.Series(mu_arr, index=model["risk_cols"]))
    X = X_df_new.to_numpy(dtype=float)
    X_scaled_new = (X - mu_arr) / sigma_arr
    centroids_arr = np.array(model["centroids"])
    d2 = ((X_scaled_new[:, None, :] - centroids_arr[None, :, :]) ** 2).sum(axis=2)
    labels_new = d2.argmin(axis=1)
    return labels_new
