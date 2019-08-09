from . import account
from . import shopping

# When listing required schema modules - order matters!
SCHEMA_MODULE_MAP = {
    'base': (account, ),
    'shopping': (account, shopping, ),
}
