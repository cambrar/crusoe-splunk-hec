# Crusoe to Splunk HEC Log Forwarder

A Python tool for fetching audit logs from the [Crusoe Cloud API](https://docs.crusoecloud.com/api/#tag/Audit-Logs/operation/getAuditLogs) and forwarding them to a Splunk HTTP Event Collector (HEC).

## Features

- ✅ Fetch audit logs from Crusoe Cloud API with pagination support
- ✅ Send logs to Splunk HEC in configurable batches
- ✅ Multiple operation modes: one-time, recent logs, time range, and daemon mode
- ✅ Comprehensive error handling and retry logic
- ✅ Health checks for both Crusoe API and Splunk HEC
- ✅ Dry-run mode for testing
- ✅ Configurable via environment variables
- ✅ Detailed logging and monitoring

## Installation

1. **Clone or download the repository**
   ```bash
   git clone https://github.com/cambrar/crusoe-splunk-hec.git
   cd crusoe-splunk-hec
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment variables**
   ```bash
   cp env.example .env
   # Edit .env with your actual configuration
   ```

## Configuration

### Required Environment Variables

#### Crusoe Cloud API

**Authentication Options** (choose one):

**Option 1: Access Key Authentication (Recommended)**
- `CRUSOE_ACCESS_KEY_ID`: Your Crusoe Cloud access key ID
- `CRUSOE_SECRET_ACCESS_KEY`: Your Crusoe Cloud secret access key
- `CRUSOE_REGION`: AWS region for request signing (default: `us-east-1`)

**Option 2: Token Authentication (Legacy)**
- `CRUSOE_API_TOKEN`: Your Crusoe Cloud API token

**Common Configuration**
- `CRUSOE_ORG_ID`: Your organization ID for audit logs
- `CRUSOE_BASE_URL`: API base URL (default: `https://api.crusoecloud.com/v1alpha5`)

#### Splunk HTTP Event Collector
- `SPLUNK_HEC_TOKEN`: Your Splunk HEC token
- `SPLUNK_HEC_URL`: Splunk HEC endpoint URL (e.g., `https://your-splunk.com:8088/services/collector`)

#### Optional Configuration
- `SPLUNK_INDEX`: Splunk index name (optional)
- `SPLUNK_SOURCETYPE`: Sourcetype for events (default: `crusoe:audit`)
- `SPLUNK_SOURCE`: Source for events (default: `crusoe_api`)
- `SPLUNK_VERIFY_SSL`: Verify SSL certificates (default: `true`)
- `BATCH_SIZE`: Number of events per batch (default: `100`)
- `REQUEST_TIMEOUT`: Request timeout in seconds (default: `30`)
- `MAX_RETRIES`: Maximum retries for failed requests (default: `3`)

### Getting Crusoe API Credentials

#### Access Key and Secret Key (Recommended)

1. **Access Keys**: 
   - Log into [Crusoe Cloud Console](https://console.crusoecloud.com)
   - Navigate to Settings > Access Keys or API Keys
   - Create a new access key pair
   - Copy both the Access Key ID and Secret Access Key

2. **Environment Setup**:
   ```bash
   # Add to your .env file
   CRUSOE_ACCESS_KEY_ID=your_access_key_id_here
   CRUSOE_SECRET_ACCESS_KEY=your_secret_access_key_here
   ```

#### API Token (Legacy Alternative)

1. **API Token**: 
   - Log into [Crusoe Cloud Console](https://console.crusoecloud.com)
   - Navigate to Settings > API Tokens
   - Create a new token with appropriate permissions

#### Organization ID

2. **Organization ID**:
   - Available in the Crusoe Cloud Console
   - Or retrieve via API: `GET /organizations`

### Setting up Splunk HEC

1. **Enable HEC in Splunk**:
   - Navigate to Settings > Data Inputs > HTTP Event Collector
   - Click "Global Settings" and enable "All Tokens"
   - Set the HTTP Port Number (default: 8088)

2. **Create HEC Token**:
   - Click "New Token"
   - Provide a name (e.g., "CrusoeAuditLogs")
   - Select or create an index for the logs
   - Configure sourcetype and other settings as needed
   - Save and copy the token value

## Usage

### Command Line Interface

The tool provides several commands for different use cases:

#### Check Configuration and Health
```bash
# Validate configuration
python main.py config-check

# Check connectivity to both services
python main.py health
```

#### Forward Recent Logs
```bash
# Forward logs from the last hour (default)
python main.py forward-recent

# Forward logs from the last 6 hours
python main.py forward-recent --hours 6

# Dry run (fetch but don't send to Splunk)
python main.py forward-recent --hours 1 --dry-run
```

#### Forward Logs for Specific Time Range
```bash
# Forward logs for a specific time range
python main.py forward-range --start-time "2024-01-01T00:00:00Z" --end-time "2024-01-01T23:59:59Z"

# Dry run for time range
python main.py forward-range --start-time "2024-01-01T00:00:00Z" --dry-run
```

#### Daemon Mode (Continuous Operation)
```bash
# Run continuously, forwarding logs every 5 minutes (300 seconds)
python main.py daemon

# Custom interval and lookback period
python main.py daemon --interval 600 --hours 2
```

### Example Workflow

1. **Initial Setup and Testing**:
   ```bash
   # Check configuration
   python main.py config-check
   
   # Test connectivity
   python main.py health
   
   # Test with a dry run
   python main.py forward-recent --hours 1 --dry-run
   ```

2. **One-time Log Forward**:
   ```bash
   # Forward logs from the last 24 hours
   python main.py forward-recent --hours 24
   ```

3. **Continuous Operation**:
   ```bash
   # Run as a daemon, checking every 10 minutes
   python main.py daemon --interval 600 --hours 1
   ```

## Log Format

Logs are sent to Splunk in the following format:

```json
{
  "time": 1234567890.123,
  "event": {
    "timestamp": "2024-01-01T12:00:00Z",
    "action": "create",
    "resource": "vm",
    "user": "user@example.com",
    "details": "Created VM instance 'vm-1234'",
    // ... other Crusoe audit log fields
  },
  "sourcetype": "crusoe:audit",
  "source": "crusoe_api",
  "index": "your_index"
}
```

## Error Handling

The tool includes comprehensive error handling:

- **Retry Logic**: Automatic retries for transient failures
- **Batch Processing**: If one batch fails, others continue processing
- **Graceful Degradation**: Continues operation even if some logs fail to send
- **Detailed Logging**: All operations are logged for debugging

## Monitoring and Logs

- Application logs are written to both console and `crusoe-splunk-hec.log`
- Health check commands can be used for monitoring
- Daemon mode includes regular status logging

## Production Deployment

For production use, consider:

1. **Process Management**: Use systemd, supervisor, or similar to manage the daemon process
2. **Environment Security**: Store credentials securely (e.g., AWS Secrets Manager, HashiCorp Vault)
3. **Monitoring**: Set up alerts based on log output and health checks
4. **Resource Limits**: Configure appropriate batch sizes and intervals based on your log volume
5. **Network**: Ensure firewall rules allow access to both Crusoe API and Splunk HEC

### Example systemd Service

```ini
[Unit]
Description=Crusoe to Splunk HEC Log Forwarder
After=network.target

[Service]
Type=simple
User=your-user
WorkingDirectory=/path/to/cursor-splunk-hec
Environment=PATH=/path/to/venv/bin
ExecStart=/path/to/venv/bin/python main.py daemon --interval 300 --hours 1
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

## Troubleshooting

### Common Issues

1. **Authentication Errors**:
   - Verify API tokens are correct and have appropriate permissions
   - Check that organization ID is correct for Crusoe API

2. **Network Connectivity**:
   - Ensure firewall rules allow outbound HTTPS traffic
   - Verify Splunk HEC endpoint is accessible
   - Check SSL certificate validation settings

3. **Splunk HEC Issues**:
   - Verify HEC is enabled in Splunk
   - Check that the index exists and is accessible
   - Confirm HEC token has write permissions

4. **No Logs Found**:
   - Verify the time range includes periods with activity
   - Check that audit logging is enabled in Crusoe Cloud
   - Ensure organization ID is correct

### Debug Mode

Enable debug logging by modifying the logging level in `main.py`:

```python
logging.basicConfig(level=logging.DEBUG, ...)
```

## API Reference

### Crusoe Cloud Audit Logs API

Based on the [official documentation](https://docs.crusoecloud.com/api/#tag/Audit-Logs/operation/getAuditLogs):

- **Endpoint**: `GET /organizations/{organization_id}/audit-logs`
- **Authentication**: Bearer token in Authorization header
- **Parameters**: Various filters for time range, pagination, etc.

### Splunk HTTP Event Collector

- **Endpoint**: `POST /services/collector`
- **Authentication**: `Splunk {token}` in Authorization header
- **Format**: NDJSON (newline-delimited JSON) events

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

MIT License - see LICENSE file for details.

## Support

For issues related to:
- **Crusoe Cloud API**: Check [Crusoe Cloud documentation](https://docs.crusoecloud.com)
- **Splunk HEC**: Check [Splunk documentation](https://docs.splunk.com)
- **This tool**: Create an issue in this repository
