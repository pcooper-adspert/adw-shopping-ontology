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

