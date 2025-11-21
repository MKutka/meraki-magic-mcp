import os
import json
import meraki
import asyncio
import functools
import inspect
import hashlib
from typing import Any, Dict, Optional
from datetime import datetime, timedelta
from mcp.server.fastmcp import FastMCP
from pydantic import Field
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Create an MCP server
mcp = FastMCP("Meraki Magic MCP - Full API")

# Configuration
MERAKI_API_KEY = os.getenv("MERAKI_API_KEY")
MERAKI_ORG_ID = os.getenv("MERAKI_ORG_ID")
ENABLE_CACHING = os.getenv("ENABLE_CACHING", "true").lower() == "true"
CACHE_TTL_SECONDS = int(os.getenv("CACHE_TTL_SECONDS", "300"))  # 5 minutes default
READ_ONLY_MODE = os.getenv("READ_ONLY_MODE", "false").lower() == "true"

# Initialize Meraki API client with optimizations
dashboard = meraki.DashboardAPI(
    api_key=MERAKI_API_KEY,
    suppress_logging=True,
    maximum_retries=3,  # Auto-retry on failures
    wait_on_rate_limit=True  # Auto-wait on rate limits instead of failing
)

###################
# CACHING SYSTEM
###################

class SimpleCache:
    """Simple in-memory cache with TTL"""
    def __init__(self):
        self.cache = {}
        self.timestamps = {}

    def get(self, key: str) -> Optional[Any]:
        """Get cached value if not expired"""
        if key in self.cache:
            if datetime.now() - self.timestamps[key] < timedelta(seconds=CACHE_TTL_SECONDS):
                return self.cache[key]
            else:
                # Expired, remove
                del self.cache[key]
                del self.timestamps[key]
        return None

    def set(self, key: str, value: Any):
        """Set cached value"""
        self.cache[key] = value
        self.timestamps[key] = datetime.now()

    def clear(self):
        """Clear all cache"""
        self.cache.clear()
        self.timestamps.clear()

    def stats(self) -> Dict:
        """Get cache statistics"""
        return {
            "total_items": len(self.cache),
            "cache_enabled": ENABLE_CACHING,
            "ttl_seconds": CACHE_TTL_SECONDS
        }

cache = SimpleCache()

###################
# ASYNC UTILITIES
###################

def to_async(func):
    """Convert a synchronous function to an asynchronous function"""
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            lambda: func(*args, **kwargs)
        )
    return wrapper

###################
# DYNAMIC TOOL GENERATION
###################

# SDK sections to expose
SDK_SECTIONS = [
    'organizations',
    'networks',
    'devices',
    'wireless',
    'switch',
    'appliance',
    'camera',
    'cellularGateway',
    'sensor',
    'sm',
    'insight',
    'licensing',
    'administered'
]

# Read-only operations (GET methods) - safe to cache
READ_ONLY_PREFIXES = ['get', 'list']
# Write operations - check read-only mode
WRITE_PREFIXES = ['create', 'update', 'delete', 'remove', 'claim', 'reboot', 'assign', 'move', 'renew', 'clone', 'combine', 'split', 'bind', 'unbind']

def is_read_only_operation(method_name: str) -> bool:
    """Check if operation is read-only"""
    return any(method_name.startswith(prefix) for prefix in READ_ONLY_PREFIXES)

def is_write_operation(method_name: str) -> bool:
    """Check if operation is a write/destructive operation"""
    return any(method_name.startswith(prefix) for prefix in WRITE_PREFIXES)

def create_cache_key(section: str, method: str, kwargs: Dict) -> str:
    """Create a cache key from method call"""
    # Sort kwargs for consistent keys
    sorted_kwargs = json.dumps(kwargs, sort_keys=True)
    key_string = f"{section}_{method}_{sorted_kwargs}"
    return hashlib.md5(key_string.encode()).hexdigest()

###################
# GENERIC API CALLER - Provides access to ALL 804+ endpoints
###################

