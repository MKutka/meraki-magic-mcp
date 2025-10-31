# Meraki Magic MCP - Complete Installation Guide

This guide provides step-by-step installation instructions for both macOS and Windows.

---

## Table of Contents
- [Prerequisites](#prerequisites)
- [macOS Installation](#macos-installation)
- [Windows Installation](#windows-installation)
- [Configuration](#configuration)
- [Claude Desktop Setup](#claude-desktop-setup)
- [Verification](#verification)
- [Troubleshooting](#troubleshooting)

---

## Prerequisites

### For Both Platforms:
- **Python 3.8 or higher** installed
- **Claude Desktop** installed ([Download here](https://claude.ai/download))
- **Meraki Dashboard API Key** ([Get one here](https://documentation.meraki.com/General_Administration/Other_Topics/Cisco_Meraki_Dashboard_API))
- **Meraki Organization ID** (found in Dashboard → Organization → Settings)

### Check Python Version:

**macOS/Linux:**
```bash
python3 --version
```

**Windows (Command Prompt):**
```cmd
python --version
```

**Windows (PowerShell):**
```powershell
python --version
```

If Python is not installed or version is < 3.8:
- **macOS:** Install from [python.org](https://www.python.org/downloads/) or use Homebrew: `brew install python`
- **Windows:** Install from [python.org](https://www.python.org/downloads/) (check "Add Python to PATH" during installation)

---

## macOS Installation

### Step 1: Open Terminal
- Press `Cmd + Space`, type "Terminal", press Enter

### Step 2: Clone the Repository
```bash
cd ~
git clone https://github.com/YOUR_USERNAME/meraki-magic-mcp.git
cd meraki-magic-mcp
```

**If you don't have git:**
```bash
# Install Homebrew first (if needed)
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install git
brew install git

# Then clone
git clone https://github.com/YOUR_USERNAME/meraki-magic-mcp.git
cd meraki-magic-mcp
```

### Step 3: Create Virtual Environment
```bash
python3 -m venv .venv
```

### Step 4: Activate Virtual Environment
```bash
source .venv/bin/activate
```

**You should see `(.venv)` appear in your terminal prompt.**

### Step 5: Install Dependencies
```bash
pip install -r requirements.txt
```

**Expected output:**
```
Successfully installed meraki-X.X.X fastmcp-X.X.X python-dotenv-X.X.X ...
```

### Step 6: Configure Environment Variables
```bash
# Copy example file
cp .env-example .env

# Edit with your preferred editor
nano .env
# OR
open -e .env
# OR
vim .env
```

**Add your credentials:**
```env
MERAKI_API_KEY="your_actual_api_key_here"
MERAKI_ORG_ID="your_org_id_here"

# Optional: Enable/disable caching (default: true)
ENABLE_CACHING=true

# Optional: Cache TTL in seconds (default: 300 = 5 minutes)
CACHE_TTL_SECONDS=300

# Optional: Read-only mode (default: false)
READ_ONLY_MODE=false
```

**Save and exit:**
- nano: `Ctrl + X`, then `Y`, then `Enter`
- vim: Press `Esc`, type `:wq`, press `Enter`

### Step 7: Get Absolute Path for Claude Config
```bash
pwd
```

**Copy the output** (e.g., `/Users/yourname/meraki-magic-mcp`)

---

## Windows Installation

### Step 1: Open Terminal

**Option A: Command Prompt**
- Press `Win + R`, type `cmd`, press Enter

**Option B: PowerShell (Recommended)**
- Press `Win + X`, select "Windows PowerShell" or "Terminal"

### Step 2: Navigate to Your Home Directory
**Command Prompt:**
```cmd
cd %USERPROFILE%
```

**PowerShell:**
```powershell
cd ~
```

### Step 3: Clone the Repository

**If you have git installed:**
```cmd
git clone https://github.com/YOUR_USERNAME/meraki-magic-mcp.git
cd meraki-magic-mcp
```

**If you don't have git:**
1. Download git from [git-scm.com](https://git-scm.com/download/win)
2. Install with default options
3. Restart terminal and run clone command above

**OR download as ZIP:**
1. Go to: https://github.com/YOUR_USERNAME/meraki-magic-mcp
2. Click green "Code" button → "Download ZIP"
3. Extract to `C:\Users\YourName\meraki-magic-mcp`
4. Navigate there in terminal:
   ```cmd
   cd %USERPROFILE%\meraki-magic-mcp
   ```

### Step 4: Create Virtual Environment
**Command Prompt & PowerShell:**
```cmd
python -m venv .venv
```

### Step 5: Activate Virtual Environment

**Command Prompt:**
```cmd
.venv\Scripts\activate.bat
```

**PowerShell:**
```powershell
.venv\Scripts\Activate.ps1
```

**If you get an execution policy error in PowerShell:**
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
.venv\Scripts\Activate.ps1
```

**You should see `(.venv)` appear in your terminal prompt.**

### Step 6: Install Dependencies
```cmd
pip install -r requirements.txt
```

**Expected output:**
```
Successfully installed meraki-X.X.X fastmcp-X.X.X python-dotenv-X.X.X ...
```

### Step 7: Configure Environment Variables
```cmd
# Copy example file
copy .env-example .env

# Edit with Notepad
notepad .env
```

**Add your credentials:**
```env
MERAKI_API_KEY="your_actual_api_key_here"
MERAKI_ORG_ID="your_org_id_here"

# Optional settings
ENABLE_CACHING=true
CACHE_TTL_SECONDS=300
READ_ONLY_MODE=false
```

**Save:** `Ctrl + S`
**Close:** `Alt + F4` or click X

### Step 8: Get Absolute Path for Claude Config

**Command Prompt:**
```cmd
cd
```

**PowerShell:**
```powershell
pwd
```

**Copy the output** (e.g., `C:\Users\YourName\meraki-magic-mcp`)

**Note:** For Windows paths, you'll need to convert backslashes to forward slashes in the Claude config:
- Windows path: `C:\Users\YourName\meraki-magic-mcp`
- Claude config: `C:/Users/YourName/meraki-magic-mcp`

---

## Configuration

### Getting Your Meraki Credentials

#### API Key:
1. Log into [Meraki Dashboard](https://dashboard.meraki.com)
2. Go to: **Organization → Settings → Dashboard API access**
3. Click **Enable API access** (if not already enabled)
4. Click **Generate new API key**
5. **Copy the key** (you won't be able to see it again!)
6. Paste into `.env` file

#### Organization ID:
1. In Meraki Dashboard, go to **Organization → Settings**
2. Look for **Organization ID** near the top
3. Copy the ID (format: `123456` or similar)
4. Paste into `.env` file

---

## Claude Desktop Setup

### Step 1: Locate Claude Desktop Config File

**macOS:**
```bash
# Open config file location
open ~/Library/Application\ Support/Claude/
```

Config file: `claude_desktop_config.json`

**Windows:**
```cmd
# Navigate to config location
cd %APPDATA%\Claude
```

Config file: `claude_desktop_config.json`

**If file doesn't exist**, create it:
- **macOS:** `touch ~/Library/Application\ Support/Claude/claude_desktop_config.json`
- **Windows:** `type nul > %APPDATA%\Claude\claude_desktop_config.json`

### Step 2: Edit Claude Desktop Config

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

**Windows Example (Command Prompt path style):**
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

**Windows Example (PowerShell path style):**
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

**Important for Windows:**
- Use forward slashes `/` (not backslashes `\`) in JSON
- Include `.exe` extension for fastmcp
- Replace `YourName` with your actual Windows username
- If your path has spaces, use quotes around the whole path

### Step 3: Restart Claude Desktop

**macOS:**
- Press `Cmd + Q` to quit Claude Desktop
- Reopen Claude Desktop from Applications

**Windows:**
- Right-click Claude in system tray → Exit
- Reopen Claude Desktop from Start Menu

---

## Verification

### Test in Claude Desktop:

**1. Check MCP is loaded:**
```
What MCP servers are available?
```

You should see "Meraki_Magic_MCP" listed.

**2. Test basic query:**
```
Get a list of my Meraki organizations
```

**3. Test a more complex query:**
```
Show me all admins in my Meraki organization
```

**4. Check configuration:**
```
Use get_mcp_config to show me the MCP configuration
```

Expected response includes:
- `mode: "hybrid"`
- `pre_registered_tools: 12`
- `total_available_methods: "804+"`
- `api_key_configured: true`

### Common Test Queries:

```
Get all networks in my organization

Show me devices in my network named "Main Office"

Get switch ports for device serial ABC123

Show me network events for the last hour

List all wireless SSIDs
```

---

## Troubleshooting

### Issue: "Module 'meraki' not found"

**Solution:**
```bash
# Make sure virtual environment is activated
# macOS:
source .venv/bin/activate

# Windows (CMD):
.venv\Scripts\activate.bat

# Windows (PowerShell):
.venv\Scripts\Activate.ps1

# Then reinstall
pip install -r requirements.txt
```

### Issue: "MCP server not showing up in Claude"

**Solutions:**
1. **Verify config file location:**
   - macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`
   - Windows: `%APPDATA%\Claude\claude_desktop_config.json`

2. **Verify JSON is valid:**
   - Use [jsonlint.com](https://jsonlint.com) to validate
   - Check for missing commas, quotes, brackets

3. **Verify paths are correct:**
   - Use absolute paths (not relative like `~/` or `.`)
   - Windows: Use forward slashes `/` and include `.exe`

4. **Restart Claude Desktop completely:**
   - Quit from menu/system tray, don't just close window

### Issue: "API Key Invalid" or "401 Unauthorized"

**Solutions:**
1. **Regenerate API key:**
   - Go to Meraki Dashboard → Organization → Settings → Dashboard API access
   - Generate new key
   - Update `.env` file

2. **Check .env file:**
   ```bash
   # macOS/Linux:
   cat .env | grep MERAKI_API_KEY

   # Windows:
   type .env | findstr MERAKI_API_KEY
   ```

3. **Verify no extra spaces or quotes:**
   ```env
   MERAKI_API_KEY="abc123"  ✅ Correct
   MERAKI_API_KEY= "abc123" ❌ Extra space
   MERAKI_API_KEY='abc123'  ❌ Wrong quotes
   ```

### Issue: Python version too old

**Check version:**
```bash
python --version
# or
python3 --version
```

**Needs to be 3.8 or higher.**

**Upgrade Python:**
- **macOS:** `brew upgrade python` or download from python.org
- **Windows:** Download latest from python.org

### Issue: "fastmcp: command not found" or "fastmcp.exe not found"

**Solution:**
```bash
# Verify fastmcp is installed
# macOS:
ls .venv/bin/fastmcp

# Windows:
dir .venv\Scripts\fastmcp.exe

# If missing, reinstall:
pip install --force-reinstall fastmcp
```

### Issue: Windows PowerShell execution policy error

**Solution:**
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

Then try activating virtual environment again.

### Issue: "Network timeout" or "Rate limit exceeded"

**Solutions:**
1. **Check internet connection**

2. **Verify API key has proper permissions**

3. **Enable rate limit handling** (already enabled by default):
   ```env
   # In .env - already set by default
   ENABLE_CACHING=true
   ```

4. **Increase cache TTL to reduce API calls:**
   ```env
   CACHE_TTL_SECONDS=600  # 10 minutes instead of 5
   ```

### Issue: Hitting conversation length limits in Claude

**This should be fixed in the current version!**

If you still experience this:
1. **Verify you're using `meraki-mcp-dynamic.py`** (not the old version)
2. **Restart Claude Desktop** after any changes
3. **Check the version has `call_meraki_api` tool:**
   ```
   Use search_methods with keyword="test" to verify
   ```

---

## Getting Help

### Check Logs

**macOS:**
```bash
# Claude Desktop logs
tail -f ~/Library/Logs/Claude/mcp*.log
```

**Windows:**
```cmd
# Navigate to logs
cd %LOCALAPPDATA%\Claude\logs
dir
```

### Enable Debug Output

Add to `.env`:
```env
DEBUG=true
```

Restart Claude Desktop and check logs for detailed output.

### Report Issues

If you encounter issues:
1. Check [Troubleshooting](#troubleshooting) section above
2. Search existing [GitHub Issues](https://github.com/YOUR_USERNAME/meraki-magic-mcp/issues)
3. Create new issue with:
   - Operating system and version
   - Python version (`python --version`)
   - Error message (full text)
   - Steps to reproduce

---

## Next Steps

Once installed:
- Read [QUICKSTART.md](QUICKSTART.md) for usage examples
- See [OPTIMIZATIONS.md](OPTIMIZATIONS.md) for performance features
- Check [UPDATE_GUIDE.md](UPDATE_GUIDE.md) to keep MCP current

**Welcome to Meraki Magic MCP!** 🎉
