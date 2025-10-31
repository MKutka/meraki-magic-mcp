import os
import json
import meraki
import asyncio
import functools
from typing import Dict, List, Optional, Any, TypedDict, Union, Callable
from pydantic import BaseModel, Field
from mcp.server.fastmcp import FastMCP
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Create an MCP server
mcp = FastMCP("Meraki Magic MCP")

# Configuration
MERAKI_API_KEY = os.getenv("MERAKI_API_KEY")
MERAKI_ORG_ID = os.getenv("MERAKI_ORG_ID")

# Initialize Meraki API client using Meraki SDK
dashboard = meraki.DashboardAPI(api_key=MERAKI_API_KEY, suppress_logging=True)

###################
# ASYNC UTILITIES
###################

def to_async(func: Callable) -> Callable:
    """
    Convert a synchronous function to an asynchronous function

    Args:
        func: The synchronous function to convert

    Returns:
        An asynchronous version of the function
    """
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            lambda: func(*args, **kwargs)
        )
    return wrapper

# Create async versions of commonly used Meraki API methods
async_get_organizations = to_async(dashboard.organizations.getOrganizations)
async_get_organization = to_async(dashboard.organizations.getOrganization)
async_get_organization_networks = to_async(dashboard.organizations.getOrganizationNetworks)
async_get_organization_devices = to_async(dashboard.organizations.getOrganizationDevices)
async_get_network = to_async(dashboard.networks.getNetwork)
async_get_network_devices = to_async(dashboard.networks.getNetworkDevices)
async_get_network_clients = to_async(dashboard.networks.getNetworkClients)
async_get_device = to_async(dashboard.devices.getDevice)
async_update_device = to_async(dashboard.devices.updateDevice)
async_get_wireless_ssids = to_async(dashboard.wireless.getNetworkWirelessSsids)
async_update_wireless_ssid = to_async(dashboard.wireless.updateNetworkWirelessSsid)

###################
# SCHEMA DEFINITIONS
###################

# Wireless SSID Schema
class Dot11wSettings(BaseModel):
    enabled: bool = Field(False, description="Whether 802.11w is enabled or not")
    required: bool = Field(False, description="Whether 802.11w is required or not")

class Dot11rSettings(BaseModel):
    enabled: bool = Field(False, description="Whether 802.11r is enabled or not")
    adaptive: bool = Field(False, description="Whether 802.11r is adaptive or not")

class RadiusServer(BaseModel):
    host: str = Field(..., description="IP address of the RADIUS server")
    port: int = Field(..., description="Port of the RADIUS server")
    secret: str = Field(..., description="Secret for the RADIUS server")
    radsecEnabled: Optional[bool] = Field(None, description="Whether RADSEC is enabled or not")
    openRoamingCertificateId: Optional[int] = Field(None, description="OpenRoaming certificate ID")
    caCertificate: Optional[str] = Field(None, description="CA certificate for RADSEC")

class SsidUpdateSchema(BaseModel):
    name: Optional[str] = Field(None, description="The name of the SSID")
    enabled: Optional[bool] = Field(None, description="Whether the SSID is enabled or not")
    authMode: Optional[str] = Field(None, description="The auth mode for the SSID (e.g., 'open', 'psk', '8021x-radius')")
    enterpriseAdminAccess: Optional[str] = Field(None, description="Enterprise admin access setting")
    encryptionMode: Optional[str] = Field(None, description="The encryption mode for the SSID")
    psk: Optional[str] = Field(None, description="The pre-shared key for the SSID when using PSK auth mode")
    wpaEncryptionMode: Optional[str] = Field(None, description="WPA encryption mode (e.g., 'WPA1 and WPA2', 'WPA2 only')")
    dot11w: Optional[Dot11wSettings] = Field(None, description="802.11w settings")
    dot11r: Optional[Dot11rSettings] = Field(None, description="802.11r settings")
    splashPage: Optional[str] = Field(None, description="The type of splash page for the SSID")
    radiusServers: Optional[List[RadiusServer]] = Field(None, description="List of RADIUS servers")
    visible: Optional[bool] = Field(None, description="Whether the SSID is visible or not")
    availableOnAllAps: Optional[bool] = Field(None, description="Whether the SSID is available on all APs")
    bandSelection: Optional[str] = Field(None, description="Band selection for SSID (e.g., '5 GHz band only', 'Dual band operation')")

