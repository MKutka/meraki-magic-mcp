# Manual vs. Dynamic MCP Comparison

## Overview

You now have **TWO versions** of the Meraki MCP server:

| Feature | Manual (`meraki-mcp.py`) | Dynamic (`meraki-mcp-dynamic.py`) |
|---------|--------------------------|-----------------------------------|
| **Tools** | 40 hand-coded endpoints | ~804 auto-generated endpoints |
| **Coverage** | 0.57% of API | 100% of SDK methods |
| **Type Safety** | ✅ Pydantic schemas | ❌ Generic kwargs |
| **Documentation** | ✅ Custom descriptions | ⚠️ Auto-generated |
| **Maintenance** | ❌ Manual updates needed | ✅ Auto-updates with SDK |
| **Custom Logic** | ✅ Can add per-endpoint | ❌ Generic wrapper |
| **Error Handling** | ✅ Built-in for all | ✅ Built-in for all |
| **Async Support** | ✅ Selective | ✅ All methods |

## What Each Version Includes

### Manual MCP (meraki-mcp.py)

**Organizations** (8 tools)
- get_organizations
- get_organization_details
- get_networks
- get_devices
- create_network
- delete_network
- get_organization_status
- get_organization_inventory
- get_organization_license

**Networks** (10 tools)
- get_network_details
- get_network_devices
- update_network (with NetworkUpdateSchema)
- get_clients
- get_client_details
- get_client_usage
- get_client_policy
- update_client_policy
- get_network_traffic

**Devices** (9 tools)
- get_device_details
- update_device (with DeviceUpdateSchema)
- claim_devices
- remove_device
- reboot_device
- get_device_clients
- get_device_status
- get_device_uplink

**Wireless** (4 tools)
- get_wireless_ssids
- update_wireless_ssid (with SsidUpdateSchema)
- get_wireless_settings
- get_wireless_clients

**Switch** (5 tools)
- get_switch_ports
- update_switch_port
- get_switch_vlans
- create_switch_vlan

**Appliance** (4 tools)
- get_security_center
- get_vpn_status
- get_firewall_rules
- update_firewall_rules (with FirewallRule schema)

**Camera** (2 tools)
- get_camera_video_settings
- get_camera_quality_settings

### Dynamic MCP (meraki-mcp-dynamic.py)

**All of the above PLUS:**

**Additional Organizations** (~164 more tools)
- Admin management (CRUD)
- Action batches
- Adaptive policy ACLs, groups, policies
- Alert profiles
- Branding policies
- Config templates
- Device migrations
- Packet capture
- Early access features
- Firmware upgrades (staged)
- Floor plans
- MQTT brokers
- SAML/SSO
- Policy objects
- SNMP settings
- Webhooks
- And much more...

**Additional Networks** (~104 more tools)
- Events and event types
- Bluetooth clients
- Network health metrics
- Traffic history
- Configuration changes
- Meraki auth users
- Floor plans
- Bind/unbind templates
- Split/combine networks
- And much more...

**Additional Wireless** (~101 more tools)
- RF profiles
- Air Marshal
- Bluetooth settings
- Channel utilization
- Client connection stats
- Ethernet ports (wireless APs)
- Failed connections
- Identity PSKs
- Latency stats
- Mesh status
- RADIUS servers
- SSID schedules
- Traffic analysis
- And much more...

**Additional Switch** (~96 more tools)
- Access control lists (ACLs)
- Access policies
- Alternate management interface
- DHCP server settings
- Link aggregation (LAG)
- MTU settings
- Multicast
- Port schedules
- QoS rules
- Routing (static, OSPF)
- STP settings
- Storm control
- Switch stacks
- Warm spare
- And much more...

**Additional Appliance** (~128 more tools)
- Content filtering
- DNS (local/split profiles)
- All firewall types (L3, L7, cellular, inbound)
- NAT rules (1:1, 1:Many, port forwarding)
- Ports configuration
- Radio settings
- SD-WAN policies
- Security (intrusion detection, malware)
- Static routes
- Traffic shaping (custom classes, rules, uplink)
- VLANs management
- VPN (BGP, site-to-site, third-party)
- Warm spare
- And much more...

**Additional Camera** (~43 more tools)
- Analytics (live, overview, recent, zones)
- Boundaries (areas, lines)
- Custom analytics artifacts
- Detection history
- Onboarding status
- Permissions
- Quality retention profiles
- Roles
- Schedules
- Sense (object detection)
- Snapshot generation
- Video links
- Wireless profiles
- And much more...

**Plus Entirely New Categories:**
- **Cellular Gateway** (24 tools) - DHCP, eSIM management, LAN, port forwarding, subnet pools
- **Sensor** (18 tools) - Alert profiles, commands, MQTT, readings, relationships
- **SM (Systems Manager)** (49 tools) - Mobile device management
- **Insight** (7 tools) - Application health monitoring
- **Licensing** (8 tools) - License management (co-term, subscription)
- **Administered** (4 tools) - Cross-org management

**Helper Tools** (3 tools)
- list_available_tools
- search_tools
- get_tool_info

## Example Use Cases

### Use Manual MCP When:

1. **Setting up a new network**
   - create_network
   - get_network_details
   - update_network

2. **Basic wireless config**
   - get_wireless_ssids
   - update_wireless_ssid

3. **Device management basics**
   - claim_devices
   - update_device
   - reboot_device

4. **Client monitoring**
   - get_clients
   - get_client_policy
   - update_client_policy

### Use Dynamic MCP When:

1. **Advanced wireless optimization**
   - wireless_getNetworkWirelessRfProfiles
   - wireless_createNetworkWirelessRfProfile
   - wireless_getNetworkWirelessChannelUtilizationHistory
   - wireless_getNetworkWirelessFailedConnections

2. **Security & compliance**
   - appliance_getNetworkApplianceFirewallL7FirewallRules
   - appliance_getNetworkApplianceSecurityIntrusion
   - organizations_getOrganizationConfigurationChanges
   - organizations_getOrganizationPiiRequests

3. **Troubleshooting**
   - networks_getNetworkEvents
   - devices_createDeviceLiveToolsPing
   - devices_createDeviceLiveToolsCableTest
   - networks_getNetworkHealthChannelUtilization

4. **Automation & webhooks**
   - organizations_createOrganizationWebhooksHttpServer
   - organizations_createOrganizationAlertsProfile
   - organizations_createOrganizationActionBatch

5. **Advanced switch management**
   - switch_createNetworkSwitchStack
   - switch_getNetworkSwitchAccessPolicies
   - switch_createNetworkSwitchPortSchedule
   - switch_getNetworkSwitchQosRules

6. **Licensing & admin**
   - organizations_getOrganizationAdmins
   - organizations_createOrganizationAdmin
   - licensing_getOrganizationLicensingCotermLicenses

7. **Camera analytics**
   - camera_getDeviceCameraAnalyticsLive
   - camera_getDeviceCameraAnalyticsZones
   - camera_generateDeviceCameraSnapshot

## Recommendation

**Start with Dynamic MCP** to get full API coverage. The manual version is a great reference for how to add:
- Custom Pydantic schemas for complex updates
- Specialized error handling
- Custom business logic

You can always extract frequently-used tools from the dynamic version and create curated versions with better schemas and documentation.

## Migration Path

1. **Phase 1**: Use dynamic MCP for everything
2. **Phase 2**: Identify your 10-20 most-used tools
3. **Phase 3**: Create curated versions with Pydantic schemas
4. **Phase 4**: Run both MCPs (curated + dynamic) for best of both worlds
