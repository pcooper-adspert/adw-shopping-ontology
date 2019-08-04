import argparse
import importlib
import logging
import pprint
from collections import deque

from adspert.scripts.utils import get_account
from adspert.base.app import adspert_app
from adspert.database.db import configure_db
from grakn.client import GraknClient
from grakn.client import DataType
from grakn.client import Session

from src.schema import SCHEMA_MODULE_MAP


log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)

ROOT_NODE_ID = 293946777986


def apply_schema(keyspace: str, name: str):
    to_apply = SCHEMA_MODULE_MAP[name]
    with GraknClient(uri='localhost:48555') as client:
        for schema_module in to_apply:
            schema = importlib.import_module(schema_module)

            log.info(f'Applying Schema `{schema.__name__}`')
            concepts = schema.create_concepts(client, keyspace)

            # print concept descriptions
            for concept_name, concept_ids in concepts.items():
                print(f'{concept_name.title()} descriptions:')
                deque(map(describe_concept_type, concept_ids), 0)


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
        else:
            thing_type = 'Unknown'

        keys = [k.label() for k in concept.keys()]
        attrs = [a.label() for a in concept.attributes()]
        roles = [r.label() for r in concept.playing()]

        tx.close()

    print(f'{label} with id {concept_id} is {thing_type}')
    print('Keys: ', end='')
    pprint.pprint(keys)
    print('Attributes:')
    pprint.pprint(attrs)
    print('Roles:')
    pprint.pprint(roles)


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
        tx.put_attribute_type('dimension-type', DataType.STRING)
        tx.commit()


def put_shopping_attributes(session: Session):
    """Colection of shopping specific attributes."""
    pass

#############################
# heirarchical relationships
#############################





def parent_child_relationship(session: Session):
    """A basic heirarchical relationship.

    define

    parent-child sub relationship,
        relates parent,
        relates child,
        plays ancestor,
        plays descendent;

    ancestorship sub relationship,
        relates ancestor,
        relates descedent;

    """
    with session.transaction().write() as tx:
        rel = _relationship('parent-child', tx)
        id = rel.id

        _role('parent', rel, tx)
        _role('child', rel, tx)
        rel.plays(tx.put_role('ancestor'))
        rel.plays(tx.put_role('descedent'))

        rel = _relationship('ancestorship', tx)
        _role('ancestor', rel, tx)
        _role('descendent', rel, tx)

        rel = _relationship('siblings', tx)
        _role('product-partition', rel, tx)

        tx.commit()

    return id

#############################
# abstract relationships
#############################


def build_case_value_relationship(session: Session):
    """Relate Product Partitions to Product Dimensions.

    define

    dimension-value sub attribute, datatype string;

    case-value sub relationship,
        relates product-dimension,
        relates product-partition,
        has dimension-value;

    """

    with session.transaction().write() as tx:
        rel = _relationship('case-value', tx)
        rel.has(tx.get_schema_concept('value'))
        rel.relates(tx.put_role('product-dimension'))
        rel.relates(tx.put_role('product-partition'))

        id = rel.id
        tx.commit()

    return id


def build_subdivision_relationship(session: Session):
    with session.transaction().write() as tx:
        log.info('adding relationship "subdivision"')

        rel = tx.put_relation_type('subdivision')
        rel.relates(tx.put_role('parent'))
        rel.relates(tx.put_role('dimension-value'))
        rel.relates(tx.put_role('product-partition'))
        rel.has(tx.put_attribute_type('dimension-type', DataType.STRING))

        tx.get_schema_concept('value').plays(
            tx.put_role('dimension-value'))

        id = rel.id
        tx.commit()

    return id


def build_offer_relationship(session: Session):
    with session.transaction.write() as tx:
        log.info('adding relationship "offer"')

        q = """
            define

            ProductOffer sub relation,
                relates product,
                relates ad-group;
            """
        with session.transaction().write() as tx:
            r = tx.query(q)
            tx.commit()


def put_entity_campaign(session: Session):
    """Campaign entity.

    define

    campaign-id sub attribute, datatype long;
    campaign-name sub attribute, datatype string;
    aw-campaign-type sub attribute, datatype string;

    Campaign sub entity,
        has campaign-id,
        has campaign-name,
        has aw-campaign-type,
        has status,
        plays parent;

    """
    with session.transaction().write() as tx:
        campaign = tx.put_entity_type('Campaign')
        campaign.has(
            tx.put_attribute_type('campaign-id', DataType.LONG))
        campaign.has(
            tx.put_attribute_type('campaign-name', DataType.STRING))
        campaign.has(
            tx.put_attribute_type('status', DataType.STRING))
        campaign.has(
            tx.put_attribute_type('aw-campaign-type', DataType.STRING))

        campaign.plays(tx.put_role('parent'))

        id = campaign.id
        attrs = [a.label() for a in campaign.attributes()]
        roles = [r.label() for r in campaign.playing()]

        tx.commit()

    log.info(f'Done adding entity Campaign {id} '
             f'with {attrs} '
             f'playing {roles}')

    return id








