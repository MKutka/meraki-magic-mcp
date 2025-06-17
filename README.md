[![MseeP.ai Security Assessment Badge](https://mseep.net/pr/mkutka-meraki-magic-mcp-badge.png)](https://mseep.ai/app/mkutka-meraki-magic-mcp)

Meraki Magic MCP

Meraki Magic is a Python-based MCP (Model Context Protocol) server for Cisco's Meraki Dashboard. Meraki Magic provides tools for querying the Meraki Dashboard API to discover, moniter, and manage your Meraki environment.


## Features

- Network discovery
- Device discovery 
- Client discovery 
- Simple and extensible MCP server implementation

## Installation

1. Clone the repository:
```bash
git clone https://github.com/mkutka/meraki-magic.git
cd meraki-magic-mcp
```

2. Create a virtual environment and activate it:
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

## Configuration

1. Copy the example environment file:
```bash
cp .env-example .env
```

2. Update the `.env` file with your Meraki API Key and Organization ID:
```env
MERAKI_API_KEY="Meraki API Key here"
MERAKI_ORG_ID="Meraki Org ID here"
```

## Usage With Claude Desktop Client

1. Configure Claude Desktop to use this MCP server:

- Open Claude Desktop
- Go to Settings > Developer > Edit Config
- Add the following configuration file `claude_desktop_config.json`

```  
{
  "mcpServers": {
      "Meraki_Magic_MCP": {
        "command": "/Users/mkutka/meraki-magic-mcp/.venv/bin/fastmcp",
        "args": [
          "run",
          "/Users/mkutka/meraki-magic-mcp/meraki-mcp.py"
        ]
      }
  }
}
```

- Replace the path's above to reflect your local environment.

2. Restart Claude Desktop

3. Interact with Claude Desktop