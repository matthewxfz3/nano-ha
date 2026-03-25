"""NanoHA Tenant Manager — multi-tenant isolation and provisioning."""

import logging
import os
import shutil
import subprocess

log = logging.getLogger(__name__)

TENANTS_DIR = os.environ.get(
    "NANOHA_TENANTS_DIR",
    os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "tenants"),
)


def _tenant_dir(tenant_id: str) -> str:
    safe_id = tenant_id.replace("/", "_").replace("..", "_")
    return os.path.join(TENANTS_DIR, safe_id)


def create_tenant(tenant_id: str, llm_provider: str = "anthropic", llm_api_key: str = "") -> dict:
    """Provision a new tenant with isolated config and data directories."""
    tenant_path = _tenant_dir(tenant_id)
    if os.path.exists(tenant_path):
        return {"success": False, "error": f"Tenant '{tenant_id}' already exists."}

    try:
        os.makedirs(tenant_path, exist_ok=True)
        os.makedirs(os.path.join(tenant_path, "ha_config"), exist_ok=True)
        os.makedirs(os.path.join(tenant_path, "memory"), exist_ok=True)

        # Generate tenant .env
        env_path = os.path.join(tenant_path, ".env")
        with open(env_path, "w") as f:
            f.write(f"TENANT_ID={tenant_id}\n")
            f.write(f"LLM_PROVIDER={llm_provider}\n")
            f.write(f"LLM_API_KEY={llm_api_key}\n")
            f.write(f"HA_URL=http://nanoha-ha-{tenant_id}:8123\n")
            f.write("HA_TOKEN=\n")

        # Generate tenant compose override
        override_path = os.path.join(tenant_path, "docker-compose.override.yml")
        with open(override_path, "w") as f:
            f.write(f"services:\n")
            f.write(f"  homeassistant:\n")
            f.write(f"    container_name: nanoha-ha-{tenant_id}\n")
            f.write(f"    volumes:\n")
            f.write(f"      - ./{tenant_id}/ha_config:/config\n")

        return {
            "success": True,
            "tenant_id": tenant_id,
            "path": tenant_path,
            "message": f"Tenant '{tenant_id}' created. Run with: docker compose --env-file tenants/{tenant_id}/.env up",
        }
    except OSError as e:
        log.error("Cannot create tenant '%s': %s", tenant_id, e)
        return {"success": False, "error": str(e)}


def list_tenants() -> dict:
    """List all provisioned tenants."""
    if not os.path.isdir(TENANTS_DIR):
        return {"success": True, "count": 0, "tenants": []}

    tenants = []
    for entry in sorted(os.listdir(TENANTS_DIR)):
        tenant_path = os.path.join(TENANTS_DIR, entry)
        if os.path.isdir(tenant_path) and os.path.exists(os.path.join(tenant_path, ".env")):
            tenants.append({
                "tenant_id": entry,
                "path": tenant_path,
                "has_env": True,
            })

    return {"success": True, "count": len(tenants), "tenants": tenants}


def get_tenant(tenant_id: str) -> dict:
    """Get tenant details."""
    tenant_path = _tenant_dir(tenant_id)
    if not os.path.exists(tenant_path):
        return {"success": False, "error": f"Tenant '{tenant_id}' not found."}

    env_path = os.path.join(tenant_path, ".env")
    config = {}
    if os.path.exists(env_path):
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if "=" in line and not line.startswith("#"):
                    key, _, val = line.partition("=")
                    # Redact sensitive values
                    if "KEY" in key or "TOKEN" in key:
                        val = val[:4] + "..." if len(val) > 4 else "***"
                    config[key] = val

    return {"success": True, "tenant_id": tenant_id, "path": tenant_path, "config": config}


def delete_tenant(tenant_id: str) -> dict:
    """Delete a tenant and all its data."""
    tenant_path = _tenant_dir(tenant_id)
    if not os.path.exists(tenant_path):
        return {"success": False, "error": f"Tenant '{tenant_id}' not found."}

    try:
        shutil.rmtree(tenant_path)
        return {"success": True, "tenant_id": tenant_id, "deleted": True}
    except OSError as e:
        return {"success": False, "error": str(e)}
