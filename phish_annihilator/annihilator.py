from typing import Dict, List, Optional
from .core import HomoglyphDetector, LogoHasher, TrafficAnalyzer
from .data import BrandDatabase, RedisAlertManager, PhishingScraper
import asyncio
from datetime import datetime
import logging

class PhishingAnnihilator:
    def __init__(self, config: Dict):
        """
        Args:
            config: {
                'redis': {'host': 'localhost', 'port': 6379},
                'phishtank_api_key': 'your-key',
                'virustotal_api_key': 'your-key',
                'brand_db_path': 'brands.db',
                'network_interface': 'eth0'
            }
        """
        self.config = config
        self.alert_callback = None  # Will be set by UI
        self.logger = self._setup_logging()
        
        # Initialize components
        self.db = BrandDatabase(config.get('brand_db_path', 'brands.db'))
        self.redis = RedisAlertManager(
            host=config.get('redis', {}).get('host', 'localhost'),
            port=config.get('redis', {}).get('port', 6379)
        )
        self.scraper = PhishingScraper({
            'phishtank': config.get('phishtank_api_key'),
            'virustotal': config.get('virustotal_api_key')
        })
        
        # Initialize detectors
        brand_domains = self._load_brand_domains()
        self.homoglyph_detector = HomoglyphDetector(brand_domains)
        self.logo_hasher = LogoHasher(self._load_brand_logos())
        self.traffic_analyzer = None
        if config.get('enable_network_monitoring', False):
            try:
                self.traffic_analyzer = TrafficAnalyzer(
                    callback=self._handle_detected_domain,
                    interface=config.get('network_interface', 'eth0')
                )
            except ImportError as e:
                print(f"Warning: Network monitoring disabled - {str(e)}")

    def _setup_logging(self):
        logger = logging.getLogger('phish_annihilator')
        logger.setLevel(logging.INFO)
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        ))
        logger.addHandler(handler)
        return logger

    def _load_brand_domains(self) -> List[str]:
        """Load brand domains from database"""
        # TODO: Implement actual loading from DB
        return ['google.com', 'amazon.com', 'facebook.com']

    def _load_brand_logos(self) -> Dict[str, str]:
        """Load brand logo URLs from database"""
        # TODO: Implement actual loading from DB
        return {
            'google': 'https://logo.clearbit.com/google.com',
            'amazon': 'https://logo.clearbit.com/amazon.com'
        }

    def _handle_detected_domain(self, domain: str):
        """Process a detected domain through all detectors"""
        if self.db.is_whitelisted(domain):
            return

        risk_score = 0
        reasons = []

        # Homoglyph detection
        homoglyph_score = self.homoglyph_detector.visual_similarity_score(domain)
        if homoglyph_score > 0.3:
            risk_score += homoglyph_score * 100
            reasons.append(f"Homoglyph score: {homoglyph_score:.2f}")

        # TODO: Add logo detection and other checks

        if risk_score > 50:  # Threshold for alerting
            self._trigger_alert(domain, risk_score, reasons)

    def _trigger_alert(self, domain: str, score: float, reasons: List[str]):
        """Publish alert to Redis, log it, show notification and notify UI"""
        alert_data = {
            'domain': domain,
            'risk_score': score,
            'reason': ', '.join(reasons),
            'timestamp': datetime.now().isoformat()
        }
        self.redis.publish_alert(alert_data)
        self.redis.cache_threat(domain, alert_data)
        self.logger.warning(f"ALERT: {alert_data}")
        
        try:
            from plyer import notification
            notification.notify(
                title=f"Phishing Alert ({score}% risk)",
                message=f"Potential phishing domain detected: {domain}\nReason: {reasons[0]}",
                app_name="Phishing Annihilator",
                timeout=10
            )
        except Exception as e:
            self.logger.error(f"Notification failed: {e}")
            
        if self.alert_callback:
            self.alert_callback(domain, score, reasons)

    async def run(self):
        """Start all components"""
        # Start network monitoring if enabled
        if self.traffic_analyzer:
            asyncio.create_task(self.traffic_analyzer.start_capture())

        # Start periodic scraping
        async for results in self.scraper.continuous_scrape():
            self.logger.info(f"Scraped {len(results)} new phishing URLs")
            # Process scraped results
            for entry in results:
                self._handle_detected_domain(entry['url'])