# Firewall Rule Schema
class FirewallRule(BaseModel):
    comment: str = Field(..., description="Description of the firewall rule")
    policy: str = Field(..., description="'allow' or 'deny'")
    protocol: str = Field(..., description="The protocol (e.g., 'tcp', 'udp', 'any')")
    srcPort: Optional[str] = Field("Any", description="Source port (e.g., '80', '443-8080', 'Any')")
    srcCidr: str = Field("Any", description="Source CIDR (e.g., '192.168.1.0/24', 'Any')")
    destPort: Optional[str] = Field("Any", description="Destination port (e.g., '80', '443-8080', 'Any')")
    destCidr: str = Field("Any", description="Destination CIDR (e.g., '192.168.1.0/24', 'Any')")
    syslogEnabled: Optional[bool] = Field(False, description="Whether syslog is enabled for this rule")

# Device Update Schema
class DeviceUpdateSchema(BaseModel):
    name: Optional[str] = Field(None, description="The name of the device")
    tags: Optional[List[str]] = Field(None, description="List of tags for the device")
    lat: Optional[float] = Field(None, description="Latitude of the device")
    lng: Optional[float] = Field(None, description="Longitude of the device")
    address: Optional[str] = Field(None, description="Physical address of the device")
    notes: Optional[str] = Field(None, description="Notes for the device")
    moveMapMarker: Optional[bool] = Field(None, description="Whether to move the map marker or not")
    switchProfileId: Optional[str] = Field(None, description="Switch profile ID")
    floorPlanId: Optional[str] = Field(None, description="Floor plan ID")

# Network Update Schema
class NetworkUpdateSchema(BaseModel):
    name: Optional[str] = Field(None, description="The name of the network")
    timeZone: Optional[str] = Field(None, description="The timezone of the network")
    tags: Optional[List[str]] = Field(None, description="List of tags for the network")
    enrollmentString: Optional[str] = Field(None, description="Enrollment string for the network")
    notes: Optional[str] = Field(None, description="Notes for the network")

#######################
# ORGANIZATION TOOLS  #
#######################

# Get organizations
@mcp.tool()
async def get_organizations() -> str:
    """Get a list of organizations the user has access to"""
    organizations = await async_get_organizations()
    return json.dumps(organizations, indent=2)

# Get organization details
@mcp.tool()
async def get_organization_details(org_id: str = None) -> str:
    """Get details for a specific organization, defaults to the configured organization"""
    organization_id = org_id or MERAKI_ORG_ID
    org_details = await async_get_organization(organization_id)
    return json.dumps(org_details, indent=2)

# Get networks from Meraki
@mcp.tool()
async def get_networks(org_id: str = None) -> str:
    """Get a list of networks from Meraki"""
    organization_id = org_id or MERAKI_ORG_ID
    networks = await async_get_organization_networks(organization_id)
    return json.dumps(networks, indent=2)

# Get devices from Meraki
@mcp.tool()
async def get_devices(org_id: str = None) -> str:
    """Get a list of devices from Meraki"""
    organization_id = org_id or MERAKI_ORG_ID
    devices = await async_get_organization_devices(organization_id)
    return json.dumps(devices, indent=2)

# Create network in Meraki
@mcp.tool()
def create_network(name: str, tags: list[str], productTypes: list[str], org_id: str = None, copyFromNetworkId: str = None) -> str:
    """Create a new network in Meraki, optionally copying from another network."""
    organization_id = org_id or MERAKI_ORG_ID
    kwargs = {}
    if copyFromNetworkId:
        kwargs['copyFromNetworkId'] = copyFromNetworkId
    network = dashboard.organizations.createOrganizationNetwork(organization_id, name, productTypes, tags=tags, **kwargs)
    return json.dumps(network, indent=2)

# Delete network in Meraki
@mcp.tool()
def delete_network(network_id: str) -> str:
    """Delete a network in Meraki"""
    dashboard.networks.deleteNetwork(network_id)
    return f"Network {network_id} deleted"