def _call_meraki_method_internal(section: str, method: str, params: dict) -> str:
    """Internal helper to call Meraki API methods"""
    try:
        # Validate section
        if not hasattr(dashboard, section):
            return json.dumps({
                "error": f"Invalid section '{section}'",
                "available_sections": SDK_SECTIONS
            }, indent=2)

        section_obj = getattr(dashboard, section)

        # Validate method
        if not hasattr(section_obj, method):
            return json.dumps({
                "error": f"Method '{method}' not found in section '{section}'"
            }, indent=2)

        method_func = getattr(section_obj, method)

        if not callable(method_func):
            return json.dumps({"error": f"'{method}' is not callable"}, indent=2)

        # Determine operation type
        is_read = is_read_only_operation(method)
        is_write = is_write_operation(method)

        # Read-only mode check
        if READ_ONLY_MODE and is_write:
            return json.dumps({
                "error": "Write operation blocked - READ_ONLY_MODE is enabled",
                "method": method,
                "hint": "Set READ_ONLY_MODE=false in .env to enable"
            }, indent=2)

        # Auto-fill org ID if needed
        sig = inspect.signature(method_func)
        method_params = [p for p in sig.parameters.keys() if p != 'self']

        if 'organizationId' in method_params and 'organizationId' not in params and MERAKI_ORG_ID:
            params['organizationId'] = MERAKI_ORG_ID

        # Check cache for read operations
        if ENABLE_CACHING and is_read:
            cache_key = create_cache_key(section, method, params)
            cached = cache.get(cache_key)
            if cached is not None:
                if isinstance(cached, dict):
                    cached['_from_cache'] = True
                return json.dumps(cached, indent=2)

        # Call the method
        result = method_func(**params)

        # Cache read results
        if ENABLE_CACHING and is_read:
            cache_key = create_cache_key(section, method, params)
            cache.set(cache_key, result)

        return json.dumps(result, indent=2)

    except meraki.exceptions.APIError as e:
        return json.dumps({
            "error": "Meraki API Error",
            "message": str(e),
            "status": getattr(e, 'status', 'unknown')
        }, indent=2)
    except TypeError as e:
        return json.dumps({
            "error": "Invalid parameters",
            "message": str(e),
            "hint": f"Use get_method_info(section='{section}', method='{method}') for parameter details"
        }, indent=2)
    except Exception as e:
        return json.dumps({
            "error": str(e),
            "type": type(e).__name__
        }, indent=2)

async def call_meraki_method(section: str, method: str, **params) -> str:
    """Internal async wrapper for pre-registered tools"""
    return await to_async(_call_meraki_method_internal)(section, method, params)

@mcp.tool()
async def call_meraki_api(
    section: str,
    method: str,
    parameters: Dict[str, Any] = Field(
        default_factory=dict,
        json_schema_extra={
            'type': 'object',
            'properties': {},
            'additionalProperties': True
        }
    )
) -> str:
    """
    Call any Meraki API method - provides access to all 804+ endpoints

    Args:
        section: SDK section (organizations, networks, wireless, switch, appliance, camera, devices, sensor, sm, etc.)
        method: Method name (e.g., getOrganizationAdmins, updateNetworkWirelessSsid, getNetworkApplianceFirewallL3FirewallRules)
        parameters: Dict of parameters (e.g., {"networkId": "L_123", "name": "MySSID"})

    Examples:
        call_meraki_api(section="organizations", method="getOrganizationAdmins", parameters={"organizationId": "123456"})
        call_meraki_api(section="wireless", method="updateNetworkWirelessSsid", parameters={"networkId": "L_123", "number": "0", "name": "NewSSID", "enabled": True})
        call_meraki_api(section="appliance", method="getNetworkApplianceFirewallL3FirewallRules", parameters={"networkId": "L_123"})
    """
    # Call internal method (parameters is always a dict due to default_factory)
    return await to_async(_call_meraki_method_internal)(section, method, parameters)

###################
# MOST COMMON TOOLS (Pre-registered for convenience)
###################

@mcp.tool()
async def getOrganizations() -> str:
    """Get all organizations"""
    return await call_meraki_method("organizations", "getOrganizations")

