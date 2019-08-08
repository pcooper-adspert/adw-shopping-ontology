import logging

from grakn.client import DataType
from grakn.client import GraknClient
from grakn.client import Session

log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)

# ----------------------------------------------------------------------------
# Public Functions
# ----------------------------------------------------------------------------

def create_concepts(client: GraknClient, keyspace):
    log.info(f'Creating `account` concepts on "{keyspace}"\n')
    with client.session(keyspace=keyspace) as session:
        entities = [
            define_product_partition_entity(session),
            define_entity_product_dimension(session),
            define_entity_product(session),
        ]
        relations = [
            define_node_heirarchy_relation(session),
            define_ancestorship_relation(session),
            define_sibling_relation(session),
            define_offer_relationship(session),
            define_case_value_relation(session),
            # define_subdivision_relation(session), WIP still
        ]
        rules = [
            define_infer_node_hierarchy_rule(session),
            define_transitive_ancestorship_rule(session),
            define_node_adjacency_rule(session),
        ]

    return {'entities': entities, 'relations': relations, 'rules': rules}


# ----------------------------------------------------------------------------
# Entity Definitions
# ----------------------------------------------------------------------------

def define_product_partition_entity(session: Session):
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
        ent = tx.put_entity_type('ProductPartition')
        ent.sup(tx.get_schema_concept('Criterion'))

        ent.has(tx.put_attribute_type(
            'adgroup-id', DataType.LONG))
        ent.has(tx.put_attribute_type(
            'parent-id', DataType.LONG))
        ent.has( tx.put_attribute_type(
            'partition-type', DataType.STRING))

        ent.plays(tx.put_role('product-partition'))
        ent.plays(tx.put_role('parent-node'))
        ent.plays(tx.put_role('child-node'))

        id = ent.id
        
        tx.commit()

    return id


def define_entity_product_dimension(session: Session):
    """Product Dimension entity.

    define

    dimension-type sub attribute, datatype string;

    ProductDimension sub entity,
        has dimension-type,
        plays product-dimension;

    """

    with session.transaction().write() as tx:
        entity = tx.put_entity_type('ProductDimension')
        id = entity.id

        entity.has(tx.put_attribute_type('dimension-type', DataType.STRING))

        entity.plays(tx.put_role('product-dimension'))

        tx.commit()

    return id


def define_entity_product(session: Session):
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
        entity.has(tx.put_attribute_type('title', DataType.STRING))
        # entity.plays(tx.put_role('product'))

        id = entity.id

        tx.commit()

    return id


# ----------------------------------------------------------------------------
# Relation Definitions
# ----------------------------------------------------------------------------

def define_node_heirarchy_relation(session: Session):
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
        rel = tx.put_relation_type('node-heirarchy')
        id = rel.id

        rel.relates(tx.put_role('parent-node'))
        rel.relates(tx.put_role('child-node'))
        rel.plays(tx.put_role('ancestor'))
        rel.plays(tx.put_role('descedent'))

        

        tx.commit()

    return id


def define_ancestorship_relation(session: Session):
    """Relate two node heirarchies."""
    with session.transaction().write() as tx:
        rel = tx.put_relation_type('ancestorship')
        id = rel.id

        rel.relates(tx.put_role('ancestor'))
        rel.relates(tx.put_role('descedent'))

        tx.commit()

    return id


def define_sibling_relation(session: Session):
    with session.transaction().write() as tx:
        rel = tx.put_relation_type('siblings')
        id = rel.id

        rel.relates(tx.put_role('child-node'))

        tx.commit()

    return id


def define_offer_relationship(session: Session):
    q = """
    define

    product-offer sub relation,
        relates product,
        relates ad-group;
    """
    with session.transaction.write() as tx:
        tx.query(q)
        id = tx.get_schema_concept('product-offer').id

        tx.commit()

    return id


def define_case_value_relation(session: Session):
    """Relate Product Partitions to Product Dimensions.

    define

    dimension-value sub attribute, datatype string;

    case-value sub relationship,
        relates product-dimension,
        relates product-partition,
        has dimension-value;

    """
    with session.transaction().write() as tx:
        rel = tx.put_relation_type('case-value')
        id = rel.id

        rel.has(tx.put_attribute_type('dimension-value'))

        rel.relates(tx.put_role('product-dimension'))
        rel.relates(tx.put_role('product-partition'))

        tx.commit()

    return id


def define_subdivision_relation(session: Session):
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


# ----------------------------------------------------------------------------
# Relation Definitions
# ----------------------------------------------------------------------------

def define_infer_node_hierarchy_rule(session: Session):
    q = """define
    infer-node-heirarchy sub rule,
    when {
      $parent isa ProductPartition, has criterion-id $x, has adgroup-id $a-id;
      $child isa ProductPartition, has parent-id $y, has adgroup-id $a-id;
      $x == $y;
      $parent != $child;
    }, then {
      (parent-node: $parent, child-node: $child) isa node-heirarchy;
    };
    """
    with session.transaction.write() as tx:
        tx.query(q)
        id = tx.get_schema_concept('infer-node-heirarchy').id

        tx.commit()

    return id


def define_transitive_ancestorship_rule(session: Session):
    q = """define
    transitive-ancestorship sub rule,
    when {
      $r1 (parent-node: $a, child-node: $p) isa node-heirarchy;
      $r2 (parent-node: $p, child-node: $c) isa node-heirarchy;
      $a isa ProductPartition;
      $p isa ProductPartition;
      $c isa ProductPartition;
    }, then {
      (ancestor: $r1, descedent: $r2) isa ancestorship;
    };"""
    with session.transaction.write() as tx:
        tx.query(q)
        id = tx.get_schema_concept('transitive-ancestorship').id

        tx.commit()

    return id


def define_node_adjacency_rule(session: Session):
    q = """define
    node-adjacency sub rule,
    when {
      (parent: $p, $x) isa parent-child;
      (parent: $p, $y) isa parent-child;
      $x != $y;
    }, then {
      ($x, $y) isa siblings;
    };"""
    with session.transaction.write() as tx:
        tx.query(q)
        id = tx.get_schema_concept('node-adjacency').id

        tx.commit()