def put_entity_product_partition(session: Session):
    """ProductPartition entity

    define

    parent-id sub criterion-id, datatype long;
    partition-type sub attribute, datatype string;

    ProductPartition sub criterion,
        has adgroup-id,
        has parent-id,
        has partition-type,
        plays product-partition,
        plays parent;

    """

    with session.transaction().write() as tx:
        partition = tx.put_entity_type('ProductPartition')
        partition.sup(tx.get_schema_concept('Criterion'))
        partition.has(
            tx.put_attribute_type('adgroup-id', DataType.LONG))
        partition.has(
            tx.put_attribute_type('parent-id', DataType.LONG))
        partition.has(
            tx.put_attribute_type('partition-type', DataType.STRING))

        partition.plays(tx.get_schema_concept('product-partition'))
        partition.plays(tx.get_schema_concept('parent'))
        partition.unplay(tx.put_role('ancestor'))
        partition.unplay(tx.put_role('descedent'))

        id = partition.id
        attrs = [a.label() for a in partition.attributes()]
        roles = [r.label() for r in partition.playing()]

        tx.commit()

    log.info(f'Done adding entity Product Partition {id} '
             f'with {attrs} '
             f'playing {roles}')

    return id


def put_entity_product_dimension(session: Session):
    """Product Dimension entity.

    define

    dimension-type sub attribute, datatype string;

    ProductDimension sub entity,
        has dimension-type,
        plays product-dimension;

    """

    with session.transaction().write() as tx:
        entity = tx.put_entity_type('ProductDimension')
        entity.has(tx.put_attribute_type('dimension-type', DataType.STRING))
        entity.plays(tx.put_role('product-dimension'))

        id = entity.id
        label = entity.label()
        attrs = [a.label() for a in entity.attributes()]
        roles = [r.label() for r in entity.playing()]

        tx.commit()

    log.info(f'Done adding entity {label} {id} '
             f'with {attrs} '
             f'playing {roles}')

    return id


def put_entity_product(session: Session):
    """Product entity.

    define

    item-id sub attribute, datatype string;
    title sub attribute, datatype string;

    Product sub entity,
        has item-id,
        has title,
        plays product;

    """
    with session.transaction().write() as tx:
        entity = tx.put_entity_type('Product')
        entity.has(tx.put_attribute_type('item-id', DataType.STRING))
        entity.has(tx.put_attribute_type('dimension-type', DataType.STRING))
        # entity.plays(tx.put_role('product'))

        id = entity.id
        label = entity.label()
        attrs = [a.label() for a in entity.attributes()]
        roles = [r.label() for r in entity.playing()]

        tx.commit()

    log.info(f'Done adding entity {label} {id} '
             f'with {attrs} '
             f'playing {roles}')

    return id


def apply_shopping_schema(session: Session):
    """Adwords Shopping Concepts."""
    log.info('Applying Shopping related schema changes and additions')

    log.info('Creating common attributes')
    put_common_attributes(session)

    log.info('Creating basic relationships')
    parent_child_relationship(session)
    adgroup_criterion_relationship(session)

    log.info('Creating account level entities')
    put_entity_campaign(session)
    put_entity_adgroup(session)
    put_abstract_entity_criterion(session)

    log.info('Creating shopping campaign relationships')
    build_case_value_relationship(session)
    build_subdivision_relationship(session)

    log.info('Creating shopping entities')
    put_entity_product(session)
    put_entity_product_partition(session)
    put_entity_product_dimension(session)

    log.info('Schema Updated')


parser = argparse.ArgumentParser()
parser.add_argument('-a', dest='adspert_id', required=True)
parser.add_argument('-s', dest='host', default='localhost')


def main(account, args):
    with GraknClient(uri=f"{args.host}:48555") as client:
        keyspace = account.account_name
        with client.session(keyspace=keyspace) as session:
            log.info(f'Connected to "{keyspace}"\n')
            apply_shopping_schema(session)


if __name__ == '__main__':
    adspert_app.init('scripts', 'development')
    configure_db()

    args = parser.parse_args()
    main(get_account(args.adspert_id), args)