# Get organization status
@mcp.tool()
def get_organization_status(org_id: str = None) -> str:
    """Get the status and health of an organization"""
    organization_id = org_id or MERAKI_ORG_ID
    status = dashboard.organizations.getOrganizationStatus(organization_id)
    return json.dumps(status, indent=2)

# Get organization inventory
@mcp.tool()
def get_organization_inventory(org_id: str = None) -> str:
    """Get the inventory for an organization"""
    organization_id = org_id or MERAKI_ORG_ID
    inventory = dashboard.organizations.getOrganizationInventoryDevices(organization_id)
    return json.dumps(inventory, indent=2)

# Get organization license state
@mcp.tool()
def get_organization_license(org_id: str = None) -> str:
    """Get the license state for an organization"""
    organization_id = org_id or MERAKI_ORG_ID
    license_state = dashboard.organizations.getOrganizationLicensesOverview(organization_id)
    return json.dumps(license_state, indent=2)

#######################
# NETWORK TOOLS       #
#######################

# Get network details
@mcp.tool()
def get_network_details(network_id: str) -> str:
    """Get details for a specific network"""
    network = dashboard.networks.getNetwork(network_id)
    return json.dumps(network, indent=2)

# Get network devices
@mcp.tool()
def get_network_devices(network_id: str) -> str:
    """Get a list of devices in a specific network"""
    devices = dashboard.networks.getNetworkDevices(network_id)
    return json.dumps(devices, indent=2)

# Update network
@mcp.tool()
def update_network(network_id: str, update_data: NetworkUpdateSchema) -> str:
    """
    Update a network's properties using a schema-validated model

    Args:
        network_id: The ID of the network to update
        update_data: Network properties to update (name, timeZone, tags, enrollmentString, notes)
    """
    # Convert the Pydantic model to a dictionary and filter out None values
    update_dict = {k: v for k, v in update_data.dict().items() if v is not None}

    result = dashboard.networks.updateNetwork(network_id, **update_dict)
    return json.dumps(result, indent=2)

# Get clients from Meraki
@mcp.tool()
def get_clients(network_id: str, timespan: int = 86400) -> str:
    """
    Get a list of clients from a specific Meraki network.

    Args:
        network_id (str): The ID of the Meraki network.
        timespan (int): The timespan in seconds to get clients (default: 24 hours)

    Returns:
        str: JSON-formatted list of clients.
    """
    clients = dashboard.networks.getNetworkClients(network_id, timespan=timespan)
    return json.dumps(clients, indent=2)

# Get client details
@mcp.tool()
def get_client_details(network_id: str, client_id: str) -> str:
    """Get details for a specific client in a network"""
    client = dashboard.networks.getNetworkClient(network_id, client_id)
    return json.dumps(client, indent=2)

# Get client usage history
@mcp.tool()
def get_client_usage(network_id: str, client_id: str) -> str:
    """Get the usage history for a client"""
    usage = dashboard.networks.getNetworkClientUsageHistory(network_id, client_id)
    return json.dumps(usage, indent=2)

# Get client policy from Meraki
@mcp.tool()
async def get_client_policy(network_id: str, client_id: str) -> str:
    """
    Get the policy for a specific client in a specific Meraki network.

    Args:
        network_id (str): The ID of the Meraki network.
        client_id (str): The ID (MAC address or client ID) of the client.

    Returns:
        str: JSON-formatted client policy.
    """
    loop = asyncio.get_event_loop()
    policy = await loop.run_in_executor(
        None,
        lambda: dashboard.networks.getNetworkClientPolicy(network_id, client_id)
    )
    return json.dumps(policy, indent=2)

# Update client policy
@mcp.tool()
def update_client_policy(network_id: str, client_id: str, device_policy: str, group_policy_id: str = None) -> str:
    """Update policy for a client"""
    kwargs = {'devicePolicy': device_policy}
    if group_policy_id:
        kwargs['groupPolicyId'] = group_policy_id

    result = dashboard.networks.updateNetworkClientPolicy(network_id, client_id, **kwargs)
    return json.dumps(result, indent=2)

