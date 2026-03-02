#!/usr/bin/env python3
"""
Script de teste da API — Passos Mágicos
Executa: python test_api.py [BASE_URL]
Padrão: http://localhost:8000
"""

import json
import sys
import urllib.request
import urllib.error

BASE_URL = sys.argv[1].rstrip("/") if len(sys.argv) > 1 else "http://localhost:8000"


def req(method: str, path: str, body: dict | None = None) -> dict:
    url = BASE_URL + path
    data = json.dumps(body).encode() if body else None
    headers = {"Content-Type": "application/json"}
    request = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(request) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as e:
        return {"error": e.code, "detail": e.read().decode()}


def print_result(title: str, result: dict):
    print(f"\n{'─'*60}")
    print(f"  {title}")
    print(f"{'─'*60}")
    print(json.dumps(result, indent=2, ensure_ascii=False))


#1. Health check
result = req("GET", "/health")
print_result("GET /health", result)

#2. Predict — aluno de alto risco
aluno_risco = {
    "Nível de Defasagem": -2,
    "Fase": 5,
    "Fase ideal": "Fase 7 (2º EM)",
    "Atingiu Ponto de Virada": "Não",
    "Indicador de Aprendizagem": 3.0,
    "Indicador de Engajamento": 2.5,
    "Indicador Psicossocial": 4.0,
    "Indicador de Adequação ao Nível": 3.0,
    "Indicador de Ponto de Virada": 4.0,
    "Índice de Desenvolvimento Educacional (INDE)": 4.2,
}
result = req("POST", "/predict", aluno_risco)
print_result("POST /predict — Aluno de alto risco", result)

#3. Predict — aluno de baixo risco
aluno_ok = {
    "Nível de Defasagem": 0,
    "Fase": 7,
    "Fase ideal": "Fase 7 (3º EM)",
    "Atingiu Ponto de Virada": "Sim",
    "Indicador de Aprendizagem": 8.5,
    "Indicador de Engajamento": 9.0,
    "Indicador Psicossocial": 8.0,
    "Indicador de Adequação ao Nível": 10.0,
    "Indicador de Ponto de Virada": 8.5,
    "Índice de Desenvolvimento Educacional (INDE)": 8.8,
}
result = req("POST", "/predict", aluno_ok)
print_result("POST /predict — Aluno de baixo risco", result)

#4. Predict — campos ausentes (imputa com média)
aluno_parcial = {
    "Fase": 4,
    "Indicador de Aprendizagem": 5.0,
}
result = req("POST", "/predict", aluno_parcial)
print_result("POST /predict — Dados parciais (imputa missing)", result)

#5. Batch predict
batch = {"students": [aluno_risco, aluno_ok, aluno_parcial]}
result = req("POST", "/predict/batch", batch)
print_result("POST /predict/batch — 3 alunos", result)

print(f"\n{'═'*60}")
print("  Testes concluídos!")
print(f"  Docs interativos: {BASE_URL}/docs")
print(f"{'═'*60}\n")
