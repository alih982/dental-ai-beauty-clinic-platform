import mlflow
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

def setup_mlflow():
    """
    Configures MLflow tracking URI and experiment name.
    Should be called on app startup.
    """
    try:
        tracking_uri = getattr(settings, 'MLFLOW_TRACKING_URI', 'http://mlflow:5000')
        mlflow.set_tracking_uri(tracking_uri)
        
        experiment_name = "AntiGravity_AI_Orchestrator"
        existing_exp = mlflow.get_experiment_by_name(experiment_name)
        
        if not existing_exp:
            mlflow.create_experiment(experiment_name)
        
        mlflow.set_experiment(experiment_name)
        logger.info(f"MLflow initialized. Tracking URI: {tracking_uri}")
    except Exception as e:
        logger.warning(f"Failed to initialize MLflow: {e}")

class MLflowTracer:
    """
    Context manager for tracing AI operations.
    """
    def __init__(self, run_name: str, parameters: dict = None):
        self.run_name = run_name
        self.parameters = parameters or {}
        self.active_run = None

    def __enter__(self):
        try:
            self.active_run = mlflow.start_run(run_name=self.run_name, nested=True)
            if self.parameters:
                mlflow.log_params(self.parameters)
            return self.active_run
        except Exception:
            return None

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.active_run:
            if exc_type:
                mlflow.log_param("status", "FAILED")
                mlflow.log_param("error", str(exc_val))
            else:
                mlflow.log_param("status", "SUCCESS")
            mlflow.end_run()
