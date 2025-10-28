from pathlib import Path
import os



# Project directories
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# 这个需要直接设置成服务器中的绝对路径！！！！！！！！
EHR_BASELINES_DIR = Path("/r/root/workspace/GraphCare/ehr_baselines/SparseTest")
# Windows 路径（测试/本地环境使用）
# EHR_BASELINES_DIR = Path(r"D:\HuaweiMoveData\Users\fengl\Desktop\code\ICU\GraphCare\ehr_baselines\SparseTest")
WEIGHTS_PATH = Path("/r/root/workspace/GraphCare/data/weights/saved_weights_mimic3_drugrec_sparse.pkl")


BACKEND_DIR = PROJECT_ROOT / "backend"

# 资源目录（用于测试模式直接读取示例结果）
RESOURCES_DIR = PROJECT_ROOT / "resources"

# 测试模式：启用后不运行模型，直接使用现有输出文件
# export DEMO_TEST_MODE=1
TEST_MODE = os.getenv("DEMO_TEST_MODE", "0") == "1"

# IO directories
UPLOAD_DIR = PROJECT_ROOT / "uploads"

# Model & conversion scripts
MODEL_SCRIPT = EHR_BASELINES_DIR / "runSparseModel.py"
CONVERT_SCRIPT = EHR_BASELINES_DIR / "utils" / "convert_indices_to_code.py"

# GraphCare conda environment name
GRAPHCARE_ENV = "graphcare"
# GraphCare项目根目录
GRAPHCARE_PROJECT_ROOT = "/r/root/workspace/GraphCare"

# Model weights and outputs
if TEST_MODE:
    # 测试模式下，直接使用项目resources中的示例结果
    # 通过在graphcare项目中运行处理脚本来获得result文件
    MODEL_OUT_JSON = RESOURCES_DIR / "inference_result.json"
    MODEL_OUT_WITH_NAMES_JSON = RESOURCES_DIR / "inference_result_with_names.json"
else:
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

# Graph image generation resources
GRAPH_JSON_PATH = RESOURCES_DIR / "graph.json"