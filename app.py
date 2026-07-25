from flask import Flask, jsonify, render_template, request
import numpy as np

from main import STAGES, resolve_stages, run_stage
from winequality.pipeline.prediction_pipeline import PredictionPipeline

app = Flask(__name__)  # initializing a flask app


@app.route("/", methods=["GET"])  # route to display the home page
def homePage():
    return render_template("index.html")


def _requested_stages():
    """Read a stage list from JSON, query parameters, or default to all."""
    payload = request.get_json(silent=True) or {}
    requested = payload.get("stages")

    if requested is None:
        requested = request.args.getlist("stages")

    if not requested:
        return ["all"]

    if isinstance(requested, str):
        requested = requested.split(",")

    if not isinstance(requested, list):
        raise ValueError("'stages' must be a list or comma-separated string.")

    cleaned = [str(stage).strip().lower() for stage in requested if str(stage).strip()]
    if not cleaned:
        raise ValueError("At least one stage must be provided.")

    invalid = [stage for stage in cleaned if stage != "all" and stage not in STAGES]
    if invalid:
        valid = ", ".join(["all", *STAGES])
        raise ValueError(
            f"Unknown stage(s): {', '.join(invalid)}. Valid stages: {valid}."
        )

    return cleaned


def _execute_training(requested):
    """Execute pipeline stages and return a consistent API response."""
    completed = []
    try:
        invalid = [
            stage for stage in requested if stage != "all" and stage not in STAGES
        ]
        if invalid:
            valid = ", ".join(["all", *STAGES])
            raise ValueError(
                f"Unknown stage(s): {', '.join(invalid)}. Valid stages: {valid}."
            )

        stages_to_run = resolve_stages(requested)
        for stage in stages_to_run:
            run_stage(stage)
            completed.append(stage)
    except ValueError as error:
        return jsonify({"status": "error", "message": str(error)}), 400
    except Exception as error:
        app.logger.exception("Training pipeline failed")
        return (
            jsonify(
                {
                    "status": "error",
                    "message": str(error),
                    "completed_stages": completed,
                }
            ),
            500,
        )

    return (
        jsonify(
            {
                "status": "success",
                "message": "Training pipeline completed successfully.",
                "completed_stages": stages_to_run,
            }
        ),
        200,
    )


@app.route("/train", methods=["GET", "POST"])
def training():
    """
    Run all stages by default or a selected stage list.

    Examples:
      POST /train                    -> all stages
      POST /train {"stages": [...]}  -> selected stages
      GET  /train?stages=ingestion&stages=validation
    """
    try:
        requested = _requested_stages()
    except ValueError as error:
        return jsonify({"status": "error", "message": str(error)}), 400

    return _execute_training(requested)


@app.route("/train/<stage>", methods=["GET", "POST"])
def training_stage(stage):
    """Run one named stage, or use /train/all for the complete pipeline."""
    return _execute_training([stage.strip().lower()])


@app.route(
    "/predict", methods=["POST", "GET"]
)  # route to show the predictions in a web UI
def index():
    if request.method == "POST":
        try:
            #  reading the inputs given by the user
            fixed_acidity = float(request.form["fixed_acidity"])
            volatile_acidity = float(request.form["volatile_acidity"])
            citric_acid = float(request.form["citric_acid"])
            residual_sugar = float(request.form["residual_sugar"])
            chlorides = float(request.form["chlorides"])
            free_sulfur_dioxide = float(request.form["free_sulfur_dioxide"])
            total_sulfur_dioxide = float(request.form["total_sulfur_dioxide"])
            density = float(request.form["density"])
            pH = float(request.form["pH"])
            sulphates = float(request.form["sulphates"])
            alcohol = float(request.form["alcohol"])

            data = [
                fixed_acidity,
                volatile_acidity,
                citric_acid,
                residual_sugar,
                chlorides,
                free_sulfur_dioxide,
                total_sulfur_dioxide,
                density,
                pH,
                sulphates,
                alcohol,
            ]
            data = np.array(data).reshape(1, 11)

            obj = PredictionPipeline()
            predict = obj.predict(data)

            return render_template("results.html", prediction=str(predict))

        except Exception as e:
            print("The Exception message is: ", e)
            return "something is wrong"

    else:
        return render_template("index.html")


if __name__ == "__main__":

    app.run(host="0.0.0.0", port=8080)
