"""Main application for forwarding Crusoe audit logs to Splunk HEC."""

import logging
import sys
import time
from datetime import datetime, timedelta, timezone
from typing import Optional
import click

from config import AppConfig
from crusoe_client import CrusoeClient, CrusoeAPIError
from splunk_hec import SplunkHECClient, SplunkHECError

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('crusoe-splunk-hec.log')
    ]
)

logger = logging.getLogger(__name__)


class LogForwarder:
    """Main class for forwarding Crusoe audit logs to Splunk HEC."""
    
    def __init__(self, config: AppConfig):
        """Initialize the log forwarder.
        
        Args:
            config: Application configuration
        """
        self.config = config
        self.crusoe_client = CrusoeClient(config.crusoe)
        self.splunk_client = SplunkHECClient(config.splunk)
    
    def health_check(self) -> bool:
        """Perform health checks on both Crusoe API and Splunk HEC.
        
        Returns:
            True if both services are healthy, False otherwise
        """
        logger.info("Performing health checks...")
        
        crusoe_healthy = self.crusoe_client.health_check()
        if not crusoe_healthy:
            logger.error("Crusoe API health check failed")
            return False
        
        splunk_healthy = self.splunk_client.health_check()
        if not splunk_healthy:
            logger.error("Splunk HEC health check failed")
            return False
        
        logger.info("All health checks passed")
        return True
    
    def forward_logs(
        self,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        dry_run: bool = False
    ) -> int:
        """Forward audit logs from Crusoe to Splunk HEC.
        
        Args:
            start_time: Start time for log filtering
            end_time: End time for log filtering
            dry_run: If True, fetch logs but don't send to Splunk
            
        Returns:
            Number of logs successfully forwarded
        """
        try:
            # Fetch audit logs from Crusoe
            logger.info("Fetching audit logs from Crusoe API...")
            logs = self.crusoe_client.get_audit_logs_paginated(
                start_time=start_time,
                end_time=end_time,
                page_size=self.config.batch_size
            )
            
            if not logs:
                logger.info("No audit logs found")
                return 0
            
            logger.info(f"Retrieved {len(logs)} audit logs")
            
            if dry_run:
                logger.info("Dry run mode - not sending logs to Splunk")
                for i, log in enumerate(logs[:5]):  # Show first 5 logs
                    logger.info(f"Sample log {i+1}: {log}")
                return len(logs)
            
            # Send logs to Splunk HEC
            logger.info("Sending logs to Splunk HEC...")
            sent_count = self.splunk_client.send_events_batch(
                logs,
                batch_size=self.config.batch_size
            )
            
            return sent_count
            
        except CrusoeAPIError as e:
            logger.error(f"Failed to fetch logs from Crusoe API: {str(e)}")
            raise
        except SplunkHECError as e:
            logger.error(f"Failed to send logs to Splunk HEC: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error during log forwarding: {str(e)}")
            raise
    
    def forward_recent_logs(self, hours: int = 1, dry_run: bool = False) -> int:
        """Forward recent audit logs (last N hours).
        
        Args:
            hours: Number of hours back to fetch logs
            dry_run: If True, fetch logs but don't send to Splunk
            
        Returns:
            Number of logs successfully forwarded
        """
        end_time = datetime.now(timezone.utc)
        start_time = end_time - timedelta(hours=hours)
        
        logger.info(f"Forwarding logs from last {hours} hours ({start_time} to {end_time})")
        
        return self.forward_logs(start_time=start_time, end_time=end_time, dry_run=dry_run)


@click.group()
@click.option('--config-file', default='.env', help='Configuration file path')
@click.pass_context
def cli(ctx, config_file):
    """Crusoe to Splunk HEC Log Forwarder."""
    try:
        # Load configuration
        config = AppConfig.from_env()
        config.validate_config()
        
        # Create log forwarder
        forwarder = LogForwarder(config)
        
        # Store in context for subcommands
        ctx.ensure_object(dict)
        ctx.obj['forwarder'] = forwarder
        ctx.obj['config'] = config
        
    except Exception as e:
        logger.error(f"Failed to initialize application: {str(e)}")
        sys.exit(1)


@cli.command()
@click.pass_context
def health(ctx):
    """Check health of Crusoe API and Splunk HEC connections."""
    forwarder = ctx.obj['forwarder']
    
    if forwarder.health_check():
        click.echo("✅ All services are healthy")
        sys.exit(0)
    else:
        click.echo("❌ One or more services are unhealthy")
        sys.exit(1)


