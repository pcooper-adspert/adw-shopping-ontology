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
            define_campaign_entity(session),
        ]
        relations = []
        rules = []

    return {'entities': entities, 'relations': relations, 'rules': rules}


# ----------------------------------------------------------------------------
# Entity Definitions
# ----------------------------------------------------------------------------

def define_campaign_entity(session: Session):
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
        plays campaign;

    """
    with session.transaction().write() as tx:
        entity = tx.put_entity_type('Campaign')

        # attributes
        entity.has(tx.put_attribute_type(
            'campaign-id',
            DataType.LONG))
        entity.has(tx.put_attribute_type(
            'campaign-name',
            DataType.STRING))
        entity.has(tx.put_attribute_type(
            'status',
            DataType.STRING))
        entity.has(tx.put_attribute_type(
            'aw-campaign-type',
            DataType.STRING))

        # roles
        entity.plays(tx.put_role('campaign'))

        id = entity.id

        tx.commit()

    return id


def define_adgroup_entity(session: Session):
    """AdGroup entity.

    define

    adgroup-id sub attribute, datatype long;
    adgroup-name sub attribute, datatype string;
    aw-adgroup-type sub attribute, datatype long;

    AdGroup sub entity,
        has adgroup-id,
        has campaign-id,
        has adgroup-name,
        has status,
        has aw-adgroup-type,
        plays parent
        plays child
        plays adgroup;

    """
    with session.transaction().write() as tx:
        entity = tx.put_entity_type('AdGroup')

        # attributes
        entity.has(tx.put_attribute_type(
            'adgroup-id', DataType.LONG))
        entity.has(tx.put_attribute_type(
            'campaign-id', DataType.LONG))
        entity.has(tx.put_attribute_type(
            'adgroup-name', DataType.STRING))
        entity.has(tx.put_attribute_type(
            'status', DataType.STRING))
        entity.has(tx.put_attribute_type(
            'aw-adgroup-type', DataType.STRING))

        # roles
        entity.plays(tx.put_role('adgroup'))

        id = entity.id

        tx.commit()

    return id


def define_abstract_criterion_entity(session: Session):
    """Criterion entity.

    define

    criterion-id sub attribute, datatype long;
    criterion-name sub attribute, datatype long;
    crit-key sub attribute, datatype long;

    Criterion sub entity is-abstract,
        has adgroup-id,
        has criterion-id,
        has criterion-name,
        has crit-key,
        has status,
        plays biddable-criterion;

    """
    with session.transaction().write() as tx:
        criterion = tx.put_entity_type('Criterion')
        criterion.is_abstract(True)
        id = criterion.id

        # attributes
        criterion.has(tx.put_attribute_type(
            'adgroup-id', DataType.LONG))
        criterion.has(tx.put_attribute_type(
            'criterion-id', DataType.LONG))
        criterion.has(tx.put_attribute_type(
            'crit-key', DataType.LONG))
        criterion.has(tx.put_attribute_type(
            'criterion-name', DataType.STRING))
        criterion.has(tx.put_attribute_type(
            'status', DataType.STRING))

        # roles
        criterion.plays(tx.put_role('biddable-criterion'))

        tx.commit()

    return id


# ----------------------------------------------------------------------------
# Relation Definitions
# ----------------------------------------------------------------------------

def define_campaign_adgroup_relation(session: Session):
    """AdGroup in Campaign.

    define

    campaign-adgroup sub relation,
        relates campaign,
        relates adgroup;

    """
    with session.transaction().write() as tx:
        rel = tx.put_relation_type('campaign-adgroup')
        id = rel.id

        rel.plays(tx.put_role('campaign'))
        rel.plays(tx.put_role('adgroup'))

        tx.commit()

    return id


def define_adgroup_criterion_relation(session: Session):
    """Criterion in AdGroup.

    define

    adgroup-criterion sub relation,
        relates adgroup,
        relates biddable-criterion;

    """
    with session.transaction().write() as tx:
        rel = tx.put_relation_type('adgroup-criterion')
        id = rel.id

        rel.plays(tx.put_role('adgroup'))
        rel.plays(tx.put_role('biddable-criterion'))

        tx.commit()

    return id


# ----------------------------------------------------------------------------
# Rules
# ----------------------------------------------------------------------------

def define_adgroup_in_campaign_rule(session: Session):
    """Infer campaign-adgroup relations via matching campaign-id."""
    with session.transaction().write() as tx:
        when = """
            $campaign isa Campaign, has campaign-id $campaign-id;
            $adgroup isa AdGroup, has campaign-id $campaign-id;
        """
        then = '(campaign: $campaign, adgroup: $adgroup) isa campaign-adgroup;'

        rule = tx.put_rule('adgroup-in-campaign', when, then)
        id = rule.id

        tx.commit()

    return id


def define_criterion_in_adgroup_rule(session: Session):
    """Infer adgroup-criterion relations via matching adgroup-id."""
    with session.transaction().write() as tx:
        when = """
            $adgroup isa AdGroup, has adgroup-id $adgroup-id;
            $criterion isa Criterion, has adgroup-id $adgroup-id;
        """

        then = ('(adgroup: $adgroup, biddable-criterion: $criterion) '
                'isa campaign-adgroup;')

        rule = tx.put_rule('criterion-in-adgroup', when, then)
        id = rule.id

        tx.commit()

    return id
