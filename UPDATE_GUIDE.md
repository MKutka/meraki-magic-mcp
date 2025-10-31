# Keeping Your Meraki MCP Up-to-Date

## How Updates Work

The **dynamic MCP doesn't use the Postman collection** - it uses Python introspection on the Meraki SDK. This means:

✅ **When Meraki releases new API endpoints** → They update the Meraki Python SDK
✅ **When you update the SDK** → Your MCP automatically has the new endpoints
✅ **No code changes needed** → Just update the SDK and restart Claude Desktop

## Quick Update

```bash
cd /Users/apavlock/meraki-magic-mcp
source .venv/bin/activate
pip install --upgrade meraki
```

Then restart Claude Desktop - you'll automatically have any new endpoints!

## Automated Update Checker

I've created `update_meraki.py` that:
- ✅ Checks for new Meraki SDK versions
- ✅ Shows you what's new
- ✅ Updates the SDK
- ✅ Counts new endpoints
- ✅ Optionally downloads latest Postman collection (for reference)

### Run the Update Checker

```bash
cd /Users/apavlock/meraki-magic-mcp
source .venv/bin/activate
python3 update_meraki.py
```

It will:
1. Check your current SDK version
2. Check PyPI for the latest version
3. Ask if you want to update
4. Show how many new endpoints were added
5. Optionally download the latest Postman collection

## Schedule Automatic Checks (Optional)

### Option 1: Manual (Recommended)

Run the update checker once a month:
```bash
cd /Users/apavlock/meraki-magic-mcp && source .venv/bin/activate && python3 update_meraki.py
```

### Option 2: Cron Job (Advanced)

Add to your crontab to check weekly:
```bash
# Edit crontab
crontab -e

# Add this line (checks every Monday at 9 AM)
0 9 * * 1 cd /Users/apavlock/meraki-magic-mcp && .venv/bin/python3 update_meraki.py
```

### Option 3: Launchd (macOS native)

Create a launch agent for macOS:

1. Create the plist file:
```bash
nano ~/Library/LaunchAgents/com.meraki.mcp.update.plist
```

2. Add this content:
```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.meraki.mcp.update</string>
    <key>ProgramArguments</key>
    <array>
        <string>/Users/apavlock/meraki-magic-mcp/.venv/bin/python3</string>
        <string>/Users/apavlock/meraki-magic-mcp/update_meraki.py</string>
    </array>
    <key>StartCalendarInterval</key>
    <dict>
        <key>Hour</key>
        <integer>9</integer>
        <key>Minute</key>
        <integer>0</integer>
        <key>Weekday</key>
        <integer>1</integer>
    </dict>
    <key>StandardOutPath</key>
    <string>/Users/apavlock/meraki-magic-mcp/update.log</string>
    <key>StandardErrorPath</key>
    <string>/Users/apavlock/meraki-magic-mcp/update_error.log</string>
</dict>
</plist>
```

3. Load it:
```bash
launchctl load ~/Library/LaunchAgents/com.meraki.mcp.update.plist
```

## Postman Collection (Optional)

The Postman collection is **only used for reference/comparison** - it's not required for the MCP to work.

### Manual Download
Go to: https://www.postman.com/meraki-api/cisco-meraki-s-public-workspace/overview

### Automatic Download
1. Get a Postman API key: https://web.postman.co/settings/me/api-keys
2. Set environment variable:
   ```bash
   export POSTMAN_API_KEY='your-key-here'
   ```
3. Run the update script:
   ```bash
   python3 update_meraki.py
   ```

The script will download the latest collection and archive old ones.

## Update Workflow

```
┌─────────────────────────────────────────────┐
│  Meraki releases new API features          │
└────────────────┬────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────┐
│  Meraki updates Python SDK on PyPI          │
└────────────────┬────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────┐
│  You run: pip install --upgrade meraki      │
└────────────────┬────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────┐
│  Restart Claude Desktop                     │
└────────────────┬────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────┐
│  Dynamic MCP automatically has new endpoints│
└─────────────────────────────────────────────┘
```

## Checking for New Endpoints

After updating, you can see what's new:

```bash
# Count current endpoints
python3 inspect_tools.py

# Or in Claude Desktop, use:
list_available_tools
search_tools with keyword="new_feature_name"
```

## Version History Tracking

The update script will tell you:
- Current SDK version
- Latest available version
- How many new endpoints were added
- Total endpoints available

## Recommended Schedule

- **Check monthly**: Most users
- **Check weekly**: If you're actively developing
- **Check before major deployments**: Always good practice

## Troubleshooting

### "No module named meraki"
```bash
cd /Users/apavlock/meraki-magic-mcp
source .venv/bin/activate
pip install meraki
```

### "pip: command not found"
```bash
python3 -m pip install --upgrade meraki
```

### Update doesn't seem to work
1. Make sure you're in the virtual environment
2. Check you have internet connection
3. Try: `pip install --upgrade --force-reinstall meraki`

## Summary

**The key thing to remember**: The dynamic MCP uses the Meraki Python SDK, not the Postman collection. So:

1. Update the SDK: `pip install --upgrade meraki`
2. Restart Claude Desktop
3. Done! You have all new endpoints.

No code changes. No manual endpoint mapping. Fully automated! 🚀
