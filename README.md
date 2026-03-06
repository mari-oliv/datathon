## Limpeza, Processamento e Modelo

- o csv fornecido está em src/data/base_dados_pede_2024.xlsx

- discovery_data.ipynb limpa e salva a base 'ajustada' fica dentro de src/base_dados_pede_2024_ajustado.csv

- processing.ipynb utiliza o csv ajustado para fazer os treinamentos

- modelo fica salvo em src/model

## Para rodar a API

- docker build -t passos-magicos-api .

- docker compose up --build

## Documentacao Swagger

- Arquivo Swagger: `docs/swagger.yaml`
- Swagger UI nativo da aplicacao FastAPI (com a API rodando): `http://localhost:8000/docs`
- Editor online para visualizar o YAML: https://editor.swagger.io/

## Testes de limpeza, processamento e modelos

### Para rodar os testes 

- pytest -v

### Para checar cobertura de testes 

- pytest --cov
