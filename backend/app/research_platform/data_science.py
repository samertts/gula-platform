from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from app._compat import UTC

logger = logging.getLogger("gula.research_platform.data_science")


@dataclass
class NotebookEnvironment:
    notebook_id: str
    name: str
    kernel: str = "python3"
    dependencies: list[str] = field(default_factory=list)
    environment_vars: dict[str, str] = field(default_factory=dict)
    resource_limits: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    status: str = "stopped"


class NotebookManager:
    def __init__(self):
        self._notebooks: dict[str, NotebookEnvironment] = {}

    def create(
        self,
        name: str,
        kernel: str = "python3",
        dependencies: list[str] | None = None,
        resource_limits: dict[str, Any] | None = None,
    ) -> NotebookEnvironment:
        import uuid

        nb = NotebookEnvironment(
            notebook_id=str(uuid.uuid4()).replace("-", "").upper()[:26],
            name=name,
            kernel=kernel,
            dependencies=dependencies or [],
            resource_limits=resource_limits or {"cpu": 2, "memory_mb": 2048, "disk_mb": 10240},
        )
        self._notebooks[nb.notebook_id] = nb
        logger.info("Notebook created: %s (%s)", nb.notebook_id, name)
        return nb

    def start(self, notebook_id: str) -> NotebookEnvironment | None:
        nb = self._notebooks.get(notebook_id)
        if nb:
            nb.status = "running"
            logger.info("Notebook started: %s", notebook_id)
        return nb

    def stop(self, notebook_id: str) -> NotebookEnvironment | None:
        nb = self._notebooks.get(notebook_id)
        if nb:
            nb.status = "stopped"
            logger.info("Notebook stopped: %s", notebook_id)
        return nb

    def get(self, notebook_id: str) -> NotebookEnvironment | None:
        return self._notebooks.get(notebook_id)

    def list(self, status: str | None = None) -> list[NotebookEnvironment]:
        if status:
            return [nb for nb in self._notebooks.values() if nb.status == status]
        return list(self._notebooks.values())

    def delete(self, notebook_id: str) -> bool:
        if notebook_id in self._notebooks:
            del self._notebooks[notebook_id]
            logger.info("Notebook deleted: %s", notebook_id)
            return True
        return False


@dataclass
class MLPipelineRun:
    run_id: str
    pipeline_name: str
    status: str = "pending"
    metrics: dict[str, float] = field(default_factory=dict)
    parameters: dict[str, Any] = field(default_factory=dict)
    artifacts: list[str] = field(default_factory=list)
    started_at: datetime | None = None
    completed_at: datetime | None = None
    error: str = ""


class MLPipeline:
    def __init__(self):
        self._runs: dict[str, MLPipelineRun] = {}

    def create_run(
        self,
        pipeline_name: str,
        parameters: dict[str, Any] | None = None,
    ) -> MLPipelineRun:
        import uuid

        run = MLPipelineRun(
            run_id=str(uuid.uuid4()).replace("-", "").upper()[:26],
            pipeline_name=pipeline_name,
            parameters=parameters or {},
            started_at=datetime.now(UTC),
            status="running",
        )
        self._runs[run.run_id] = run
        logger.info("ML pipeline run created: %s (%s)", run.run_id, pipeline_name)
        return run

    def complete_run(
        self,
        run_id: str,
        metrics: dict[str, float] | None = None,
        artifacts: list[str] | None = None,
    ) -> MLPipelineRun | None:
        run = self._runs.get(run_id)
        if run:
            run.status = "completed"
            run.metrics = metrics or {}
            run.artifacts = artifacts or []
            run.completed_at = datetime.now(UTC)
        return run

    def fail_run(self, run_id: str, error: str) -> MLPipelineRun | None:
        run = self._runs.get(run_id)
        if run:
            run.status = "failed"
            run.error = error
            run.completed_at = datetime.now(UTC)
        return run

    def get_run(self, run_id: str) -> MLPipelineRun | None:
        return self._runs.get(run_id)

    def list_runs(self, pipeline_name: str | None = None) -> list[MLPipelineRun]:
        if pipeline_name:
            return [r for r in self._runs.values() if r.pipeline_name == pipeline_name]
        return list(self._runs.values())


@dataclass
class FeatureDefinition:
    name: str
    feature_type: str
    description: str = ""
    source: str = ""
    transformation: str = ""
    is_active: bool = True
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))


class FeatureStore:
    def __init__(self):
        self._features: dict[str, FeatureDefinition] = {}
        self._feature_values: dict[str, dict[str, Any]] = {}

    def register(self, feature: FeatureDefinition) -> None:
        self._features[feature.name] = feature
        logger.info("Feature registered: %s (%s)", feature.name, feature.feature_type)

    def get(self, name: str) -> FeatureDefinition | None:
        return self._features.get(name)

    def list(self, feature_type: str | None = None) -> list[FeatureDefinition]:
        if feature_type:
            return [f for f in self._features.values() if f.feature_type == feature_type]
        return list(self._features.values())

    def set_values(self, entity_id: str, values: dict[str, Any]) -> None:
        self._feature_values[entity_id] = values

    def get_values(self, entity_id: str, features: list[str] | None = None) -> dict[str, Any]:
        values = self._feature_values.get(entity_id, {})
        if features:
            return {k: v for k, v in values.items() if k in features}
        return values

    def serving_features(self, entity_ids: list[str], features: list[str]) -> list[dict[str, Any]]:
        return [self.get_values(eid, features) for eid in entity_ids]


