"""Operaciones de CI/CD implementadas en Python, sin scripts de shell."""

from __future__ import annotations

import argparse
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path


def write_metadata() -> int:
    repository = os.environ["GITHUB_REPOSITORY"].lower()
    source_sha = os.environ["GITHUB_SHA"]
    output_path = Path(os.environ["GITHUB_OUTPUT"])
    with output_path.open("a", encoding="utf-8") as output:
        output.write(f"image_name=ghcr.io/{repository}\n")
        output.write(f"image_tag=sha-{source_sha}\n")
    return 0


def write_summary() -> int:
    quality = os.environ["QUALITY_RESULT"]
    regression = os.environ["REGRESSION_RESULT"]
    manifests = os.environ["MANIFESTS_RESULT"]
    summary_path = Path(os.environ["GITHUB_STEP_SUMMARY"])
    summary = (
        "## Resultado del candidato\n\n"
        "| Control | Resultado |\n"
        "| --- | --- |\n"
        f"| Análisis y unit tests | {quality} |\n"
        f"| Docker Compose y regresión | {regression} |\n"
        f"| Manifiestos de Kubernetes | {manifests} |\n"
    )
    with summary_path.open("a", encoding="utf-8") as output:
        output.write(summary)
    results = (quality, regression, manifests)
    return 0 if all(result == "success" for result in results) else 1


def git(repository: Path, *arguments: str, check: bool = True) -> int:
    result = subprocess.run(
        ["git", *arguments],
        cwd=repository,
        check=check,
    )
    return result.returncode


def replace_line(content: str, key: str, value: str) -> str:
    updated, count = re.subn(
        rf"^(\s*{re.escape(key)}:\s*).*$",
        rf"\g<1>{value}",
        content,
        count=1,
        flags=re.MULTILINE,
    )
    if count != 1:
        raise RuntimeError(f"No se encontró una única clave {key}.")
    return updated


def promote(
    source: Path,
    desired: Path,
    image_name: str,
    image_tag: str,
    source_sha: str,
) -> int:
    source = source.resolve()
    desired = desired.resolve()

    for relative_path in (Path("k8s"), Path("gitops/production")):
        destination = desired / relative_path
        if destination.exists():
            shutil.rmtree(destination)
        shutil.copytree(source / relative_path, destination)

    kustomization = desired / "gitops/production/kustomization.yaml"
    content = kustomization.read_text(encoding="utf-8")
    content = replace_line(content, "newName", image_name)
    content = replace_line(content, "newTag", image_tag)
    content = replace_line(content, "app.kubernetes.io/version", image_tag)
    kustomization.write_text(content, encoding="utf-8")

    git(desired, "config", "user.name", "github-actions[bot]")
    git(
        desired,
        "config",
        "user.email",
        "41898282+github-actions[bot]@users.noreply.github.com",
    )
    git(desired, "add", "k8s", "gitops/production")

    diff_result = git(desired, "diff", "--cached", "--quiet", check=False)
    if diff_result == 0:
        print("La imagen ya estaba promovida.")
        return 0
    if diff_result != 1:
        raise RuntimeError("No se pudo comprobar el estado de la promoción.")

    git(desired, "commit", "-m", f"deploy: promover {source_sha}")
    git(desired, "push", "origin", "HEAD:gitops")
    return 0


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("metadata")
    subparsers.add_parser("summary")

    promote_parser = subparsers.add_parser("promote")
    promote_parser.add_argument("--source", type=Path, required=True)
    promote_parser.add_argument("--desired", type=Path, required=True)
    promote_parser.add_argument("--image-name", required=True)
    promote_parser.add_argument("--image-tag", required=True)
    promote_parser.add_argument("--source-sha", required=True)
    return parser.parse_args()


def main() -> int:
    arguments = parse_arguments()
    try:
        if arguments.command == "metadata":
            return write_metadata()
        if arguments.command == "summary":
            return write_summary()
        return promote(
            source=arguments.source,
            desired=arguments.desired,
            image_name=arguments.image_name,
            image_tag=arguments.image_tag,
            source_sha=arguments.source_sha,
        )
    except (KeyError, OSError, RuntimeError, subprocess.CalledProcessError) as error:
        print(f"Error: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