@mcp.tool()
async def getOrganizationAdmins(organizationId: str = None) -> str:
    """Get organization administrators"""
    params = {}
    if organizationId:
        params['organizationId'] = organizationId
    return await call_meraki_method("organizations", "getOrganizationAdmins", **params)

@mcp.tool()
async def getOrganizationNetworks(organizationId: str = None) -> str:
    """Get organization networks"""
    params = {}
    if organizationId:
        params['organizationId'] = organizationId
    return await call_meraki_method("organizations", "getOrganizationNetworks", **params)

@mcp.tool()
async def getOrganizationDevices(organizationId: str = None) -> str:
    """Get organization devices"""
    params = {}
    if organizationId:
        params['organizationId'] = organizationId
    return await call_meraki_method("organizations", "getOrganizationDevices", **params)

@mcp.tool()
async def getNetwork(networkId: str) -> str:
    """Get network details"""
    return await call_meraki_method("networks", "getNetwork", networkId=networkId)

@mcp.tool()
async def getNetworkClients(networkId: str, timespan: int = 86400) -> str:
    """Get network clients"""
    return await call_meraki_method("networks", "getNetworkClients", networkId=networkId, timespan=timespan)

@mcp.tool()
async def getNetworkEvents(networkId: str, productType: str = None, perPage: int = 100) -> str:
    """Get network events"""
    params = {"networkId": networkId, "perPage": perPage}
    if productType:
        params['productType'] = productType
    return await call_meraki_method("networks", "getNetworkEvents", **params)

@mcp.tool()
async def getNetworkDevices(networkId: str) -> str:
    """Get network devices"""
    return await call_meraki_method("networks", "getNetworkDevices", networkId=networkId)

@mcp.tool()
async def getDevice(serial: str) -> str:
    """Get device by serial"""
    return await call_meraki_method("devices", "getDevice", serial=serial)

@mcp.tool()
async def getNetworkWirelessSsids(networkId: str) -> str:
    """Get wireless SSIDs"""
    return await call_meraki_method("wireless", "getNetworkWirelessSsids", networkId=networkId)

# Switch Tools
@mcp.tool()
async def getDeviceSwitchPorts(serial: str) -> str:
    """Get switch ports for a device"""
    return await call_meraki_method("switch", "getDeviceSwitchPorts", serial=serial)

@mcp.tool()
async def updateDeviceSwitchPort(serial: str, portId: str, name: str = None, tags: str = None, enabled: bool = None,
                                  poeEnabled: bool = None, type: str = None, vlan: int = None, voiceVlan: int = None,
                                  allowedVlans: str = None, isolationEnabled: bool = None, rstpEnabled: bool = None,
                                  stpGuard: str = None, linkNegotiation: str = None, portScheduleId: str = None,
                                  udld: str = None, accessPolicyType: str = None, accessPolicyNumber: int = None,
                                  macAllowList: str = None, stickyMacAllowList: str = None,
                                  stickyMacAllowListLimit: int = None, stormControlEnabled: bool = None) -> str:
    """Update switch port configuration"""
    params = {"serial": serial, "portId": portId}
    if name is not None: params['name'] = name
    if tags is not None: params['tags'] = tags
    if enabled is not None: params['enabled'] = enabled
    if poeEnabled is not None: params['poeEnabled'] = poeEnabled
    if type is not None: params['type'] = type
    if vlan is not None: params['vlan'] = vlan
    if voiceVlan is not None: params['voiceVlan'] = voiceVlan
    if allowedVlans is not None: params['allowedVlans'] = allowedVlans
    if isolationEnabled is not None: params['isolationEnabled'] = isolationEnabled
    if rstpEnabled is not None: params['rstpEnabled'] = rstpEnabled
    if stpGuard is not None: params['stpGuard'] = stpGuard
    if linkNegotiation is not None: params['linkNegotiation'] = linkNegotiation
    if portScheduleId is not None: params['portScheduleId'] = portScheduleId
    if udld is not None: params['udld'] = udld
    if accessPolicyType is not None: params['accessPolicyType'] = accessPolicyType
    if accessPolicyNumber is not None: params['accessPolicyNumber'] = accessPolicyNumber
    if macAllowList is not None: params['macAllowList'] = macAllowList
    if stickyMacAllowList is not None: params['stickyMacAllowList'] = stickyMacAllowList
    if stickyMacAllowListLimit is not None: params['stickyMacAllowListLimit'] = stickyMacAllowListLimit
    if stormControlEnabled is not None: params['stormControlEnabled'] = stormControlEnabled

    return await call_meraki_method("switch", "updateDeviceSwitchPort", **params)