# Get network traffic analysis
@mcp.tool()
def get_network_traffic(network_id: str, timespan: int = 86400) -> str:
    """Get traffic analysis data for a network"""
    traffic = dashboard.networks.getNetworkTraffic(network_id, timespan=timespan)
    return json.dumps(traffic, indent=2)

#######################
# DEVICE TOOLS        #
#######################

# Get device details
@mcp.tool()
async def get_device_details(serial: str) -> str:
    """Get details for a specific device by serial number"""
    device = await async_get_device(serial)
    return json.dumps(device, indent=2)

# Update device
@mcp.tool()
async def update_device(serial: str, device_settings: DeviceUpdateSchema) -> str:
    """
    Update a device in the Meraki organization using a schema-validated model

    Args:
        serial: The serial number of the device to update
        device_settings: Device properties to update (name, tags, lat, lng, address, notes, etc.)

    Returns:
        Confirmation of the update with the new settings
    """
    # Convert the Pydantic model to a dictionary and filter out None values
    update_dict = {k: v for k, v in device_settings.dict().items() if v is not None}

    await async_update_device(serial, **update_dict)

    # Get the updated device details to return
    updated_device = await async_get_device(serial)

    return json.dumps({
        "status": "success",
        "message": f"Device {serial} updated",
        "updated_settings": update_dict,
        "current_device": updated_device
    }, indent=2)

# Claim devices into the Meraki organization
@mcp.tool()
def claim_devices(network_id: str, serials: list[str]) -> str:
    """Claim one or more devices into a Meraki network"""
    dashboard.networks.claimNetworkDevices(network_id, serials)
    return f"Devices {serials} claimed into network {network_id}"

# Remove device from network
@mcp.tool()
def remove_device(serial: str) -> str:
    """Remove a device from its network"""
    dashboard.networks.removeNetworkDevices(serial)
    return f"Device {serial} removed from network"

# Reboot device
@mcp.tool()
def reboot_device(serial: str) -> str:
    """Reboot a device"""
    result = dashboard.devices.rebootDevice(serial)
    return json.dumps(result, indent=2)

# Get device clients
@mcp.tool()
def get_device_clients(serial: str, timespan: int = 86400) -> str:
    """Get clients connected to a specific device"""
    clients = dashboard.devices.getDeviceClients(serial, timespan=timespan)
    return json.dumps(clients, indent=2)

# Get device status
@mcp.tool()
def get_device_status(serial: str) -> str:
    """Get the current status of a device"""
    status = dashboard.devices.getDeviceStatuses(serial)
    return json.dumps(status, indent=2)

# Get device uplink status
@mcp.tool()
def get_device_uplink(serial: str) -> str:
    """Get the uplink status of a device"""
    uplink = dashboard.devices.getDeviceUplink(serial)
    return json.dumps(uplink, indent=2)

#######################
# WIRELESS TOOLS      #
#######################

# Get wireless SSIDs
@mcp.tool()
async def get_wireless_ssids(network_id: str) -> str:
    """Get wireless SSIDs for a network"""
    ssids = await async_get_wireless_ssids(network_id)
    return json.dumps(ssids, indent=2)

# Update wireless SSID
@mcp.tool()
async def update_wireless_ssid(network_id: str, ssid_number: str, ssid_settings: SsidUpdateSchema) -> str:
    """
    Update a wireless SSID with comprehensive schema validation

    Args:
        network_id: The ID of the network containing the SSID
        ssid_number: The number of the SSID to update
        ssid_settings: Comprehensive SSID settings following the Meraki schema

    Returns:
        The updated SSID configuration
    """
    # Convert the Pydantic model to a dictionary and filter out None values
    update_dict = {k: v for k, v in ssid_settings.dict().items() if v is not None}

    result = await async_update_wireless_ssid(network_id, ssid_number, **update_dict)
    return json.dumps(result, indent=2)

# Get wireless settings
@mcp.tool()
def get_wireless_settings(network_id: str) -> str:
    """Get wireless settings for a network"""
    settings = dashboard.wireless.getNetworkWirelessSettings(network_id)
    return json.dumps(settings, indent=2)

# Get wireless clients
@mcp.tool()
def get_wireless_clients(network_id: str, timespan: int = 86400) -> str:
    """Get wireless clients for a network"""
    clients = dashboard.wireless.getNetworkWirelessClients(network_id, timespan=timespan)
    return json.dumps(clients, indent=2)

