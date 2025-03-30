import unicodedata
from typing import Dict, List, Optional

HOMOGLYPH_MAP = {
    'а': 'a',  # Cyrillic
    'е': 'e',
    'і': 'i',
    '𝒸': 'c',  # Mathematical script
    '𝗮': 'a',  # Mathematical bold
    'ℂ': 'C',  # Double-struck
    'ⓔ': 'e',  # Circled
    '⒢': 'g'   # Parenthesized
}

class HomoglyphDetector:
    def __init__(self, brand_domains: List[str]):
        self.brand_domains = brand_domains

    def normalize_domain(self, domain: str) -> str:
        """Normalize domain by converting homoglyphs to ASCII."""
        normalized = []
        for char in domain:
            normalized.append(HOMOGLYPH_MAP.get(char, char))
        return unicodedata.normalize('NFKC', ''.join(normalized)).encode('ascii', 'ignore').decode()

    def is_homoglyph(self, char: str) -> bool:
        """Check if character is a non-Latin homoglyph."""
        latin_ranges = [(0x0041, 0x005A), (0x0061, 0x007A)]  # A-Z, a-z
        code_point = ord(char)
        return not any(start <= code_point <= end for start, end in latin_ranges)

    def visual_similarity_score(self, domain: str) -> float:
        """Calculate visual similarity score (0-1) for domain."""
        score = 0.0
        domain = domain.lower()
        
        # Check for common phishing patterns
        if any(pat in domain for pat in ['-login', 'verify', 'generator', 'rewards']):
            score += 0.5
            
        # Check for brand name variations
        for brand in self.brand_domains:
            brand = brand.split('.')[0].lower()
            if brand in domain or domain in brand:
                score += 0.3
            if any(c in domain for c in ['0', '1', 'l1']):  # Common number substitutions
                score += 0.2
                
        # Character-level checks
        normalized = self.normalize_domain(domain)
        for char in domain:
            if char in HOMOGLYPH_MAP:
                score += 0.5  # Partial match penalty
            elif self.is_homoglyph(char):
                score += 0.8  # Full penalty
                
        return min(score, 1.0)  # Cap at 1.0

    @staticmethod
    def test_homoglyphs():
        """Test homoglyph detection"""
        detector = HomoglyphDetector(['google.com', 'facebook.com'])
        test_domains = ['g00gle.com', 'faceb00k.com', 'аррӏе.com']
        results = detector.find_suspicious_domains(test_domains)
        print(f"Homoglyph Test: Detected {len(results)} suspicious domains")
        return results

    def find_suspicious_domains(self, domains: List[str]) -> Dict[str, float]:
        """Analyze list of domains and return suspicious ones with scores."""
        return {
            domain: self.visual_similarity_score(domain)
            for domain in domains
            if self.visual_similarity_score(domain) > 0.3
        }
