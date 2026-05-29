from __future__ import annotations

import os
from datetime import datetime, timezone
from pathlib import Path
from threading import RLock
from typing import Any

default_product_store_path = lambda: Path(__file__).resolve().parents[2] / "data" / "products.json"

def _slugify(value: str) -> str:
	return "-".join(value.strip().lower().split())

def _now_iso() -> str:
	return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

class ProductRepository:
	_memory_stores: dict[str, list[dict[str, Any]]] = {}
	_memory_lock = RLock()

	def __init__(self, file_path: str | Path | None = None) -> None:
		self._namespace = str((Path(file_path) if file_path is not None else default_product_store_path()).resolve())
		if not os.path.exists(self._namespace):
			self._memory_items()

	def _memory_items(self) -> list[dict[str, Any]]:
		with self._memory_lock:
			items = self._memory_stores.get(self._namespace)
			if items is None:
				items = []
				self._memory_stores[self._namespace] = items
			return items

	def _read_items(self) -> list[dict[str, Any]]:
		return [dict(item) for item in self._memory_items() if isinstance(item, dict) and item.get("deleted_at") is None]

	def _write_items(self, items: list[dict[str, Any]]) -> None:
		with self._memory_lock:
			self._memory_stores[self._namespace] = [dict(item) for item in items]

	def create(
		self,
		*,
		organization_id: int,
		name: str,
		slug: str | None = None,
		category: str,
		status: str = "active",
		description: str | None = None,
	) -> dict[str, Any]:
		items = self._read_items()
		candidate_slug = _slugify(slug or name)
		now = _now_iso()
		prod_id = max([p["id"] for p in items if "id" in p and isinstance(p["id"], int)] + [0]) + 1
		product = {
			"id": prod_id,
			"organization_id": organization_id,
			"name": name,
			"slug": candidate_slug,
			"category": category,
			"status": status,
			"description": description,
			"created_at": now,
			"updated_at": now,
			"deleted_at": None,
		}
		items.append(product)
		ProductRepository._memory_stores[str(default_product_store_path())] = items
		return product

	def soft_delete(self, product_id: int) -> bool:
		items = self._read_items()
		for prod in items:
			if int(prod.get("id")) == int(product_id):
				prod["deleted_at"] = _now_iso()
				self._write_items(items)
				return True
		return False

	def get_by_id(self, product_id: int) -> dict[str, Any] | None:
		for product in self._read_items():
			if int(product.get("id")) == int(product_id):
				return product
		return None

	def list_products(self) -> list[dict[str, Any]]:
		return self._read_items()

	def list_by_organization(self, organization_id: int) -> list[dict[str, Any]]:
		return [item for item in self._read_items() if int(item.get("organization_id") or 0) == int(organization_id)]
