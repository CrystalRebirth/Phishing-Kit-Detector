import sqlite3
from typing import Dict, List
import json

class BrandDatabase:
    def __init__(self, db_path: str = 'brands.db'):
        self.conn = sqlite3.connect(db_path)
        self._init_db()

    def _init_db(self):
        """Initialize database schema"""
        cursor = self.conn.cursor()
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS brands (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            domain TEXT UNIQUE NOT NULL,
            logo_hash TEXT,
            regex_patterns TEXT,
            last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS whitelist (
            domain TEXT PRIMARY KEY,
            added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)
        self.conn.commit()

    def add_brand(self, name: str, domain: str, patterns: List[str], logo_hash: str = None):
        # Add common phishing patterns for this brand
        if 'roblox' in name.lower():
            patterns.extend([
                r'robl?ox',  # Matches robx, roblox
                r'r[o0]bl?[o0]x',  # Matches r0bl0x, rob0x
                r'[\w-]*roblox[\w-]*',  # Matches wwww-roblox
                r'generator|free|rbx|rewards'  # Common phishing keywords
            ])
        """Add a new brand to the database"""
        cursor = self.conn.cursor()
        cursor.execute("""
        INSERT OR REPLACE INTO brands (name, domain, logo_hash, regex_patterns)
        VALUES (?, ?, ?, ?)
        """, (name, domain, logo_hash, json.dumps(patterns)))
        self.conn.commit()

    def get_brand_by_domain(self, domain: str) -> Dict:
        """Retrieve brand info by domain"""
        cursor = self.conn.cursor()
        cursor.execute("""
        SELECT name, domain, logo_hash, regex_patterns 
        FROM brands 
        WHERE domain = ?
        """, (domain,))
        row = cursor.fetchone()
        if row:
            return {
                'name': row[0],
                'domain': row[1],
                'logo_hash': row[2],
                'regex_patterns': json.loads(row[3])
            }
        return None

    def is_whitelisted(self, domain: str) -> bool:
        """Check if domain is in whitelist"""
        cursor = self.conn.cursor()
        cursor.execute("""
        SELECT 1 FROM whitelist WHERE domain = ?
        """, (domain,))
        return cursor.fetchone() is not None
