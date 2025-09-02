"""Crusoe Cloud API client for fetching audit logs."""

import logging
import time
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from config import CrusoeConfig

logger = logging.getLogger(__name__)


class CrusoeAPIError(Exception):
    """Custom exception for Crusoe API errors."""
    pass


class CrusoeClient:
    """Client for interacting with Crusoe Cloud API."""
    
    def __init__(self, config: CrusoeConfig):
        """Initialize the Crusoe client.
        
        Args:
            config: Crusoe configuration object
        """
        self.config = config
        self.session = self._create_session()
        
    def _create_session(self) -> requests.Session:
        """Create a requests session with retry strategy."""
        session = requests.Session()
        
        # Configure retry strategy
        retry_strategy = Retry(
            total=3,
            status_forcelist=[429, 500, 502, 503, 504],
            method_whitelist=["HEAD", "GET", "OPTIONS"],
            backoff_factor=1
        )
        
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        
        # Set default headers
        session.headers.update({
            "Authorization": f"Bearer {self.config.api_token}",
            "Content-Type": "application/json",
            "User-Agent": "crusoe-splunk-hec/1.0"
        })
        
        return session
    
    def get_audit_logs(
        self,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
        **kwargs
    ) -> List[Dict[str, Any]]:
        """Fetch audit logs from Crusoe Cloud API.
        
        Args:
            start_time: Start time for log filtering (ISO format)
            end_time: End time for log filtering (ISO format)
            limit: Maximum number of logs to return
            offset: Number of logs to skip
            **kwargs: Additional query parameters
            
        Returns:
            List of audit log entries
            
        Raises:
            CrusoeAPIError: If API request fails
        """
        url = f"{self.config.base_url}/organizations/{self.config.organization_id}/audit-logs"
        
        # Build query parameters
        params = {}
        if start_time:
            params["start_time"] = start_time.isoformat()
        if end_time:
            params["end_time"] = end_time.isoformat()
        if limit:
            params["limit"] = limit
        if offset:
            params["offset"] = offset
        
        # Add any additional parameters
        params.update(kwargs)
        
        try:
            logger.info(f"Fetching audit logs from {url} with params: {params}")
            response = self.session.get(url, params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            logs = data.get("items", [])
            
            logger.info(f"Successfully fetched {len(logs)} audit logs")
            return logs
            
        except requests.exceptions.RequestException as e:
            error_msg = f"Failed to fetch audit logs: {str(e)}"
            if hasattr(e, 'response') and e.response is not None:
                try:
                    error_detail = e.response.json()
                    error_msg += f" - {error_detail}"
                except:
                    error_msg += f" - Status: {e.response.status_code}"
            
            logger.error(error_msg)
            raise CrusoeAPIError(error_msg) from e
    
    def get_audit_logs_paginated(
        self,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        page_size: int = 100,
        max_pages: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Fetch audit logs with pagination support.
        
        Args:
            start_time: Start time for log filtering
            end_time: End time for log filtering
            page_size: Number of logs per page
            max_pages: Maximum number of pages to fetch (None for all)
            
        Returns:
            List of all audit log entries
        """
        all_logs = []
        offset = 0
        page_count = 0
        
        while True:
            if max_pages and page_count >= max_pages:
                break
                
            try:
                logs = self.get_audit_logs(
                    start_time=start_time,
                    end_time=end_time,
                    limit=page_size,
                    offset=offset
                )
                
                if not logs:
                    # No more logs available
                    break
                
                all_logs.extend(logs)
                offset += len(logs)
                page_count += 1
                
                # If we got fewer logs than page_size, we've reached the end
                if len(logs) < page_size:
                    break
                    
                # Small delay between requests to be respectful
                time.sleep(0.1)
                
            except CrusoeAPIError:
                # Re-raise API errors
                raise
            except Exception as e:
                logger.error(f"Unexpected error during pagination: {str(e)}")
                break
        
        logger.info(f"Fetched total of {len(all_logs)} audit logs across {page_count} pages")
        return all_logs
    
    def health_check(self) -> bool:
        """Check if the Crusoe API is accessible.
        
        Returns:
            True if API is accessible, False otherwise
        """
        try:
            # Try to fetch a small number of logs to test connectivity
            self.get_audit_logs(limit=1)
            return True
        except Exception as e:
            logger.error(f"Crusoe API health check failed: {str(e)}")
            return False