print("Registered hybrid MCP: 12 common tools + call_meraki_api for full API access (804+ methods)")

###################
# DISCOVERY TOOLS
###################

@mcp.tool()
async def list_all_methods(section: str = None) -> str:
    """
    List all available Meraki API methods

    Args:
        section: Optional section filter (organizations, networks, wireless, switch, appliance, etc.)
    """
    methods_by_section = {}
    sections_to_check = [section] if section else SDK_SECTIONS

    for section_name in sections_to_check:
        if not hasattr(dashboard, section_name):
            continue

        section_obj = getattr(dashboard, section_name)
        methods = [m for m in dir(section_obj)
                  if not m.startswith('_') and callable(getattr(section_obj, m))]
        methods_by_section[section_name] = sorted(methods)

    return json.dumps({
        "sections": methods_by_section,
        "total_methods": sum(len(v) for v in methods_by_section.values()),
        "usage": "Use call_meraki_api(section='...', method='...', parameters='{...}') to call any method"
    }, indent=2)

@mcp.tool()
async def search_methods(keyword: str) -> str:
    """
    Search for Meraki API methods by keyword

    Args:
        keyword: Search term (e.g., 'admin', 'firewall', 'ssid', 'event')
    """
    keyword_lower = keyword.lower()
    results = {}

    for section_name in SDK_SECTIONS:
        if not hasattr(dashboard, section_name):
            continue

        section_obj = getattr(dashboard, section_name)
        methods = [m for m in dir(section_obj)
                  if not m.startswith('_')
                  and callable(getattr(section_obj, m))
                  and keyword_lower in m.lower()]

        if methods:
            results[section_name] = sorted(methods)

    return json.dumps({
        "keyword": keyword,
        "results": results,
        "total_matches": sum(len(v) for v in results.values()),
        "usage": "Use call_meraki_api(section='...', method='...', parameters='{...}')"
    }, indent=2)

@mcp.tool()
async def get_method_info(section: str, method: str) -> str:
    """
    Get detailed parameter information for a method

    Args:
        section: SDK section (e.g., 'organizations', 'networks')
        method: Method name (e.g., 'getOrganizationAdmins')
    """
    try:
        if not hasattr(dashboard, section):
            return json.dumps({
                "error": f"Section '{section}' not found",
                "available_sections": SDK_SECTIONS
            }, indent=2)

        section_obj = getattr(dashboard, section)

        if not hasattr(section_obj, method):
            return json.dumps({
                "error": f"Method '{method}' not found in '{section}'"
            }, indent=2)

        method_func = getattr(section_obj, method)
        sig = inspect.signature(method_func)

        params = {}
        for param_name, param in sig.parameters.items():
            if param_name == 'self':
                continue
            params[param_name] = {
                "required": param.default == inspect.Parameter.empty,
                "default": None if param.default == inspect.Parameter.empty else str(param.default)
            }

        return json.dumps({
            "section": section,
            "method": method,
            "parameters": params,
            "docstring": inspect.getdoc(method_func),
            "usage_example": f'call_meraki_api(section="{section}", method="{method}", parameters=\'{{...}}\')'
        }, indent=2)

    except Exception as e:
        return json.dumps({
            "error": str(e)
        }, indent=2)

@mcp.tool()
async def cache_stats() -> str:
    """Get cache statistics and configuration"""
    stats = cache.stats()
    stats['read_only_mode'] = READ_ONLY_MODE
    return json.dumps(stats, indent=2)

@mcp.tool()
async def cache_clear() -> str:
    """Clear all cached data"""
    cache.clear()
    return json.dumps({
        "status": "success",
        "message": "Cache cleared successfully"
    }, indent=2)

