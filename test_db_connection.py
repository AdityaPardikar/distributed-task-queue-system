#!/usr/bin/env python
"""Test database connection"""

from sqlalchemy import text
from src.db.session import engine

try:
    conn = engine.connect()
    result = conn.execute(text('SELECT version()'))
    print('✓ PostgreSQL connected')
    print(result.fetchone()[0])
    conn.close()
except Exception as e:
    print(f'✗ PostgreSQL connection failed: {e}')
