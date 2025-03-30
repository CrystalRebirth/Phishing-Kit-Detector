import redis
import json
from typing import Dict, Optional, Callable
import threading

class RedisAlertManager:
    def __init__(self, host: str = 'localhost', port: int = 6379):
        self.redis = None
        self.pubsub = None
        try:
            self.redis = redis.Redis(host=host, port=port, db=0, socket_connect_timeout=2)
            self.pubsub = self.redis.pubsub()
            self.redis.ping()  # Test connection
        except (redis.ConnectionError, redis.TimeoutError) as e:
            print(f"Redis connection failed: {e}. Alerts will only show in UI.")
            self.redis = None
        self.listener_thread = None

    def publish_alert(self, alert_data: Dict):
        """Publish a phishing alert to Redis"""
        if not self.redis:
            print(f"Alert (Redis not available): {alert_data}")
            return
            
        try:
            self.redis.publish(
                'phishing_alerts',
                json.dumps({
                    'domain': alert_data.get('domain'),
                    'risk_score': alert_data.get('risk_score'),
                    'reason': alert_data.get('reason'),
                    'timestamp': alert_data.get('timestamp')
                })
            )
        except redis.RedisError as e:
            print(f"Failed to publish alert: {e}")

    def subscribe_alerts(self, callback: Callable[[Dict], None]):
        """Subscribe to phishing alerts with a callback"""
        self.pubsub.subscribe('phishing_alerts')
        self.listener_thread = threading.Thread(
            target=self._listen_for_alerts,
            args=(callback,),
            daemon=True
        )
        self.listener_thread.start()

    def _listen_for_alerts(self, callback: Callable[[Dict], None]):
        """Internal listener for Redis pub/sub messages"""
        for message in self.pubsub.listen():
            if message['type'] == 'message':
                try:
                    alert = json.loads(message['data'])
                    callback(alert)
                except json.JSONDecodeError:
                    continue

    def cache_threat(self, domain: str, data: Dict, ttl: int = 3600):
        """Cache threat data with expiration"""
        if not self.redis:
            print(f"Cache failed (Redis not available): {domain}")
            return
            
        try:
            self.redis.setex(
                f'threat:{domain}',
                ttl,
                json.dumps(data)
            )
        except redis.RedisError as e:
            print(f"Failed to cache threat: {e}")

    def get_cached_threat(self, domain: str) -> Optional[Dict]:
        """Retrieve cached threat data"""
        if not self.redis:
            return None
            
        try:
            cached = self.redis.get(f'threat:{domain}')
            return json.loads(cached) if cached else None
        except redis.RedisError as e:
            print(f"Failed to get cached threat: {e}")
            return None
