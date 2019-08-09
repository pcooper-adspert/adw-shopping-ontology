import argparse
import functools
import logging
import pprint
from collections import deque

# from adspert.scripts.utils import get_account
# from adspert.base.app import adspert_app
# from adspert.database.db import configure_db
from grakn.client import GraknClient
from grakn.client import DataType
from grakn.client import Session

import schema


log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)

ROOT_NODE_ID = 293946777986


def apply_schema(keyspace: str, name: str):
    to_apply = schema.SCHEMA_MODULE_MAP[name]
    with GraknClient(uri='localhost:48555') as client:
        for schema_module in to_apply:
            # mod = importlib.import_module(schema_module)

            log.info(f'Applying Schema `{schema_module.__name__}`')
            concepts = schema_module.create_concepts(client, keyspace)

            # print concept descriptions
            for concept_name, concept_ids in concepts.items():
                print(f'\n{concept_name.title()}:')

                with client.session(keyspace=keyspace) as session:
                    partial = functools.partial(
                        describe_concept_type, session)
                    deque(map(partial, concept_ids), 0)

        log.info('Schema Updated')


def describe_concept_type(session: Session, concept_id):
    with session.transaction().read() as tx:
        concept = tx.get_concept(concept_id)

        if concept.is_thing():
            concept = concept.type()

        label = concept.label()

        if concept.is_entity_type():
            thing_type = 'an entity'
        elif concept.is_attribute_type():
            thing_type = 'an attribute'
        elif concept.is_relation_type():
            thing_type = 'a relation'
        elif concept.is_rule():
            thing_type = 'an inference rule'
        else:
            thing_type = 'Unknown'

        attrs = keys = roles = []
        if hasattr(concept, 'keys'):
            keys = [k.label() for k in concept.keys()]
        if hasattr(concept, 'attributes'):
            attrs = [a.label() for a in concept.attributes()]
        if hasattr(concept, 'playing'):
            roles = [r.label() for r in concept.playing()
                     if not r.label().startswith('@')]

        print(f'\n{label} with id {concept_id} is {thing_type}')

        if concept.is_rule():
            print('\nRule definition:')
            print(f'\twhen: {concept.get_when()}')
            print(f'\tthen: {concept.get_then()}\n\n')
        else:
            if keys:
                print('\nKeys: ', end='')
                pprint.pprint(keys)

            print('\nAttributes: ', end='')
            fattrs = '\n' + pprint.pformat(attrs) if attrs else 'None'
            print(fattrs)

            print('Roles: ', end='')
            froles = '\n' + pprint.pformat(roles) if roles else 'None'
            print(froles, end='\n' + str('-' * 79)+ '\n')

        tx.close()


def _relationship(label, tx):
    log.info(f'Add relationship `{label}`')
    rel = tx.put_relation_type(label)
    return rel


def _role(label, rel, tx):
    log.info(f'Add role `{label}`')
    role = tx.put_role(label)
    rel.relates(role)
    return role


def put_common_attributes(session: Session):
    """Colection of often used attributes.

    define

    status sub attribute, datatype string;

    """
    with session.transaction().write() as tx:
        tx.put_attribute_type('name', DataType.STRING)
        tx.put_attribute_type('status', DataType.STRING)
        tx.put_attribute_type('value', DataType.STRING)
        tx.commit()


parser = argparse.ArgumentParser()
parser.add_argument('-a', dest='adspert_id', required=False)
parser.add_argument('-k', dest='keyspace', required=True)
parser.add_argument('-n', dest='schema_name', required=True)

actions = parser.add_mutually_exclusive_group(required=True)
actions.add_argument('--apply', action='store_true')
actions.add_argument('--describe', action='store_true')

# optional
parser.add_argument('-s', dest='host', default='localhost')


def main(args):
    keyspace = args.keyspace
    schema = args.schema_name

    if args.apply:
        apply_schema(keyspace, schema)
    elif args.describe:
        # concept or entire schema?
        pass

    return 0


if __name__ == '__main__':
    # adspert_app.init('scripts', 'development')
    # configure_db()
    args = parser.parse_args()
    main(args)
