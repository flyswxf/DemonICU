import subprocess
import sys
from .. import constants as C


def run_external_model(patient_id: str, with_feedback: bool = False) -> None:
    cmd = [
        sys.executable,
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
    subprocess.run(cmd, cwd=str(C.PROJECT_ROOT), check=True)


def run_keyword_extractor() -> None:
    subprocess.run([sys.executable, str(C.KEYWORD_EXTRACTOR_SCRIPT)], cwd=str(C.PROJECT_ROOT), check=True)


def run_cluster_mapper() -> None:
    subprocess.run([sys.executable, str(C.CLUSTER_MAPPER_SCRIPT)], cwd=str(C.PROJECT_ROOT), check=True)


def run_convert_with_fallback() -> None:
    try:
        convert_cmd = [
            sys.executable,
            str(C.CONVERT_SCRIPT),
            "--input",
            str(C.MODEL_OUT_JSON),
            "--output",
            str(C.MODEL_OUT_WITH_NAMES_JSON),
        ]
        subprocess.run(convert_cmd, cwd=str(C.PROJECT_ROOT), check=True)
    except subprocess.CalledProcessError:
        fallback_cmd = [
            sys.executable,
            str(C.CONVERT_SCRIPT),
        ]
        subprocess.run(fallback_cmd, cwd=str(C.PROJECT_ROOT), check=True)