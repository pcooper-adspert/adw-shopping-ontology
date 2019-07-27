"""Copy the shopping structure of an account from Adspert account DB

Import all campaigns where:
    status == ACTIVE
    optimize == True
    aw_type == SHOPPING
    sales_country IN (VALID_SALES_COUNTRIES)

Import all Ad Groups contained in these campaigns where:
    status == ACTIVE

Import all Product Partitions for these Ad Groups

Import all Offers for these Ad Groups

For each distinct item_id in Offers, create a Product entity
with a ProductGroup mapping:

    product_dimension_type:value

"""
import logging
from typing import List
from typing import Tuple

from adspert.database.models.main import Account
from adspert.database.models.account import AdGroup
from adspert.database.models.account import AdwordsOffer
from adspert.database.models.account import Campaign
from adspert.database.models.account import ProductPartition
from adspert.scripts.utils import get_account
from adspert.base.app import adspert_app
from adspert.database.db import configure_db
from adspert.database.db import dbs
from grakn.client import GraknClient
from grakn.client import Session

log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)

GRAKN_SERVER = 'localhost'


def make_insert_query(label: str, obj: dict):
    base = f'insert $x isa {label}'
    attrs = ['has {} "{}"'.format(k.replace('_', '-'), v)
             for k, v in obj.items()]
    query = '{}, {};'.format(base, ', '.join(attrs))
    return query


def load_campaign_data(session,
                       campaign_types: Tuple,
                       include_paused: bool):
    """"""
    # fetch campaign data from accountdb
    q = Campaign.select(
            Campaign.campaign_id,
            Campaign.campaign_name,
            Campaign.aw_campaign_type,
            Campaign.status)
    q = q.where(Campaign.aw_campaign_type.in_(campaign_types))

    with session.transaction().write() as tx:
        entity = tx.get_schema_concept('Campaign')
        ids = []
        for r in q.dicts():
            campaign = entity.create()
            ids.append(campaign.id)
            for k, v in r.items():
                attr = tx.get_schema_concept(k.replace('_', '-'))
                campaign.has(attr.create(v))
        tx.commit()

    print('Inserted {} campaigns with IDs {} '.format(len(ids), ids))


def load_adgroup_data(session: Session,
                      limit: int = 0,
                      adgroup_types: Tuple = (),
                      include_paused: bool = False):
    """Load ad group data from account db."""
    q = AdGroup.select(
        AdGroup.adgroup_id,
        AdGroup.adgroup_name,
        AdGroup.campaign_id,
        AdGroup.status,
        AdGroup.aw_adgroup_type)
    q = q.where(AdGroup.status == 'Active')
    if adgroup_types:
        q = q.where(AdGroup.aw_adgroup_type.in_(adgroup_types))
    if limit:
        q = q.limit(limit)

    ids = []
    for r in q.dicts():
        # keep entity references consistent
        r['campaign_id'] = r['campaign']
        del r['campaign']

        with session.transaction().write() as tx:
            adgroup = tx.get_schema_concept('AdGroup').create()
            ids.append(adgroup.id)
            for k, v in r.items():
                try:
                    attr = tx.get_schema_concept(k.replace('_', '-'))
                    adgroup.has(attr.create(v))
                except TypeError:
                    pass
            tx.commit()

    print('Inserted {} adgroups with IDs {} '.format(
        len(ids), ids))


def load_product_partition_data(
        session: Session, adgroup_ids: Tuple = ()):
    """Load ad group data from account db."""

    q = ProductPartition.select(
        ProductPartition.criterion_id,
        ProductPartition.adgroup_id,
        ProductPartition.dimension_type,
        ProductPartition.dimension_value,
        ProductPartition.partition_type,
        ProductPartition.parent_id)
    if adgroup_ids:
        q = q.where(ProductPartition.adgroup_id.in_(adgroup_ids))

    inserts = ['insert']
    tpl = ('$pp isa ProductPartition, '
           'has criterion-id {}, '
           'has adgroup-id {}, '
           'has partition-type {} '
           'has parent-id {};')

    ids = []
    for r in q.dicts():
        dt = r.pop('dimension_type')
        dv = r.pop('dimension_value')

        q = tpl.format(*r.values())
        inserts.append(q)

        with session.transaction().write() as tx:
            pp = tx.get_schema_concept('ProductPartition').create()
            for k, v in r.items():
                attr = tx.get_schema_concept(k.replace('_', '-'))
                pp.has(attr.create(v))
            ids.append(pp.id)
            tx.commit()

        if dt:
            with session.transaction().write() as tx:
                it = tx.query(
                    'match $x isa ProductDimension, '
                    f'has dimension-type "{dt}"; get;')
                pd = next(iter(it.collect_concepts()), None)
                if not pd:
                    pd = tx.get_schema_concept('ProductDimension').create()
                    pd.has(tx.get_schema_concept('dimension-type').create(dt))

                dv = tx.get_schema_concept('value').create(dv)

                cv = tx.get_schema_concept('case-value').create()
                cv.has(dv)
                cv.assign(tx.put_role('product-dimension'), pd)
                cv.assign(tx.put_role(
                    'product-partition'), tx.get_concept(ids[-1]))
                tx.commit()
    else:
        query = '\n'.join(inserts)
        print(query)

    print(
        'Inserted {} partitions with IDs {} '.format(
            len(ids), ids))


def load_product_data(session: Session, adgroup_ids: Tuple = ()):
    """Product Data."""
    q = AdwordsOffer.select(
        AdwordsOffer.adgroup_id,
        AdwordsOffer.item_id)
    if adgroup_ids:
        q = q.where(AdwordsOffer.adgroup_id.in_(adgroup_ids))

    ids = []
    for row in q.dicts():
        with session.transaction().write() as tx:
            attr = tx.put_attribute_type('item-id')
            e = tx.put_entity_type('Product').create()
            e.has(attr.create(row['item_id']))

            ids.append(e.id)
            tx.commit()


def import_account_structure(account: Account,
                             campaign_types: List[str],
                             include_paused: bool = False,
                             include=(), exclude=()):
    """Import Adspert account structure into Grakn keyspace."""
    log.info(
        f'Importing the account structure of {account.account_name_extern}.')

    with GraknClient(uri=f"{GRAKN_SERVER}:48555") as client:
        # client.keyspaces().delete(keyspace=account.account_name)
        with client.session(keyspace=account.account_name) as session:
            load_campaign_data(session, campaign_types, include_paused)
            load_adgroup_data(
                session, adgroup_types=['SHOPPING_PRODUCT'], limit=2)

            with session.transaction().write() as tx:
                it = tx.query('match $x isa adgroup-id; get;')
                adgroup_ids = [ans.value() for ans in it.collect_concepts()]
                tx.commit()

            load_product_partition_data(session, adgroup_ids)
            load_product_data(session, adgroup_ids)


if __name__ == '__main__':
    adspert_app.init('scripts', 'development')
    configure_db()

    account = get_account('406367')
    dbs.account.setup(account)
    import_account_structure(account, ['SHOPPING'], include_paused=False)