@dataclass
class Experiment:
    experiment_id: str
    name: str
    description: str = ""
    tags: dict[str, str] = field(default_factory=dict)
    runs: list[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    artifact_location: str = ""


class ExperimentTracker:
    def __init__(self):
        self._experiments: dict[str, Experiment] = {}
        self._runs: dict[str, dict] = {}

    def create_experiment(
        self,
        name: str,
        description: str = "",
        tags: dict[str, str] | None = None,
    ) -> Experiment:
        import uuid

        exp = Experiment(
            experiment_id=str(uuid.uuid4()).replace("-", "").upper()[:26],
            name=name,
            description=description,
            tags=tags or {},
        )
        self._experiments[exp.experiment_id] = exp
        logger.info("Experiment created: %s (%s)", exp.experiment_id, name)
        return exp

    def get_experiment(self, experiment_id: str) -> Experiment | None:
        return self._experiments.get(experiment_id)

    def list_experiments(self) -> list[Experiment]:
        return list(self._experiments.values())

    def log_run(
        self,
        experiment_id: str,
        run_name: str,
        params: dict[str, Any] | None = None,
        metrics: dict[str, float] | None = None,
        tags: dict[str, str] | None = None,
    ) -> str:
        import uuid

        run_id = str(uuid.uuid4()).replace("-", "").upper()[:26]
        run = {
            "run_id": run_id,
            "experiment_id": experiment_id,
            "run_name": run_name,
            "params": params or {},
            "metrics": metrics or {},
            "tags": tags or {},
            "started_at": datetime.now(UTC).isoformat(),
            "status": "completed",
        }
        self._runs[run_id] = run
        exp = self._experiments.get(experiment_id)
        if exp:
            exp.runs.append(run_id)
        return run_id

    def get_run(self, run_id: str) -> dict | None:
        return self._runs.get(run_id)

    def search_runs(
        self,
        experiment_id: str | None = None,
        metric_filter: dict[str, float] | None = None,
    ) -> list[dict]:
        results = list(self._runs.values())
        if experiment_id:
            results = [r for r in results if r.get("experiment_id") == experiment_id]
        if metric_filter:
            results = [
                r for r in results
                if all(r.get("metrics", {}).get(k) == v for k, v in metric_filter.items())
            ]
        return results


@dataclass
class ModelVersion:
    version_id: str
    model_name: str
    version: str
    stage: str = "none"
    run_id: str = ""
    metrics: dict[str, float] = field(default_factory=dict)
    artifacts: list[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))


class ModelRegistry:
    def __init__(self):
        self._models: dict[str, list[ModelVersion]] = {}

    def register(
        self,
        model_name: str,
        run_id: str = "",
        metrics: dict[str, float] | None = None,
        artifacts: list[str] | None = None,
    ) -> ModelVersion:
        versions = self._models.get(model_name, [])
        version_num = len(versions) + 1
        mv = ModelVersion(
            version_id=f"{model_name}_v{version_num}",
            model_name=model_name,
            version=f"v{version_num}",
            run_id=run_id,
            metrics=metrics or {},
            artifacts=artifacts or [],
        )
        self._models.setdefault(model_name, []).append(mv)
        logger.info("Model registered: %s@%s", model_name, mv.version)
        return mv

    def get(self, model_name: str, version: str | None = None) -> ModelVersion | None:
        versions = self._models.get(model_name, [])
        if version:
            return next((v for v in versions if v.version == version), None)
        return versions[-1] if versions else None

    def promote(self, model_name: str, version: str, stage: str) -> ModelVersion | None:
        mv = self.get(model_name, version)
        if mv:
            mv.stage = stage
            logger.info("Model %s@%s promoted to %s", model_name, version, stage)
        return mv

    def list_models(self) -> list[dict]:
        return [{"name": k, "versions": len(v)} for k, v in self._models.items()]


@dataclass
class EvaluationResult:
    model_name: str
    version: str
    metrics: dict[str, float] = field(default_factory=dict)
    confusion_matrix: dict[str, int] | None = None
    feature_importance: dict[str, float] | None = None
    roc_auc: float | None = None
    precision_recall: dict[str, float] | None = None


class EvaluationFramework:
    def __init__(self, registry: ModelRegistry | None = None):
        self._registry = registry or ModelRegistry()
        self._results: dict[str, EvaluationResult] = {}

    def evaluate(
        self,
        model_name: str,
        version: str,
        y_true: list[float],
        y_pred: list[float],
    ) -> EvaluationResult:
        from math import sqrt

        n = len(y_true)
        mse = sum((a - b) ** 2 for a, b in zip(y_true, y_pred, strict=False)) / max(n, 1)
        rmse = sqrt(mse)
        mae = sum(abs(a - b) for a, b in zip(y_true, y_pred, strict=False)) / max(n, 1)
        result = EvaluationResult(
            model_name=model_name,
            version=version,
            metrics={"mse": round(mse, 4), "rmse": round(rmse, 4), "mae": round(mae, 4), "r2": 0.0},
        )
        self._results[f"{model_name}@{version}"] = result
        logger.info("Model evaluated: %s@%s (RMSE=%.4f)", model_name, version, rmse)
        return result

    def get_result(self, model_name: str, version: str) -> EvaluationResult | None:
        return self._results.get(f"{model_name}@{version}")

    def compare_models(self, model_names: list[str]) -> list[dict]:
        comparisons = []
        for name in model_names:
            mv = self._registry.get(name)
            if mv:
                result = self.get_result(name, mv.version)
                if result:
                    comparisons.append({
                        "model": name,
                        "version": mv.version,
                        "metrics": result.metrics,
                    })
        return comparisons
