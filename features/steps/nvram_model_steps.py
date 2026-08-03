import os
import subprocess
from pathlib import Path

from behave import given, when, then

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
DEFAULT_IMAGE = REPO_ROOT / "Fedora-Server-Guest-Generic-44-1.7.x86_64.qcow2"


def run_nvram(context, *args) -> subprocess.CompletedProcess:
    return subprocess.run(
        [str(REPO_ROOT / "nvram.py"), *args],
        cwd=context.model_dir,
        capture_output=True,
        text=True,
    )


@given('the hardware model directory "{model}"')
def step_impl(context, model):
    context.model_dir = REPO_ROOT / model
    assert context.model_dir.is_dir(), f"{context.model_dir} does not exist"


@when("I extract firmware signatures for the model")
def step_impl(context):
    result = run_nvram(context, "extract")
    assert result.returncode == 0, result.stderr


@when("I build custom_VARS.fd for the model")
def step_impl(context):
    result = run_nvram(context, "build")
    assert result.returncode == 0, result.stderr


@when("I boot the guest image with the model's firmware")
def step_impl(context):
    image = context.config.userdata.get("image") or os.environ.get("IMAGE")
    image_path = Path(image).resolve() if image else DEFAULT_IMAGE
    assert image_path.exists(), f"guest image not found: {image_path}"
    context.run_result = run_nvram(context, "run", "--image", str(image_path))


@then("the VM should exit successfully")
def step_impl(context):
    assert context.run_result.returncode == 0, context.run_result.stderr