#######################
# SWITCH TOOLS        #
#######################

# Get switch ports
@mcp.tool()
def get_switch_ports(serial: str) -> str:
    """Get ports for a switch"""
    ports = dashboard.switch.getDeviceSwitchPorts(serial)
    return json.dumps(ports, indent=2)

# Update switch port
@mcp.tool()
def update_switch_port(serial: str, port_id: str, name: str = None, tags: list[str] = None, enabled: bool = None, vlan: int = None) -> str:
    """Update a switch port"""
    kwargs = {}
    if name:
        kwargs['name'] = name
    if tags:
        kwargs['tags'] = tags
    if enabled is not None:
        kwargs['enabled'] = enabled
    if vlan:
        kwargs['vlan'] = vlan

    result = dashboard.switch.updateDeviceSwitchPort(serial, port_id, **kwargs)
    return json.dumps(result, indent=2)

# Get switch VLAN settings
@mcp.tool()
def get_switch_vlans(network_id: str) -> str:
    """Get VLANs for a network"""
    vlans = dashboard.switch.getNetworkSwitchVlans(network_id)
    return json.dumps(vlans, indent=2)

# Create switch VLAN
@mcp.tool()
def create_switch_vlan(network_id: str, vlan_id: int, name: str, subnet: str = None, appliance_ip: str = None) -> str:
    """Create a switch VLAN"""
    kwargs = {}
    if subnet:
        kwargs['subnet'] = subnet
    if appliance_ip:
        kwargs['applianceIp'] = appliance_ip

    result = dashboard.switch.createNetworkSwitchVlan(network_id, vlan_id, name, **kwargs)
    return json.dumps(result, indent=2)

#######################
# APPLIANCE TOOLS     #
#######################

# Get security center
@mcp.tool()
def get_security_center(network_id: str) -> str:
    """Get security information for a network"""
    security = dashboard.appliance.getNetworkApplianceSecurityCenter(network_id)
    return json.dumps(security, indent=2)

# Get VPN status
@mcp.tool()
def get_vpn_status(network_id: str) -> str:
    """Get VPN status for a network"""
    vpn_status = dashboard.appliance.getNetworkApplianceVpnSiteToSiteVpn(network_id)
    return json.dumps(vpn_status, indent=2)

# Get firewall rules
@mcp.tool()
def get_firewall_rules(network_id: str) -> str:
    """Get firewall rules for a network"""
    rules = dashboard.appliance.getNetworkApplianceFirewallL3FirewallRules(network_id)
    return json.dumps(rules, indent=2)

# Update firewall rules
@mcp.tool()
def update_firewall_rules(network_id: str, rules: List[FirewallRule]) -> str:
    """
    Update firewall rules for a network using schema-validated models

    Args:
        network_id: The ID of the network
        rules: List of firewall rules following the Meraki schema

    Returns:
        The updated firewall rules configuration
    """
    # Convert the list of Pydantic models to a list of dictionaries
    rules_dict = [rule.dict(exclude_none=True) for rule in rules]

    result = dashboard.appliance.updateNetworkApplianceFirewallL3FirewallRules(network_id, rules=rules_dict)
    return json.dumps(result, indent=2)

#######################
# CAMERA TOOLS        #
#######################

# Get camera video settings
@mcp.tool()
def get_camera_video_settings(network_id: str, serial: str) -> str:
    """Get video settings for a camera"""
    settings = dashboard.camera.getDeviceCameraVideoSettings(serial)
    return json.dumps(settings, indent=2)

# Get camera quality and retention settings
@mcp.tool()
def get_camera_quality_settings(network_id: str) -> str:
    """Get quality and retention settings for cameras in a network"""
    settings = dashboard.camera.getNetworkCameraQualityRetentionProfiles(network_id)
    return json.dumps(settings, indent=2)

# Define resources
#Add a dynamic greeting resource
@mcp.resource("greeting: //{name}")
def greeting(name: str) -> str:
    """Greet a user by name"""
    return f"Hello {name}!"

#execute and return the stdio output
if __name__ == "__main__":
    mcp.run()