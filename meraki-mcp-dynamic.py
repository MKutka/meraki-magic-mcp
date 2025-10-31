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
async def call_meraki_api(section: str, method: str, parameters: dict = None) -> str:
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
    # Use empty dict if parameters not provided
    params = parameters if parameters is not None else {}

    # Call internal method
    return await to_async(_call_meraki_method_internal)(section, method, params)

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

# Execute and return the stdio output
if __name__ == "__main__":
    mcp.run()
