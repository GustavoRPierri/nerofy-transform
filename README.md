# nerofy-transform

Lambda de transformação JSON → Parquet para o data lake da Nerofy.

## Função

Escuta eventos S3 no bucket **bronze** e:
1. Lê o JSON recém-criado
2. Converte para Parquet (PyArrow)
3. Salva no bucket **silver** com mesma partição `year/month/day`
4. Registra/atualiza a tabela no **Glue Catalog**

## Estrutura

```
├── config/              # Configurações (pydantic-settings)
├── src/
│   ├── application/     # TransformService (lógica principal)
│   ├── domain/
│   │   ├── entities/    # Modelos de dados
│   │   └── interfaces/  # Contratos (IStorageReader, IStorageWriter, IGlueCatalog)
│   ├── infrastructure/  # Adaptadores S3 e Glue
│   └── tests/           # Testes
├── scripts/             # Execução local com mocks
├── infra/               # Terraform
├── template.yaml        # SAM
└── lambda_handler.py    # Entry point
```

## Fluxo

```
S3 bronze/ (JSON) → S3 Event Notification → Lambda → silver/ (Parquet) → Glue Catalog
```

## Desenvolvimento local

```bash
python scripts/invoke_local.py
```

## Deploy

```bash
sam build && sam deploy
```