@cli.command()
@click.option('--hours', default=1, help='Number of hours back to fetch logs')
@click.option('--dry-run', is_flag=True, help='Fetch logs but do not send to Splunk')
@click.pass_context
def forward_recent(ctx, hours, dry_run):
    """Forward recent audit logs (last N hours)."""
    forwarder = ctx.obj['forwarder']
    
    try:
        sent_count = forwarder.forward_recent_logs(hours=hours, dry_run=dry_run)
        
        if dry_run:
            click.echo(f"✅ Found {sent_count} logs (dry run - not sent to Splunk)")
        else:
            click.echo(f"✅ Successfully forwarded {sent_count} logs to Splunk")
            
    except Exception as e:
        click.echo(f"❌ Error: {str(e)}")
        sys.exit(1)


@cli.command()
@click.option('--start-time', help='Start time (ISO format, e.g., 2024-01-01T00:00:00Z)')
@click.option('--end-time', help='End time (ISO format, e.g., 2024-01-01T23:59:59Z)')
@click.option('--dry-run', is_flag=True, help='Fetch logs but do not send to Splunk')
@click.pass_context
def forward_range(ctx, start_time, end_time, dry_run):
    """Forward audit logs for a specific time range."""
    forwarder = ctx.obj['forwarder']
    
    # Parse time arguments
    start_dt = None
    end_dt = None
    
    if start_time:
        try:
            start_dt = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
        except ValueError:
            click.echo(f"❌ Invalid start time format: {start_time}")
            sys.exit(1)
    
    if end_time:
        try:
            end_dt = datetime.fromisoformat(end_time.replace('Z', '+00:00'))
        except ValueError:
            click.echo(f"❌ Invalid end time format: {end_time}")
            sys.exit(1)
    
    try:
        sent_count = forwarder.forward_logs(
            start_time=start_dt,
            end_time=end_dt,
            dry_run=dry_run
        )
        
        if dry_run:
            click.echo(f"✅ Found {sent_count} logs (dry run - not sent to Splunk)")
        else:
            click.echo(f"✅ Successfully forwarded {sent_count} logs to Splunk")
            
    except Exception as e:
        click.echo(f"❌ Error: {str(e)}")
        sys.exit(1)


@cli.command()
@click.option('--interval', default=300, help='Interval between runs in seconds (default: 5 minutes)')
@click.option('--hours', default=1, help='Number of hours back to fetch logs each run')
@click.pass_context
def daemon(ctx, interval, hours):
    """Run in daemon mode, continuously forwarding logs."""
    forwarder = ctx.obj['forwarder']
    
    logger.info(f"Starting daemon mode: forwarding logs every {interval} seconds")
    
    while True:
        try:
            logger.info("Starting log forwarding cycle...")
            sent_count = forwarder.forward_recent_logs(hours=hours)
            logger.info(f"Forwarding cycle completed: {sent_count} logs sent")
            
        except KeyboardInterrupt:
            logger.info("Daemon mode interrupted by user")
            break
        except Exception as e:
            logger.error(f"Error in daemon cycle: {str(e)}")
            # Continue running even if one cycle fails
        
        logger.info(f"Sleeping for {interval} seconds...")
        time.sleep(interval)


@cli.command()
@click.pass_context
def config_check(ctx):
    """Validate configuration and display current settings."""
    config = ctx.obj['config']
    
    click.echo("Configuration Check:")
    click.echo(f"  Crusoe API URL: {config.crusoe.base_url}")
    click.echo(f"  Crusoe Org ID: {config.crusoe.organization_id}")
    click.echo(f"  Crusoe API Token: {'✅ Set' if config.crusoe.api_token else '❌ Missing'}")
    click.echo(f"  Splunk HEC URL: {config.splunk.hec_url}")
    click.echo(f"  Splunk HEC Token: {'✅ Set' if config.splunk.hec_token else '❌ Missing'}")
    click.echo(f"  Splunk Index: {config.splunk.index or 'Default'}")
    click.echo(f"  Splunk Sourcetype: {config.splunk.sourcetype}")
    click.echo(f"  Batch Size: {config.batch_size}")
    click.echo(f"  Request Timeout: {config.timeout}s")
    click.echo(f"  Max Retries: {config.max_retries}")


if __name__ == '__main__':
    cli()
