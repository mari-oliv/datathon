import sys
import os
import traceback
import argparse
import pickle
from pathlib import Path

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


def main(save_model: bool = False, out_path: str | None = None):
    try:
        import numpy as np
        import pandas as pd
        from src.processing_and_models import (
            parse_fase_ideal,
            normalize_bool_sim_nao,
            standardize_numpy,
            kmeans_numpy,
            simulate_cluster_impact,
        )

        os.environ["OPENBLAS_NUM_THREADS"] = "1"
        os.environ["OMP_NUM_THREADS"] = "1"

        csv_path = os.path.join(os.path.dirname(__file__), '..', 'src', 'base_dados_pede_2024_ajustado.csv')
        csv_path = os.path.abspath(csv_path)
        print('Lendo:', csv_path)
        df = pd.read_csv(csv_path)


        df['Fase_ideal_num'] = df['Fase ideal'].apply(parse_fase_ideal)
        df['gap_fase'] = df['Fase_ideal_num'] - df['Fase']
        df['pv_bool'] = normalize_bool_sim_nao(df['Atingiu Ponto de Virada'])

        risk_cols = [
            'Nível de Defasagem',
            'Fase',
            'Fase_ideal_num',
            'gap_fase',
            'Indicador de Aprendizagem',
            'Indicador de Engajamento',
            'Indicador Psicossocial',
            'Indicador de Adequação ao Nível',
            'Indicador de Ponto de Virada',
            'Índice de Desenvolvimento Educacional (INDE)'
        ]

        missing = [c for c in risk_cols if c not in df.columns]
        if missing:
            raise RuntimeError(f"Faltam colunas no df: {missing}")

        X_df = df[risk_cols].copy()
        X_df = X_df.apply(pd.to_numeric, errors='coerce')
        X_df = X_df.fillna(X_df.mean(numeric_only=True))
        X = X_df.to_numpy(dtype=float)

        X_scaled, mu, sigma = standardize_numpy(X)

        k = 5
        labels, centroids, inertia = kmeans_numpy(X_scaled, k=k, n_init=40, max_iter=700, seed=42)
        df['cluster5'] = labels

        print(f"k={k} | inertia={inertia:.4f}")
        print('\nTamanhos dos clusters:')
        print(df['cluster5'].value_counts().sort_index())

        cluster_card5 = (
            df.groupby('cluster5')
              .agg(
                  n=('RA', 'count'),
                  pv_rate=('pv_bool', 'mean'),
                  defasagem_media=('Nível de Defasagem', 'mean'),
                  gap_fase_medio=('gap_fase', 'mean'),
                  inde_medio=('Índice de Desenvolvimento Educacional (INDE)', 'mean'),
                  ida_media=('Indicador de Aprendizagem', 'mean'),
                  ieg_media=('Indicador de Engajamento', 'mean'),
                  ips_media=('Indicador Psicossocial', 'mean'),
                  ian_media=('Indicador de Adequação ao Nível', 'mean'),
                  ipv_medio=('Indicador de Ponto de Virada', 'mean'),
              )
              .sort_values(['defasagem_media', 'pv_rate'], ascending=[True, True])
        )

        print('\n=== Cartão do Cluster (k=5) ===')
        print(cluster_card5)

        # simulação similar ao notebook: escolher cluster crítico = 1 e pesos
        cluster_critico = 1
        weights = {
            'Indicador de Aprendizagem': 0.20,
            'Indicador de Engajamento': 0.15,
            'Indicador Psicossocial': 0.10,
            'Indicador de Adequação ao Nível': 0.15,
            'Indicador de Ponto de Virada': 0.15,
        }
        scenario = {
            'Indicador de Aprendizagem': 6.0,
            'Indicador de Engajamento': 7.0,
        }

        inde_base, inde_new, details = simulate_cluster_impact(cluster_critico, scenario, weights, cluster_card5)

        print(f"\n=== Simulação (Cluster {cluster_critico}) ===")
        print(f"INDE base: {inde_base:.3f} -> INDE estimado: {inde_new:.3f}")
        print('Detalhes:')
        for feat, cur, tgt, delta, w, contrib in details:
            print(f"- {feat}: {cur:.2f} -> {tgt:.2f} | Δ={delta:.2f} | peso={w:.2f} | contrib={contrib:.3f}")

        # --- salvar modelo (se solicitado) ------------------------------------------------
        if save_model:
            model_obj = {
                "k": int(k),
                "risk_cols": risk_cols,
                "mu": mu.tolist(),
                "sigma": sigma.tolist(),
                "centroids": centroids.tolist(),
            }

            if out_path is None:
                out_dir = Path(__file__).parent / ".." / "src" / "model"
                out_dir = out_dir.resolve()
                out_dir.mkdir(parents=True, exist_ok=True)
                out_path = str(out_dir / "model.pkl")

            with open(out_path, "wb") as f:
                pickle.dump(model_obj, f)

            print(f"Modelo salvo em: {out_path}")

    except Exception as e:
        print('Erro durante execução:')
        traceback.print_exc()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Run simulation / train clusters and optionally save model")
    parser.add_argument("--save-model", "-s", action="store_true", help="Salvar o modelo treinado em src/model/model.pkl")
    parser.add_argument("--out", "-o", default=None, help="Caminho do arquivo de saída para o modelo (opcional)")
    args = parser.parse_args()
    main(save_model=args.save_model, out_path=args.out)
