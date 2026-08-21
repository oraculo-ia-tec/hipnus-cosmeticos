import sys
sys.path.insert(0, '.')
sys.path.insert(0, 'frontend')

from app.skills.auth_skill import verify_password

h = '9b5500f0afd63b680aeba1e4047ad572abe2fcacd0a20c9dc6ab0ebe1f4fca05'
print(f'hash len={len(h)}, is_sha256={len(h)==64}')
result = verify_password('helialda@2026', h)
print(f'verify_password result: {result}')