@mcp.tool()
async def get_mcp_config() -> str:
    """Get MCP configuration"""
    return json.dumps({
        "mode": "hybrid",
        "description": "12 pre-registered tools + call_meraki_api for full API access",
        "pre_registered_tools": ["getOrganizations", "getOrganizationAdmins", "getOrganizationNetworks",
                                  "getOrganizationDevices", "getNetwork", "getNetworkClients",
                                  "getNetworkEvents", "getNetworkDevices", "getDevice",
                                  "getNetworkWirelessSsids", "getDeviceSwitchPorts", "updateDeviceSwitchPort"],
        "generic_caller": "call_meraki_api - access all 804+ methods",
        "total_available_methods": "804+",
        "read_only_mode": READ_ONLY_MODE,
        "caching_enabled": ENABLE_CACHING,
        "cache_ttl_seconds": CACHE_TTL_SECONDS,
        "organization_id_configured": bool(MERAKI_ORG_ID),
        "api_key_configured": bool(MERAKI_API_KEY)
    }, indent=2)

# SSE Server Support
if __name__ == "__main__":
    import sys

    # Check if --sse flag is provided
    if "--sse" in sys.argv:
        # Run as SSE server
        import uvicorn
        from sse_starlette.sse import EventSourceResponse
        from starlette.applications import Starlette
        from starlette.routing import Route
        from starlette.requests import Request
        from starlette.responses import Response

        # Get port from command line or environment, default to 8000
        port = 8000
        for i, arg in enumerate(sys.argv):
            if arg == "--port" and i + 1 < len(sys.argv):
                port = int(sys.argv[i + 1])
        port = int(os.getenv("MCP_PORT", port))

        # Get host from environment, default to 0.0.0.0 for remote access
        host = os.getenv("MCP_HOST", "0.0.0.0")

        # Store active SSE connections
        from collections import defaultdict
        sse_connections = {}
        message_queues = defaultdict(asyncio.Queue)

        async def handle_sse(request: Request):
            """Handle SSE endpoint - clients connect here to receive events"""
            session_id = request.headers.get("x-session-id", "default")

            async def event_generator():
                queue = message_queues[session_id]
                try:
                    # Send initial connection event
                    yield {
                        "event": "endpoint",
                        "data": json.dumps({"endpoint": "/messages"})
                    }

                    # Keep connection alive and send messages
                    while True:
                        try:
                            message = await asyncio.wait_for(queue.get(), timeout=30.0)
                            yield {
                                "event": "message",
                                "data": json.dumps(message)
                            }
                        except asyncio.TimeoutError:
                            # Send keepalive
                            yield {
                                "event": "ping",
                                "data": json.dumps({"type": "ping"})
                            }
                except asyncio.CancelledError:
                    pass

            return EventSourceResponse(event_generator())

        async def handle_messages(request: Request):
            """Handle POST messages from clients"""
            session_id = request.headers.get("x-session-id", "default")

            try:
                # Parse incoming JSON-RPC message
                body = await request.json()

                # Get the method being called
                method = body.get("method")
                params = body.get("params", {})
                msg_id = body.get("id")

                # Handle different JSON-RPC methods
                if method == "initialize":
                    response = {
                        "jsonrpc": "2.0",
                        "id": msg_id,
                        "result": {
                            "protocolVersion": "2024-11-05",
                            "capabilities": {
                                "tools": {}
                            },
                            "serverInfo": {
                                "name": "Meraki Magic MCP",
                                "version": "1.0.0"
                            }
                        }
                    }
                elif method == "tools/list":
                    # Return list of available tools
                    tools_list = [
                        {"name": "call_meraki_api", "description": "Call any Meraki API method"},
                        {"name": "getOrganizations", "description": "Get all organizations"},
                        {"name": "getOrganizationAdmins", "description": "Get organization administrators"},
                        {"name": "getOrganizationNetworks", "description": "Get organization networks"},
                        {"name": "getOrganizationDevices", "description": "Get organization devices"},
                        {"name": "getNetwork", "description": "Get network details"},
                        {"name": "getNetworkClients", "description": "Get network clients"},
                        {"name": "getNetworkEvents", "description": "Get network events"},
                        {"name": "getNetworkDevices", "description": "Get network devices"},
                        {"name": "getDevice", "description": "Get device by serial"},
                        {"name": "getNetworkWirelessSsids", "description": "Get wireless SSIDs"},
                        {"name": "getDeviceSwitchPorts", "description": "Get switch ports"},
                        {"name": "updateDeviceSwitchPort", "description": "Update switch port"},
                        {"name": "list_all_methods", "description": "List all available API methods"},
                        {"name": "search_methods", "description": "Search for API methods"},
                        {"name": "get_method_info", "description": "Get method parameter info"},
                        {"name": "cache_stats", "description": "Get cache statistics"},
                        {"name": "cache_clear", "description": "Clear cache"},
                        {"name": "get_mcp_config", "description": "Get MCP configuration"}
                    ]
                    response = {
                        "jsonrpc": "2.0",
                        "id": msg_id,
                        "result": {"tools": tools_list}
                    }
                elif method == "tools/call":
                    # Execute a tool
                    tool_name = params.get("name")
                    tool_params = params.get("arguments", {})

                    # Map to actual async function
                    tool_map = {
                        "call_meraki_api": call_meraki_api,
                        "getOrganizations": getOrganizations,
                        "getOrganizationAdmins": getOrganizationAdmins,
                        "getOrganizationNetworks": getOrganizationNetworks,
                        "getOrganizationDevices": getOrganizationDevices,
                        "getNetwork": getNetwork,
                        "getNetworkClients": getNetworkClients,
                        "getNetworkEvents": getNetworkEvents,
                        "getNetworkDevices": getNetworkDevices,
                        "getDevice": getDevice,
                        "getNetworkWirelessSsids": getNetworkWirelessSsids,
                        "getDeviceSwitchPorts": getDeviceSwitchPorts,
                        "updateDeviceSwitchPort": updateDeviceSwitchPort,
                        "list_all_methods": list_all_methods,
                        "search_methods": search_methods,
                        "get_method_info": get_method_info,
                        "cache_stats": cache_stats,
                        "cache_clear": cache_clear,
                        "get_mcp_config": get_mcp_config
                    }

                    if tool_name in tool_map:
                        result = await tool_map[tool_name](**tool_params)
                        response = {
                            "jsonrpc": "2.0",
                            "id": msg_id,
                            "result": {
                                "content": [{"type": "text", "text": result}]
                            }
                        }
                    else:
                        response = {
                            "jsonrpc": "2.0",
                            "id": msg_id,
                            "error": {
                                "code": -32601,
                                "message": f"Tool not found: {tool_name}"
                            }
                        }
                else:
                    response = {
                        "jsonrpc": "2.0",
                        "id": msg_id,
                        "error": {
                            "code": -32601,
                            "message": f"Method not found: {method}"
                        }
                    }

                # Send response back via SSE
                await message_queues[session_id].put(response)

                return Response(status_code=202)

            except Exception as e:
                error_response = {
                    "jsonrpc": "2.0",
                    "id": body.get("id") if 'body' in locals() else None,
                    "error": {
                        "code": -32603,
                        "message": str(e)
                    }
                }
                await message_queues[session_id].put(error_response)
                return Response(status_code=500, content=str(e))

        # Create Starlette app
        app = Starlette(
            routes=[
                Route("/sse", endpoint=handle_sse),
                Route("/messages", endpoint=handle_messages, methods=["POST"]),
            ]
        )

        print(f"Starting Meraki Magic MCP Server in SSE mode on {host}:{port}")
        print(f"SSE endpoint: http://{host}:{port}/sse")
        print(f"Messages endpoint: http://{host}:{port}/messages")
        print("\nClients should connect to the SSE endpoint to use this server remotely")

        uvicorn.run(app, host=host, port=port)
    else:
        # Run as stdio server (default)
        print("Starting Meraki Magic MCP Server in stdio mode")
        mcp.run()
