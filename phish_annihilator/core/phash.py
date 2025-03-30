import imagehash
from PIL import Image
import requests
from io import BytesIO
from typing import Dict, Optional
import numpy as np

class LogoHasher:
    def __init__(self, brand_logos: Dict[str, str]):
        """
        Initialize with a dictionary of brand names to their logo URLs
        Args:
            brand_logos: {'amazon': 'https://.../amazon-logo.png', ...}
        """
        self.brand_hashes = {}
        for brand, url in brand_logos.items():
            try:
                response = requests.get(url)
                img = Image.open(BytesIO(response.content))
                self.brand_hashes[brand] = str(imagehash.phash(img))
            except Exception as e:
                print(f"Error processing {brand} logo: {e}")

    def calculate_phash(self, image_data: bytes) -> Optional[str]:
        """Calculate perceptual hash for an image"""
        try:
            img = Image.open(BytesIO(image_data))
            return str(imagehash.phash(img))
        except Exception:
            return None

    def find_similar_logos(self, image_data: bytes, threshold: int = 5) -> Dict[str, int]:
        """
        Compare image against known brand logos
        Returns dict of {brand_name: hamming_distance} for matches under threshold
        """
        query_hash = self.calculate_phash(image_data)
        if not query_hash:
            return {}

        results = {}
        for brand, brand_hash in self.brand_hashes.items():
            distance = self._hamming_distance(query_hash, brand_hash)
            if distance <= threshold:
                results[brand] = distance

        return results

    @staticmethod
    def test_logo_matching():
        """Test logo matching"""
        import requests
        try:
            hasher = LogoHasher({
                'amazon': 'https://logo.clearbit.com/amazon.com',
                'paypal': 'https://logo.clearbit.com/paypal.com'
            })
            test_logo = requests.get('https://logo.clearbit.com/amazon.com', timeout=5).content
            matches = hasher.find_similar_logos(test_logo)
            print(f"Logo Test: Found {len(matches)} matches")
            return matches
        except Exception as e:
            print(f"Logo Test Error: {str(e)}")
            return {}

    def _hamming_distance(self, hash1: str, hash2: str) -> int:
        """Calculate hamming distance between two phash strings"""
        return sum(c1 != c2 for c1, c2 in zip(hash1, hash2))
