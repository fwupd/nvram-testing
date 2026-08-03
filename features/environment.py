"""BehaveX/behave environment hooks."""

from pathlib import Path

from behave.model import Table

REPO_ROOT = Path(__file__).resolve().parent.parent

DYNAMIC_OUTLINE_NAME = "Build and boot NVRAM firmware for a hardware model"


def discover_models() -> list[str]:
    """Find hardware model directories, same rule as the Makefile's SUBDIRS."""
    return sorted(p.parent.name for p in REPO_ROOT.glob("*/custom_VARS.builder.xml"))


def before_feature(context, feature):
    for scenario in feature.scenarios:
        if getattr(scenario, "name", None) != DYNAMIC_OUTLINE_NAME:
            continue
        models = discover_models()
        if not models:
            print("warning: no hardware model directories discovered")
        scenario.examples[0].table = Table(["model"], rows=[[m] for m in models])
