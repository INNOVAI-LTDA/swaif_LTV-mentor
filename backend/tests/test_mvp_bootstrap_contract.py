from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path


def _load_bootstrap_module():
    script_path = Path(__file__).resolve().parents[2] / "scripts" / "mvp_bootstrap.py"
    spec = spec_from_file_location("mvp_bootstrap", script_path)
    if spec is None or spec.loader is None:
        raise AssertionError("Unable to load scripts/mvp_bootstrap.py for contract test.")
    module = module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_client_code_contract_sets_backend_and_frontend_pair() -> None:
    module = _load_bootstrap_module()
    backend_env_overrides: dict[str, str] = {}
    frontend_env_overrides: dict[str, str] = {}

    module.apply_client_code_contract(backend_env_overrides, frontend_env_overrides, "accmed")

    assert backend_env_overrides["CLIENT_CODE"] == "accmed"
    assert frontend_env_overrides["CLIENT_CODE"] == "accmed"
    assert frontend_env_overrides["VITE_CLIENT_CODE"] == "accmed"
