from pathlib import Path

# Project directories
PROJECT_ROOT = Path(__file__).resolve().parent.parent
BACKEND_DIR = PROJECT_ROOT / "backend"

# IO directories
UPLOAD_DIR = PROJECT_ROOT / "uploads"

# Model & conversion scripts
EHR_BASELINES_DIR = PROJECT_ROOT / "ehr_baselines" / "SparseTest"
MODEL_SCRIPT = EHR_BASELINES_DIR / "runSparseModel.py"
CONVERT_SCRIPT = EHR_BASELINES_DIR / "utils" / "convert_indices_to_code.py"

# Model weights and outputs
WEIGHTS_PATH = PROJECT_ROOT / "data" / "weights" / "saved_weights_mimic3_drugrec_sparse.pkl"
MODEL_OUT_JSON = EHR_BASELINES_DIR / "result" / "inference_result.json"
MODEL_OUT_WITH_NAMES_JSON = EHR_BASELINES_DIR / "result" / "inference_result_with_names.json"