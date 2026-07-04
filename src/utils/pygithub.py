from __future__ import annotations

import importlib.util
import site
import sys
from pathlib import Path


def _load_pygithub_package():
    current_module = sys.modules.get("github")
    if current_module is not None and getattr(current_module, "__file__", None):
        return current_module

    search_paths: list[str] = []
    if hasattr(site, "getsitepackages"):
        search_paths.extend(site.getsitepackages())

    user_site = site.getusersitepackages()
    if isinstance(user_site, str):
        search_paths.append(user_site)
    else:
        search_paths.extend(user_site)

    for base_path in search_paths:
        package_init = Path(base_path) / "github" / "__init__.py"
        if not package_init.exists():
            continue

        spec = importlib.util.spec_from_file_location(
            "github",
            package_init,
            submodule_search_locations=[str(package_init.parent)],
        )
        if spec is None or spec.loader is None:
            continue

        module = importlib.util.module_from_spec(spec)
        sys.modules["github"] = module
        spec.loader.exec_module(module)
        return module

    raise ImportError("PyGithub package not found")


_github = _load_pygithub_package()

Github = _github.Github
Auth = _github.Auth
GithubException = _github.GithubException

from github.Repository import Repository  