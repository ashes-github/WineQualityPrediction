import argparse
from collections.abc import Callable

from winequality import logger
from winequality.pipeline.data_ingestion_pipeline import (
    DataIngestionTrainingPipeline,
)
from winequality.pipeline.data_transformation_pipeline import (
    DataTransformationTrainingPipeline,
)
from winequality.pipeline.data_validation_pipeline import (
    DataValidationTrainingPipeline,
)
from winequality.pipeline.model_evaluation_pipeline import (
    ModelEvaluationTrainingPipeline,
)
from winequality.pipeline.model_trainer_pipeline import (
    ModelTrainerTrainingPipeline,
)

STAGES: dict[str, tuple[str, Callable[[], None]]] = {
    "ingestion": (
        "Data Ingestion",
        lambda: DataIngestionTrainingPipeline().initiate_data_ingestion(),
    ),
    "validation": (
        "Data Validation",
        lambda: DataValidationTrainingPipeline().initiate_data_validation(),
    ),
    "transformation": (
        "Data Transformation",
        lambda: DataTransformationTrainingPipeline().initiate_data_transformation(),
    ),
    "training": (
        "Model Training",
        lambda: ModelTrainerTrainingPipeline().initiate_model_training(),
    ),
    "evaluation": (
        "Model Evaluation",
        lambda: ModelEvaluationTrainingPipeline().initiate_model_evaluation(),
    ),
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run all or selected wine-quality training pipeline stages."
    )
    parser.add_argument(
        "--stages",
        nargs="+",
        choices=["all", *STAGES],
        default=["all"],
        help=(
            "Stages to run. Use 'all' or one or more of: "
            f"{', '.join(STAGES)}. Defaults to all."
        ),
    )
    return parser.parse_args()


def resolve_stages(requested_stages: list[str]) -> list[str]:
    if "all" in requested_stages:
        if len(requested_stages) > 1:
            raise ValueError("'all' cannot be combined with individual stages.")
        return list(STAGES)

    # Run selected stages once and in dependency order, regardless of CLI order.
    requested = set(requested_stages)
    return [stage for stage in STAGES if stage in requested]


def run_stage(stage: str) -> None:
    display_name, run = STAGES[stage]
    logger.info(f">>>>>> stage {display_name} started <<<<<<")
    try:
        run()
    except Exception:
        logger.exception(f"Stage {display_name} failed")
        raise
    logger.info(f">>>>>> stage {display_name} completed <<<<<<\n\nx==========x")


def main() -> None:
    args = parse_args()
    try:
        stages_to_run = resolve_stages(args.stages)
    except ValueError as error:
        raise SystemExit(str(error)) from error

    for stage in stages_to_run:
        run_stage(stage)


if __name__ == "__main__":
    main()
