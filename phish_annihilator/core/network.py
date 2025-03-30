try:
    import pyshark
    PYSHARK_AVAILABLE = True
except ImportError:
    PYSHARK_AVAILABLE = False

import asyncio
from typing import Callable, Optional
import tldextract
from concurrent.futures import ThreadPoolExecutor

class TrafficAnalyzer:
    def __init__(self, *args, **kwargs):
        if not PYSHARK_AVAILABLE:
            raise ImportError("pyshark is not available. Network monitoring disabled.")
    def __init__(self, 
                 callback: Callable[[str], None],
                 interface: str = 'eth0',
                 capture_filter: str = 'tcp port 80 or tcp port 443'):
        """
        Args:
            callback: Function to call when a new domain is detected
            interface: Network interface to monitor
            capture_filter: BPF filter for traffic capture
        """
        self.callback = callback
        self.interface = interface
        self.capture_filter = capture_filter
        self.executor = ThreadPoolExecutor(max_workers=1)
        self.loop = asyncio.new_event_loop()
        self.capture = None

    async def start_capture(self):
        """Start async network traffic capture"""
        self.capture = pyshark.LiveCapture(
            interface=self.interface,
            display_filter=self.capture_filter,
            use_json=True,
            include_raw=True
        )

        for packet in self.capture.sniff_continuously():
            domain = self._extract_domain(packet)
            if domain:
                self.executor.submit(self.callback, domain)

    def _extract_domain(self, packet) -> Optional[str]:
        """Extract domain from network packet"""
        try:
            if hasattr(packet, 'http') and hasattr(packet.http, 'host'):
                domain = tldextract.extract(packet.http.host).registered_domain
                print(f"HTTP Domain detected: {domain}")  # Debug log
                return domain
            elif hasattr(packet, 'tls'):
                if hasattr(packet.tls, 'handshake_extensions_server_name'):
                    domain = tldextract.extract(
                        packet.tls.handshake_extensions_server_name
                    ).registered_domain
                    print(f"TLS Domain detected: {domain}")  # Debug log
                    return domain
        except Exception as e:
            print(f"Domain extraction error: {str(e)}")  # Debug log
            return None
        print("No domain found in packet")  # Debug log
        return None

    @staticmethod
    async def test_network_capture():
        """Test network capture with simulated packets"""
        test_results = []
        
        def callback(domain):
            test_results.append(domain)
            print(f"Network Test: Detected suspicious domain - {domain}")

        analyzer = TrafficAnalyzer(callback)
        
        # Simulate HTTP packet
        http_packet = type('', (), {
            'http': type('', (), {'host': 'faceb00k-login.com'}),
            'tls': None
        })
        
        # Simulate TLS packet 
        tls_packet = type('', (), {
            'http': None,
            'tls': type('', (), {'handshake_extensions_server_name': 'paypa1.com'})
        })

        # Test packet processing
        analyzer._extract_domain(http_packet)
        analyzer._extract_domain(tls_packet)
        
        print(f"Network Test: Found {len(test_results)} suspicious domains")
        return test_results

    def stop_capture(self):
        """Stop network capture"""
        if self.capture:
            self.capture.close()
            self.loop.stop()
            self.executor.shutdown(wait=False)
