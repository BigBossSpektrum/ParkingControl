"""Settings desechables para generar las capturas del manual.

Apuntan la base de datos y los archivos subidos a docs/presentacion/, de modo
que sembrar datos de ejemplo nunca toque db.sqlite3 ni media/ del sistema real.
Solo lo usa docs/presentacion/; la aplicacion sigue arrancando con
parking_site.settings.
"""

from .settings import *  # noqa: F401,F403

_DEMO_DIR = BASE_DIR / 'docs' / 'presentacion'

DATABASES['default']['NAME'] = _DEMO_DIR / 'demo.sqlite3'

# Los QR y las fotos de la demo van aparte; DEBUG=True heredado de settings es
# lo que permite que runserver los sirva.
MEDIA_ROOT = _DEMO_DIR / 'media_demo'
