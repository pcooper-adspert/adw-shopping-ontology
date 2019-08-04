from . import account

# When listing required schema modules - order matters!
SCHEMA_MODULE_MAP = {
    'base': (account,),
    'shopping': (account, 'shopping', 'product'),
}
