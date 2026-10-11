import json
from pathlib import Path
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("CloudOps Resource Tools")
INVENTORY_FILE = Path(__file__).parent / "data" / "cloud_inventory.json"

def load_inventory():
    with INVENTORY_FILE.open("r", encoding="utf-8") as f:
        return json.load(f)

@mcp.tool()
def list_cloud_resources(resource_type: str = "all", status: str = "all") -> dict:
    """List simulated resources. resource_type: all, AKS Cluster, Azure SQL Database, App Service, Virtual Machine, Storage Account. status: all, Healthy, Warning, Critical, Running, Stopped."""
    resources = load_inventory()["resources"]
    if resource_type.lower() != "all":
        resources = [r for r in resources if r["type"].lower() == resource_type.lower()]
    if status.lower() != "all":
        resources = [r for r in resources if r["status"].lower() == status.lower()]
    return {"simulated": True, "count": len(resources), "resources": resources}

@mcp.tool()
def get_resource_status(resource_name: str) -> dict:
    """Get status, region, environment and operational details for a resource by its name."""
    for r in load_inventory()["resources"]:
        if r["name"].lower() == resource_name.strip().lower():
            return {"simulated": True, "found": True, "resource": r}
    return {"simulated": True, "found": False, "message": f"No demo resource named '{resource_name}' was found."}

@mcp.tool()
def get_resource_health_summary() -> dict:
    """Summarize counts of simulated cloud resources by status and type."""
    resources = load_inventory()["resources"]
    statuses, types = {}, {}
    for r in resources:
        statuses[r["status"]] = statuses.get(r["status"], 0) + 1
        types[r["type"]] = types.get(r["type"], 0) + 1
    return {"simulated": True, "total_resources": len(resources), "by_status": statuses, "by_type": types}

if __name__ == "__main__":
    mcp.run(transport="stdio")
