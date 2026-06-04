"""
Validates all prompt YAML files in the prompts/ directory.

Checks:
  - File is valid YAML
  - Required top-level keys: version, created, description, prompts
  - Required prompt keys: system_prompt, agent_system_prompt
  - No empty prompt strings
  - version field matches filename stem

Usage:
    python scripts/validate_prompts.py          # validates all prompts/*.yaml
    python scripts/validate_prompts.py v2       # validates prompts/v2.yaml only
"""

import sys
import yaml
from pathlib import Path


REQUIRED_TOP_LEVEL = {"version", "created", "description", "prompts"}
REQUIRED_PROMPTS = {"system_prompt", "agent_system_prompt"}
MIN_PROMPT_LENGTH = 50  # characters — guard against accidentally empty prompts


def validate_file(path: Path) -> list[str]:
    errors: list[str] = []

    # 1. Parse YAML
    try:
        with open(path, encoding="utf-8") as f:
            data = yaml.safe_load(f)
    except yaml.YAMLError as exc:
        return [f"Invalid YAML: {exc}"]

    if not isinstance(data, dict):
        return ["Top-level structure must be a YAML mapping"]

    # 2. Required top-level keys
    for key in REQUIRED_TOP_LEVEL:
        if key not in data:
            errors.append(f"Missing required top-level key: '{key}'")

    if "prompts" not in data:
        return errors  # can't check sub-keys if prompts block is missing

    prompts = data["prompts"]
    if not isinstance(prompts, dict):
        errors.append("'prompts' must be a YAML mapping")
        return errors

    # 3. Required prompt keys
    for key in REQUIRED_PROMPTS:
        if key not in prompts:
            errors.append(f"Missing required prompt: '{key}'")
        elif not prompts[key] or not isinstance(prompts[key], str):
            errors.append(f"Prompt '{key}' must be a non-empty string")
        elif len(prompts[key].strip()) < MIN_PROMPT_LENGTH:
            errors.append(
                f"Prompt '{key}' is suspiciously short "
                f"({len(prompts[key].strip())} chars, minimum {MIN_PROMPT_LENGTH})"
            )

    # 4. version field should match filename
    if "version" in data and data["version"] != path.stem:
        errors.append(
            f"version field '{data['version']}' does not match filename '{path.stem}'"
        )

    # 5. changelog should be a list if present
    if "changelog" in data and not isinstance(data["changelog"], list):
        errors.append("'changelog' must be a list")

    return errors


def main() -> None:
    prompts_dir = Path("backend/prompts") if Path("backend/prompts").exists() else Path("prompts")

    if not prompts_dir.exists():
        print("ERROR: prompts/ directory not found", file=sys.stderr)
        sys.exit(1)

    if len(sys.argv) > 1:
        target = sys.argv[1]
        files = [prompts_dir / f"{target}.yaml"]
        missing = [f for f in files if not f.exists()]
        if missing:
            print(f"ERROR: {missing[0]} not found", file=sys.stderr)
            sys.exit(1)
    else:
        files = sorted(prompts_dir.glob("*.yaml"))
        if not files:
            print("ERROR: No YAML files found in prompts/", file=sys.stderr)
            sys.exit(1)

    all_passed = True
    for path in files:
        errors = validate_file(path)
        if errors:
            all_passed = False
            print(f"\n  FAIL  {path}")
            for err in errors:
                print(f"        ✗ {err}")
        else:
            print(f"  OK    {path}")

    if all_passed:
        print(f"\n  All {len(files)} prompt file(s) are valid.\n")
        sys.exit(0)
    else:
        print(f"\n  Validation failed. Fix the errors above and re-run.\n")
        sys.exit(1)


if __name__ == "__main__":
    main()
