def create_client(idx):
    cnpj_num = f"{idx:014d}"
    payload = {
        "name": f"Cliente {idx}",
        "cnpj": cnpj_num,
        "slug": f"cliente-{idx}-{randstr(4)}",
        "brand_name": f"Brand {idx}",
        "timezone": "America/Sao_Paulo",
        "currency": "BRL",
        "notes": None
    }
    resp = requests.post(f"{API_URL}/clientes", json=payload, headers=HEADERS)
    resp.raise_for_status()
    return resp.json()
"""
Script de integração para montar e validar a estrutura organizacional via API.
- Cria até 15 registros por entidade (Organization, User, Product, Enrollment, Metric)
- Consulta os endpoints de listagem
- Monta um JSON com a estrutura completa
- Salva em resultado_organizacional.json
"""

import requests
import random
import string
import json

API_URL = "http://localhost:8040/admin"

def get_admin_token():
    login_url = "http://localhost:8040/auth/login"
    payload = {"email": "admin@swaif.local", "password": "admin123"}
    resp = requests.post(login_url, json=payload)
    resp.raise_for_status()
    return resp.json()["access_token"]

ADMIN_TOKEN = get_admin_token()
HEADERS = {
    "accept": "application/json",
    "Content-Type": "application/json",
    "Authorization": f"Bearer {ADMIN_TOKEN}"
}

# Helpers
def randstr(n=8):
    return ''.join(random.choices(string.ascii_lowercase, k=n))

def create_organization(idx):
    payload = {
        "name": f"Org {idx}",
        "brand_name": f"Brand {idx}",
        "slug": f"org-{idx}-{randstr(4)}",
        "cnpj": f"00.000.000/000{idx}-00",
        "timezone": "America/Sao_Paulo",
        "currency": "BRL",
        "status": "active"
    }
    # Garantir todos os campos obrigatórios
    for field in ["name", "brand_name", "slug", "timezone", "currency", "status"]:
        if not payload.get(field):
            raise Exception(f"Payload missing required field: {field}")
    resp = requests.post(f"{API_URL}/organizations", json=payload, headers=HEADERS)
    resp.raise_for_status()
    return resp.json()

def create_user(idx, org_id):
    payload = {
        "full_name": f"User {idx}",
        "email": f"user{idx}@example.com",
        "organization_id": org_id
    }
    resp = requests.post(f"{API_URL}/users", json=payload, headers=HEADERS)
    resp.raise_for_status()
    return resp.json()

def create_product(idx, org_id):
    payload = {
        "name": f"Product {idx}",
        "code": f"PROD-{idx}-{randstr(3)}",
        "slug": f"prod-{idx}-{randstr(4)}",
        "description": f"Produto {idx}",
        "delivery_model": "live"
    }
    resp = requests.post(f"{API_URL}/clientes/{org_id}/produtos", json=payload, headers=HEADERS)
    resp.raise_for_status()
    return resp.json()

def create_metric(idx, product_id, pillar_id=1):
    payload = {
        "pillar_id": pillar_id,  # Ajuste conforme necessário
        "protocol_id": 1,
        "name": f"Metric {idx}",
        "code": f"metric-{idx}-{randstr(3)}",
        "direction": "higher_better",
        "unit": "pt",
        "score_type": "static",
        "min_score": 0,
        "max_score": 100,
        "mcv_score": 50,
        "max_basis_score": "MAX_VALUE"
    }
    # O endpoint correto para criar métrica é por pilar
    resp = requests.post(f"{API_URL}/pilares/{pillar_id}/metricas", json=payload, headers=HEADERS)
    resp.raise_for_status()
    return resp.json()

def create_enrollment(idx, org_id, user_id, product_id):
    payload = {
        "student_id": user_id,
        "organization_id": org_id,
        "mentor_id": user_id,
        "progress_score": random.uniform(0, 1),
        "engagement_score": random.uniform(0, 1),
        "urgency_status": "normal",
        "day": idx,
        "total_days": 90,
        "days_left": 90 - idx,
        "ltv_cents": 10000 + idx * 1000
    }
    resp = requests.post(f"{API_URL}/enrollments", json=payload, headers=HEADERS)
    resp.raise_for_status()
    return resp.json()

def main():
    clients = [create_client(i) for i in range(1, 6)]
    orgs = [create_organization(i) for i in range(1, 6)]
    users = []
    products = []
    metrics = []
    enrollments = []
    for idx, (client, org) in enumerate(zip(clients, orgs), 1):
        client_id = client["id"]
        org_id = org["id"]
        org_users = [create_user(i, org_id) for i in range(1, 4)]
        users.extend(org_users)
        org_products = [create_product(i, client_id) for i in range(1, 4)]
        products.extend(org_products)
        for prod in org_products:
            prod_id = prod["id"]
            prod_metrics = [create_metric(i, prod_id) for i in range(1, 4)]
            metrics.extend(prod_metrics)
        for user in org_users:
            user_id = user["id"]
            for prod in org_products:
                prod_id = prod["id"]
                enrollments.append(create_enrollment(random.randint(1, 15), org_id, user_id, prod_id))
    # Consultar endpoints de listagem
    all_orgs = requests.get(f"{API_URL}/organizations", headers=HEADERS).json()
    all_users = requests.get(f"{API_URL}/users", headers=HEADERS).json()
    # Listar produtos por organização
    all_products = []
    for org in orgs:
        org_id = org["id"]
        org_products = requests.get(f"{API_URL}/clientes/{org_id}/produtos", headers=HEADERS).json()
        all_products.extend(org_products)
    # Listar métricas por produto
    all_metrics = []
    for prod in all_products:
        prod_id = prod["id"]
        prod_metrics = requests.get(f"{API_URL}/produtos/{prod_id}/metricas", headers=HEADERS).json()
        all_metrics.extend(prod_metrics)
    # Listar matrículas
    all_enrollments = requests.get(f"{API_URL}/enrollments", headers=HEADERS).json()
    estrutura = {
        "organizations": all_orgs,
        "users": all_users,
        "products": all_products,
        "metrics": all_metrics,
        "enrollments": all_enrollments
    }
    with open("resultado_organizacional.json", "w", encoding="utf-8") as f:
        json.dump(estrutura, f, ensure_ascii=False, indent=2)
    print("Estrutura organizacional salva em resultado_organizacional.json")

if __name__ == "__main__":
    main()
