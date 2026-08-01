# Wine Quality Prediction

An end-to-end red-wine quality prediction project built with ElasticNet,
DVC, DagsHub, MLflow, and Flask.

## Pipeline

```text
Ingestion → Validation → Transformation → Training → Evaluation
```

DVC versions the generated datasets, model, and metrics. DagsHub provides the
DVC remote and MLflow experiment tracking.

## Setup

```powershell
conda create --prefix ./venv python=3.11 -y
conda activate ./venv
python -m pip install -r requirements.txt
python -m pip install -e .
```

For an existing clone, restore the DVC-managed artifacts:

```powershell
dvc pull
```

### Package setup

`setup.py` defines the installable `winequality` package and its dependencies.
Because the source code uses a `src/` layout, install the project in editable
mode during development:

```powershell
python -m pip install -e .
```

This makes `winequality` imports available while keeping code changes
immediately visible without reinstalling the package. The command may create a
local `*.egg-info/` metadata directory; this is expected and should remain
excluded from Git.

## DVC pipeline

The repository already contains `dvc.yaml`; it normally does not need to be
generated again. To recreate it from scratch, remove the existing stages and
run the following commands from the project root.

### Ingestion

```powershell
dvc stage add -n ingestion `
  -d main.py -d config/config.yaml `
  -d src/winequality/components/data_ingestion.py `
  -d src/winequality/pipeline/data_ingestion_pipeline.py `
  -o artifacts/data_ingestion/data.zip `
  -o artifacts/data_ingestion/winequality-red.csv `
  "python main.py --stages ingestion"
```

### Validation

```powershell
dvc stage add -n validation `
  -d main.py -d config/config.yaml -d schema.yaml `
  -d artifacts/data_ingestion/winequality-red.csv `
  -d src/winequality/components/data_validation.py `
  -d src/winequality/pipeline/data_validation_pipeline.py `
  -o artifacts/data_validation/status.txt `
  "python main.py --stages validation"
```

### Transformation

```powershell
dvc stage add -n transformation `
  -d main.py -d config/config.yaml `
  -d artifacts/data_ingestion/winequality-red.csv `
  -d artifacts/data_validation/status.txt `
  -d src/winequality/components/data_transformation.py `
  -d src/winequality/pipeline/data_transformation_pipeline.py `
  -o artifacts/data_transformation/train.csv `
  -o artifacts/data_transformation/test.csv `
  "python main.py --stages transformation"
```

### Training

```powershell
dvc stage add -n training `
  -d main.py -d config/config.yaml -d schema.yaml `
  -d artifacts/data_transformation/train.csv `
  -d artifacts/data_transformation/test.csv `
  -d src/winequality/components/model_trainer.py `
  -d src/winequality/pipeline/model_trainer_pipeline.py `
  -p ElasticNet.alpha -p ElasticNet.l1_ratio `
  -o artifacts/model_trainer/model.joblib `
  "python main.py --stages training"
```

### Evaluation

```powershell
dvc stage add -n evaluation `
  -d main.py -d config/config.yaml -d schema.yaml `
  -d artifacts/data_transformation/test.csv `
  -d artifacts/model_trainer/model.joblib `
  -d src/winequality/components/model_evaluation.py `
  -d src/winequality/pipeline/model_evaluation_pipeline.py `
  -p ElasticNet.alpha -p ElasticNet.l1_ratio `
  -M artifacts/model_evaluation/metrics.json `
  "python main.py --stages evaluation"
```

Run and inspect the pipeline:

```powershell
dvc repro
dvc dag
dvc metrics show
```

Push the generated artifacts to the configured DagsHub remote:

```powershell
dvc push
git add dvc.yaml dvc.lock params.yaml
git commit -m "Update DVC pipeline"
git push
```

The `artifacts/` directory is excluded from Git. DagsHub may still display its
files because DagsHub combines the Git repository with DVC-managed storage.

## Direct pipeline execution

Run every stage:

```powershell
python main.py --stages all
```

Run one or more selected stages:

```powershell
python main.py --stages ingestion
python main.py --stages ingestion validation transformation
```

Supported stages are `ingestion`, `validation`, `transformation`, `training`,
and `evaluation`.

Use `dvc repro` when DVC caching and artifact versioning are required.

## Flask application

Start the application:

```powershell
python app.py
```

Open the prediction UI at `http://127.0.0.1:8080`.

## Docker

The image includes the trained model at
`artifacts/model_trainer/model.joblib`, so it can serve predictions immediately.
The local `.env` file is never copied into the image; it is supplied only at
container runtime for DagsHub/MLflow access during training.

Build and run with Docker Compose:

```powershell
docker compose up --build
```

Open the prediction UI at `http://127.0.0.1:8080`. The Compose configuration
mounts `artifacts/` and `logs/` so models produced by `/train` and application
logs persist on the host. Stop the application with `Ctrl+C` and remove its
container with:

```powershell
docker compose down
```

To run the image without Compose (for prediction-only use), pass MLflow
credentials only if you intend to call a training endpoint:

```powershell
docker build -t winequalityprediction .
docker run --rm -p 8080:8080 winequalityprediction
```

Run the complete training pipeline:

```powershell
Invoke-RestMethod -Method Post -Uri "http://127.0.0.1:8080/train"
```

Run one stage:

```powershell
Invoke-RestMethod -Method Post -Uri "http://127.0.0.1:8080/train/training"
```

Run selected stages:

```powershell
$body = @{ stages = @("ingestion", "validation") } | ConvertTo-Json

Invoke-RestMethod `
  -Method Post `
  -Uri "http://127.0.0.1:8080/train" `
  -ContentType "application/json" `
  -Body $body
```

The Flask training endpoints call the Python pipeline directly; they do not run
`dvc repro`.

## DagsHub MLflow configuration

Set these values locally or through CI secrets:

```text
MLFLOW_TRACKING_URI=https://dagshub.com/<owner>/<repository>.mlflow
MLFLOW_TRACKING_USERNAME=<owner>
MLFLOW_TRACKING_PASSWORD=<DagsHub access token>
```

Never commit credentials or the local `.env` file.

## Development workflow

When adding or modifying a pipeline stage, follow this order:

1. Update `config/config.yaml`.
2. Update `schema.yaml`, if the data schema changes.
3. Update `params.yaml`, if model parameters change.
4. Update the entity in `src/winequality/entity`.
5. Update the configuration manager in `src/winequality/config`.
6. Update the component in `src/winequality/components`.
7. Update the pipeline wrapper in `src/winequality/pipeline`.
8. Update the stage registration in `main.py`.
9. Update the corresponding dependencies, parameters, and outputs in `dvc.yaml`.
10. Run `dvc repro` and commit the updated `dvc.lock`.
