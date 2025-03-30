import requests
import pandas as pd
import asyncio
from typing import List, Dict
from datetime import datetime
import time
from concurrent.futures import ThreadPoolExecutor

class PhishingScraper:
    def __init__(self, api_keys: Dict[str, str]):
        """
        Args:
            api_keys: {'phishtank': 'your-api-key', 'virustotal': 'your-api-key'}
        """
        self.api_keys = api_keys
        self.executor = ThreadPoolExecutor(max_workers=3)
        self.sources = {
            'phishtank': self._scrape_phishtank,
            'virustotal': self._scrape_virustotal
        }

    def scrape_all(self) -> List[Dict]:
        """Scrape all available sources"""
        results = []
        futures = []
        
        for source in self.sources:
            if self.api_keys.get(source):  # Only scrape if API key is provided
                futures.append(self.executor.submit(self.sources[source]))
        
        for future in futures:
            try:
                results.extend(future.result())
            except Exception as e:
                print(f"Error scraping: {e}")
                
        return results

    def _scrape_phishtank(self) -> List[Dict]:
        """Scrape PhishTank API"""
        url = "https://data.phishtank.com/data/{}/online-valid.json".format(
            self.api_keys.get('phishtank', '')
        )
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        return [{
            'url': entry['url'],
            'target': entry.get('target', 'unknown'),
            'verification_time': entry.get('verification_time', datetime.now().isoformat()),
            'source': 'phishtank'
        } for entry in data]

    def _scrape_virustotal(self) -> List[Dict]:
        """Scrape VirusTotal API"""
        url = "https://www.virustotal.com/api/v3/urls"
        headers = {
            "x-apikey": self.api_keys.get('virustotal')
        }
        params = {
            "filter": "last_submission_date:1d+ AND malicious_count:3+"
        }
        
        response = requests.get(url, headers=headers, params=params, timeout=15)
        response.raise_for_status()
        
        data = response.json().get('data', [])
        return [{
            'url': entry['attributes']['url'],
            'target': 'unknown',
            'verification_time': entry['attributes']['last_submission_date'],
            'source': 'virustotal',
            'malicious_count': entry['attributes']['last_analysis_stats']['malicious']
        } for entry in data]

    async def continuous_scrape(self, interval: int = 3600):
        """Run scraper continuously at specified interval (seconds)"""
        while True:
            try:
                results = self.scrape_all()
                yield results
                await asyncio.sleep(interval)
            except Exception as e:
                print(f"Scraping error: {e}")
                await asyncio.sleep(60)
