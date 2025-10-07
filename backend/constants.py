from pathlib import Path

# Project directories
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# 这个需要直接设置成服务器中的绝对路径！！！！！！！！
EHR_BASELINES_DIR = Path("/r/root/workspace/GraphCare/ehr_baselines/SparseTest")
WEIGHTS_PATH = Path("/r/root/workspace/GraphCare/data/weights/saved_weights_mimic3_drugrec_sparse.pkl")


BACKEND_DIR = PROJECT_ROOT / "backend"

# IO directories
UPLOAD_DIR = PROJECT_ROOT / "uploads"

# Model & conversion scripts
MODEL_SCRIPT = EHR_BASELINES_DIR / "runSparseModel.py"
CONVERT_SCRIPT = EHR_BASELINES_DIR / "utils" / "convert_indices_to_code.py"

# Model weights and outputs
MODEL_OUT_JSON = EHR_BASELINES_DIR / "result" / "inference_result.json"
MODEL_OUT_WITH_NAMES_JSON = EHR_BASELINES_DIR / "result" / "inference_result_with_names.json"

# Feedback pipeline paths
FEEDBACK_DIR = EHR_BASELINES_DIR / "utils" / "feedback"
FEEDBACK_RESULT_DIR = FEEDBACK_DIR / "result"
KEYWORD_EXTRACTOR_SCRIPT = FEEDBACK_DIR / "keyword_extractor.py"
CLUSTER_MAPPER_SCRIPT = FEEDBACK_DIR / "cluster_mapper.py"
FEEDBACK_RESPONSE_TXT = FEEDBACK_RESULT_DIR / "response.txt"
FEEDBACK_KEYWORD_TXT = FEEDBACK_RESULT_DIR / "keyword.txt"
FEEDBACK_CLUSTER_INDEX_TXT = FEEDBACK_RESULT_DIR / "clusterIndex.txt"