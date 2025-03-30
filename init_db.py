from phish_annihilator.data.db import BrandDatabase

def init_sample_data():
    db = BrandDatabase()
    
    # Add sample brands with common phishing targets
    brands = [
        {
            'name': 'Google',
            'domain': 'google.com',
            'patterns': ['g00gle', 'go0gle', 'gogle', 'googlé'],
            'logo_url': 'https://logo.clearbit.com/google.com'
        },
        {
            'name': 'Amazon',
            'domain': 'amazon.com', 
            'patterns': ['amaz0n', 'amaz0n', 'amaz0n-login', 'amaz0n-payment'],
            'logo_url': 'https://logo.clearbit.com/amazon.com'
        },
        {
            'name': 'Facebook',
            'domain': 'facebook.com',
            'patterns': ['faceb00k', 'facebok', 'facébook', 'facebook-login'],
            'logo_url': 'https://logo.clearbit.com/facebook.com'
        }
    ]

    for brand in brands:
        db.add_brand(
            name=brand['name'],
            domain=brand['domain'],
            patterns=brand['patterns'],
            logo_hash=None  # Will be populated by LogoHasher
        )

    print("Added sample brand data to database")

if __name__ == '__main__':
    init_sample_data()
