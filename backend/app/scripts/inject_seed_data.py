"""
Script to inject/update/delete Users, Clients, Products, Mentors, Pillars, Metrics, and Students from JSON files.
Each JSON file should be an array of objects with a 'crud_action' field: 'C' (create), 'U' (update), 'D' (delete).
Run: python backend/app/scripts/inject_seed_data.py
"""
import json
import os
import inspect
from app.storage.user_repository import UserRepository, default_user_store_path
from app.storage.client_repository import ClientRepository, default_client_store_path
from app.storage.organization_repository import OrganizationRepository, default_organization_store_path
from app.storage.mentor_repository import MentorRepository, default_mentor_store_path
from app.storage.pillar_repository import PillarRepository, default_pillar_store_path
from app.storage.metric_repository import MetricRepository, default_metric_store_path
from app.storage.student_repository import StudentRepository, default_student_store_path

ENTITY_CONFIG = [
    ("users", UserRepository, default_user_store_path),
    ("clients", ClientRepository, default_client_store_path),
    ("mentors", MentorRepository, default_mentor_store_path),
    ("pillars", PillarRepository, default_pillar_store_path),
    ("metrics", MetricRepository, default_metric_store_path),
    ("students", StudentRepository, default_student_store_path),
    ("organizations", OrganizationRepository, default_organization_store_path),
]

def process_entity(entity_name, repo_cls, path_func, base_dir=None):
    if base_dir is None:
        # Always resolve backend/data_ops relative to this script's directory
        script_dir = os.path.dirname(os.path.abspath(__file__))
        base_dir = os.path.abspath(os.path.join(script_dir, "..", "..", "data_ops"))
    json_path = os.path.join(base_dir, f"{entity_name}.json")
    if not os.path.exists(json_path):
        print(f"No ops file found for {entity_name}, skipping.")
        return
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)
        # Support both {"items": [...]} and direct array
        if isinstance(data, dict) and "items" in data:
            items = data["items"]
        else:
            items = data
    repo = repo_cls(path_func())
    # Get accepted argument names for create()
    create_args = set()
    if hasattr(repo, "create"):
        sig = inspect.signature(repo.create)
        create_args = set(
            p.name for p in sig.parameters.values()
            if p.kind in (p.KEYWORD_ONLY, p.POSITIONAL_OR_KEYWORD) and p.name != "self"
        )
    for item in items:
        action = item.get("crud_action")
        item_id = item.get("id")
        if not action:
            print(f"[{entity_name}] Skipping item with no 'crud_action': {item_id}")
            continue
        action = action.upper()
        if action == "C":
            if hasattr(repo, "create"):
                filtered = {k: v for k, v in item.items() if k != "crud_action" and k in create_args}
                repo.create(**filtered)
                print(f"[{entity_name}] Created: {item_id}")
            else:
                print(f"[{entity_name}] Create not supported, skipping: {item_id}")
        elif action == "U":
            if hasattr(repo, "update"):
                repo.update(**{k: v for k, v in item.items() if k != "crud_action"})
                print(f"[{entity_name}] Updated: {item_id}")
            else:
                print(f"[{entity_name}] Update not supported, skipping: {item_id}")
        elif action == "D":
            if hasattr(repo, "delete"):
                repo.delete(item_id)
                print(f"[{entity_name}] Deleted: {item_id}")
            else:
                print(f"[{entity_name}] Delete not supported, skipping: {item_id}")
        else:
            print(f"[{entity_name}] Unknown action '{action}' for {item_id}")

def main():
    for entity_name, repo_cls, path_func in ENTITY_CONFIG:
        process_entity(entity_name, repo_cls, path_func)
    # Products (optional)
    try:
        from app.storage.product_repository import ProductRepository, default_product_store_path
        process_entity("products", ProductRepository, default_product_store_path)
    except ImportError:
        print("ProductRepository not found, skipping products.")
    print("All entity operations processed.")

if __name__ == "__main__":
    main()
