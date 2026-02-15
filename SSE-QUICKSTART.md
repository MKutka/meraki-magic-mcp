# SSE Server Quick Start Guide

## What is SSE?

**SSE (Server-Sent Events)** allows your MCP server to run as an HTTP web server that clients can connect to remotely. This is what you need for Webex AI Agent.

**stdio** (current default) - Only works locally
**SSE** (what you need) - Works over the network

## Remote Server Setup

### 1. Deploy to your remote Mac or Linux VM

```bash
# Clone or copy the repository
cd /path/to/meraki-magic-mcp

# The startup script will handle virtual environment and dependencies
# Just make sure you have Python 3.8+ installed
```

### 2. Configure environment variables

```bash
# Copy example and edit
cp .env-example .env
nano .env
```

Add your credentials:
```env
MERAKI_API_KEY="your_api_key_here"
MERAKI_ORG_ID="your_org_id_here"

# SSE Server Settings (optional)
MCP_HOST=0.0.0.0  # 0.0.0.0 = accept remote connections
MCP_PORT=8000
```

### 3. Start the server

```bash
./start-sse-server.sh
```

That's it! The script will:
- ✅ Create virtual environment if needed
- ✅ Install dependencies if needed
- ✅ Validate your configuration
- ✅ Check port availability
- ✅ Start the SSE server

### 4. Your server is now accessible at:

```
http://YOUR-SERVER-IP:8000/sse
```

## Configuration Options

### Change Port
```bash
MCP_PORT=8080 ./start-sse-server.sh
```

Or add to `.env`:
```env
MCP_PORT=8080
```

### Local Only (for testing)
```env
MCP_HOST=127.0.0.1
```

### Remote Access (production)
```env
MCP_HOST=0.0.0.0
```

## Connecting Webex AI Agent

Point your Webex AI Agent to:
```
http://YOUR-SERVER-IP:8000/sse
```

Replace `YOUR-SERVER-IP` with the actual IP address of your Mac or Linux VM.

## Running as a Background Service

### Option 1: Using screen (simple)
```bash
screen -S meraki-mcp
./start-sse-server.sh
# Press Ctrl+A, then D to detach
# screen -r meraki-mcp to reattach
```

### Option 2: Using nohup
```bash
nohup ./start-sse-server.sh > server.log 2>&1 &
# View logs: tail -f server.log
```

### Option 3: systemd service (Linux only)

Create `/etc/systemd/system/meraki-mcp.service`:
```ini
[Unit]
Description=Meraki Magic MCP SSE Server
After=network.target

[Service]
Type=simple
User=yourusername
WorkingDirectory=/path/to/meraki-magic-mcp
ExecStart=/path/to/meraki-magic-mcp/start-sse-server.sh
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Then:
```bash
sudo systemctl enable meraki-mcp
sudo systemctl start meraki-mcp
sudo systemctl status meraki-mcp
```

## Testing

### 1. Test from the server itself
```bash
curl http://localhost:8000/sse
```

### 2. Test from another machine
```bash
curl http://YOUR-SERVER-IP:8000/sse
```

If this doesn't work, check your firewall settings.

## Firewall Configuration

### macOS
```bash
# Allow incoming connections on port 8000
sudo /usr/libexec/ApplicationFirewall/socketfilterfw --add /path/to/python
sudo /usr/libexec/ApplicationFirewall/socketfilterfw --unblockapp /path/to/python
```

### Linux (ufw)
```bash
sudo ufw allow 8000/tcp
sudo ufw reload
```

### Linux (firewalld)
```bash
sudo firewall-cmd --permanent --add-port=8000/tcp
sudo firewall-cmd --reload
```

## Troubleshooting

**"Port already in use"**
- Change the port: `MCP_PORT=8001 ./start-sse-server.sh`
- Or find what's using it: `lsof -i :8000`

**"Can't connect from remote machine"**
- Make sure `MCP_HOST=0.0.0.0` in `.env`
- Check firewall allows port 8000
- Verify server is running: `curl http://localhost:8000/sse`

**"MERAKI_API_KEY not set"**
- Create `.env` file with your credentials
- Copy from `.env-example` if needed

## Security for Production

If deploying to production:

1. **Use HTTPS** - Put behind nginx/Apache with SSL
2. **Add Authentication** - Implement API key verification
3. **Firewall** - Restrict access to specific IPs
4. **Keep .env Secret** - Never commit to git

## Stopping the Server

**If running in foreground:**
- Press `Ctrl+C`

**If running with screen:**
```bash
screen -r meraki-mcp
# Then press Ctrl+C
```

**If running with systemd:**
```bash
sudo systemctl stop meraki-mcp
```

**If running with nohup:**
```bash
# Find the process
ps aux | grep meraki-mcp-dynamic-sse
# Kill it
kill <PID>
```

## Support

- Main README: [README.md](README.md)
- Issue #2 related to this SSE implementation
