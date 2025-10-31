Meraki Magic MCP

Meraki Magic is a Python-based MCP (Model Context Protocol) server for Cisco's Meraki Dashboard. Meraki Magic provides tools for querying the Meraki Dashboard API to discover, monitor, and manage your Meraki environment.

## Two Versions Available

**🚀 Dynamic MCP (Recommended)** - `meraki-mcp-dynamic.py`
- **~804 API endpoints** automatically exposed
- **100% SDK coverage** - all Meraki API methods available
- **Auto-updates** when you upgrade the Meraki SDK
- **No manual coding** required for new endpoints

**📋 Manual MCP** - `meraki-mcp.py`
- **40 curated endpoints** with detailed schemas
- **Type-safe** with Pydantic validation
- **Custom business logic** for specific use cases
- **Clean documentation** for common operations

## Features

**Dynamic MCP includes:**
- All organization management (admins, networks, devices, inventory, licensing)
- Complete wireless management (SSIDs, RF profiles, Air Marshal, analytics)
- Full switch management (ports, VLANs, stacks, QoS, access policies)
- Advanced appliance/security (all firewall types, NAT, VPN, traffic shaping)
- Camera management (analytics, quality, schedules, permissions)
- Network monitoring (events, alerts, health, performance)
- Live troubleshooting tools (ping, cable test, ARP table)
- Webhooks and automation (alert profiles, action batches)
- And 700+ more endpoints...

**Manual MCP includes:**
- Network discovery and management
- Device discovery and configuration
- Client discovery and policy management
- Wireless SSID management
- Switch port and VLAN configuration
- Basic firewall rules
- Camera settings

## Quick Installation

### Prerequisites
- Python 3.8+
- Claude Desktop
- Meraki Dashboard API Key
- Meraki Organization ID

### Fast Track

**macOS:**
```bash
git clone https://github.com/YOUR_USERNAME/meraki-magic-mcp.git
cd meraki-magic-mcp
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env-example .env
# Edit .env with your API credentials
```

**Windows (PowerShell):**
```powershell
git clone https://github.com/YOUR_USERNAME/meraki-magic-mcp.git
cd meraki-magic-mcp
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env-example .env
# Edit .env with your API credentials
```

**📖 For detailed step-by-step instructions, see [INSTALL.md](INSTALL.md)**

## Configuration

Edit `.env` with your Meraki credentials:

```env
MERAKI_API_KEY="your_api_key_here"
MERAKI_ORG_ID="your_org_id_here"

# Optional: Performance tuning
ENABLE_CACHING=true
CACHE_TTL_SECONDS=300
READ_ONLY_MODE=false
```

Get your API key from: **Meraki Dashboard → Organization → Settings → Dashboard API access**

## Claude Desktop Setup

### Dynamic MCP (Recommended)

1. **Locate Claude config file:**
   - **macOS:** `~/Library/Application Support/Claude/claude_desktop_config.json`
   - **Windows:** `%APPDATA%\Claude\claude_desktop_config.json`

2. **Edit config with your paths:**

**macOS Example:**
```json
{
  "mcpServers": {
    "Meraki_Magic_MCP": {
      "command": "/Users/yourname/meraki-magic-mcp/.venv/bin/fastmcp",
      "args": [
        "run",
        "/Users/yourname/meraki-magic-mcp/meraki-mcp-dynamic.py"
      ]
    }
  }
}
```

**Windows Example:**
```json
{
  "mcpServers": {
    "Meraki_Magic_MCP": {
      "command": "C:/Users/YourName/meraki-magic-mcp/.venv/Scripts/fastmcp.exe",
      "args": [
        "run",
        "C:/Users/YourName/meraki-magic-mcp/meraki-mcp-dynamic.py"
      ]
    }
  }
}
```

**⚠️ Windows users:** Use forward slashes `/` and include `.exe` extension

3. **Restart Claude Desktop** (Quit completely, then reopen)

4. **Verify:** Ask Claude "What MCP servers are available?"

**📖 Detailed setup instructions: [INSTALL.md](INSTALL.md)**

### Manual MCP (Original)

Use `meraki-mcp.py` instead of `meraki-mcp-dynamic.py` in the config above.

### Both MCPs (Advanced)

You can run both simultaneously:

```json
{
  "mcpServers": {
    "Meraki_Curated": {
      "command": "/Users/apavlock/meraki-magic-mcp/.venv/bin/fastmcp",
      "args": ["run", "/Users/apavlock/meraki-magic-mcp/meraki-mcp.py"]
    },
    "Meraki_Full_API": {
      "command": "/Users/apavlock/meraki-magic-mcp/.venv/bin/fastmcp",
      "args": ["run", "/Users/apavlock/meraki-magic-mcp/meraki-mcp-dynamic.py"]
    }
  }
}
```

## Keeping Updated

The dynamic MCP automatically stays current with Meraki's API:

```bash
# Check for updates
python3 update_meraki.py

# Or manually update
pip install --upgrade meraki
```

Then restart Claude Desktop. See [UPDATE_GUIDE.md](UPDATE_GUIDE.md) for details.

## Performance & Safety Features

The dynamic MCP includes several optimizations:

✅ **Response Caching** - Read-only operations cached for 5 minutes (reduces API calls by 50-90%)
✅ **Read-Only Mode** - Optional safety mode blocks write operations
✅ **Auto-Retry** - Automatic retry on failures (3 attempts)
✅ **Rate Limit Handling** - Automatically waits when rate limited
✅ **Operation Labeling** - Tools labeled as [READ], [WRITE], or [MISC]

See [OPTIMIZATIONS.md](OPTIMIZATIONS.md) for details.

## Documentation

- **[INSTALL.md](INSTALL.md)** - Detailed installation guide (macOS & Windows)
- **[QUICKSTART.md](QUICKSTART.md)** - Get started quickly with examples
- **[README-DYNAMIC.md](README-DYNAMIC.md)** - Dynamic MCP technical details
- **[COMPARISON.md](COMPARISON.md)** - Compare manual vs dynamic approaches
- **[UPDATE_GUIDE.md](UPDATE_GUIDE.md)** - Keep your MCP current with latest APIs
- **[OPTIMIZATIONS.md](OPTIMIZATIONS.md)** - Performance and safety features

## How It Works

The Dynamic MCP provides two ways to access Meraki APIs:

1. **Pre-registered tools** (12 most common operations):
   - `getOrganizations`, `getOrganizationAdmins`, `getOrganizationNetworks`
   - `getNetworkClients`, `getNetworkEvents`, `getDeviceSwitchPorts`
   - And 6 more common operations

2. **Generic API caller** (`call_meraki_api`):
   - Access ALL 804+ Meraki API methods
   - Example: `call_meraki_api(section="appliance", method="getNetworkApplianceFirewallL3FirewallRules", parameters={"networkId": "L_123"})`

## Example Usage

```
Get all admins in my organization

Show me firewall rules for network "Main Office"

Update switch port 12 on device ABC123 to enable BPDU guard

Get wireless clients from the last hour

Create a new network named "Branch Office"
```

## Support

- **Issues:** [GitHub Issues](https://github.com/YOUR_USERNAME/meraki-magic-mcp/issues)
- **Meraki API Docs:** [developer.cisco.com/meraki/api-v1](https://developer.cisco.com/meraki/api-v1)
- **MCP Protocol:** [modelcontextprotocol.io](https://modelcontextprotocol.io)

## Contributing

Contributions welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Submit a pull request

## License

See [LICENSE](LICENSE) file for details.