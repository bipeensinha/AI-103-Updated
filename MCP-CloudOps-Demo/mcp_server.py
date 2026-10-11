
import json
from pathlib import Path

from mcp.server.fastmcp import FastMCP

# Create the MCP server.
mcp = FastMCP("Cloud Operations Demo")

# Find the inventory file relative to this Python file.
INVENTORY_FILE = (
    Path(__file__).parent / "data" / "vm_inventory.json"
)


def load_inventory():
    """Load the fictional VM inventory from JSON."""
    if not INVENTORY_FILE.exists():
        raise FileNotFoundError(
            f"Inventory file not found: {INVENTORY_FILE}"
        )

    with INVENTORY_FILE.open("r", encoding="utf-8") as file:
        return json.load(file)


@mcp.tool()
def list_virtual_machines() -> dict:
    """List all virtual machines in the demo inventory.

    Returns VM names, statuses, regions, environments,
    and sample CPU utilization.
    """
    vms = load_inventory()

    return {
        "count": len(vms),
        "virtual_machines": vms
    }


@mcp.tool()
def get_vm_status(vm_name: str) -> dict:
    """Get status and details for one VM by its exact name.

    Args:
        vm_name: The name of the VM to look up.
    """
    vms = load_inventory()

    for vm in vms:
        if vm["name"].lower() == vm_name.strip().lower():
            return {
                "found": True,
                "virtual_machine": vm
            }

    return {
        "found": False,
        "message": f"No VM named '{vm_name}' was found."
    }


if __name__ == "__main__":
    # Use standard input/output for MCP communication.
    mcp.run(transport="stdio")
