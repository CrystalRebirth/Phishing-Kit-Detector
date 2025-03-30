from phish_annihilator.core import homoglyph, phash, network
import asyncio

async def run_tests():
    print("=== Phishing Detector Test Suite ===")
    
    print("\n[1/3] Testing Homoglyph Detection...")
    h_results = homoglyph.HomoglyphDetector.test_homoglyphs()
    
    print("\n[2/3] Testing Logo Matching...") 
    p_results = phash.LogoHasher.test_logo_matching()
    
    print("\n[3/3] Testing Network Capture...")
    n_results = await network.TrafficAnalyzer.test_network_capture()
    
    print("\n=== Test Summary ===")
    print(f"Homoglyph: Detected {len(h_results)} suspicious domains")
    print(f"Logo: Found {len(p_results)} matches")
    print(f"Network: Caught {len(n_results)} suspicious domains")
    
    return {
        'homoglyph': h_results,
        'logo': p_results,
        'network': n_results
    }

def main():
    return asyncio.run(run_tests())

if __name__ == "__main__":
    asyncio.run(run_tests())
