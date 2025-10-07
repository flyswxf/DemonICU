import subprocess
import sys
from .. import constants as C

# GraphCare conda environment name
GRAPHCARE_ENV = "graphcare"
# GraphCare项目根目录
GRAPHCARE_PROJECT_ROOT = "/r/root/workspace/GraphCare"


def _run_in_conda_env(command, cwd=None, **kwargs):
    """
    在指定的conda环境中运行命令
    """
    # 构建conda激活命令列表
    if isinstance(command, list):
        conda_command = ["conda", "run", "-n", GRAPHCARE_ENV] + command
    else:
        conda_command = ["conda", "run", "-n", GRAPHCARE_ENV] + command.split()
    
    # 设置默认工作目录为GraphCare项目根目录
    if cwd is None:
        cwd = GRAPHCARE_PROJECT_ROOT
    
    return subprocess.run(
        conda_command,
        cwd=cwd,
        **kwargs
    )


def run_external_model(patient_id: str, with_feedback: bool = False) -> None:
    cmd = [
        "python",
        "-u",
        str(C.MODEL_SCRIPT),
        "--dataset",
        "mimic3",
        "--task",
        "drugrec",
        "--infer",
        "--weights_path",
        str(C.WEIGHTS_PATH),
        "--out",
        str(C.MODEL_OUT_JSON),
        "--patient_id",
        str(patient_id),
    ]
    if with_feedback:
        cmd.append("--feedback")
    _run_in_conda_env(cmd)


def run_keyword_extractor() -> None:
    cmd = ["python", str(C.KEYWORD_EXTRACTOR_SCRIPT)]
    _run_in_conda_env(cmd)


def run_cluster_mapper() -> None:
    cmd = ["python", str(C.CLUSTER_MAPPER_SCRIPT)]
    _run_in_conda_env(cmd)


def run_convert_with_fallback() -> None:
    try:
        convert_cmd = [
            "python",
            str(C.CONVERT_SCRIPT),
            "--input",
            str(C.MODEL_OUT_JSON),
            "--output",
            str(C.MODEL_OUT_WITH_NAMES_JSON),
        ]
        _run_in_conda_env(convert_cmd)
    except subprocess.CalledProcessError:
        fallback_cmd = [
            "python",
            str(C.CONVERT_SCRIPT),
        ]
        _run_in_conda_env(fallback_cmd)