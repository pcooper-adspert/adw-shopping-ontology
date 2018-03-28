import shopping_campaign

from models.shopping_campaign_node import ShoppingCampaignNode


if __name__ == '__main__':

    sc = shopping_campaign.ShoppingCampaign()
    
    data_list = []

    data_list.append({
        'id': 2,
        'name': 'Cat',
        'parent': 1,
        'node_type': ShoppingCampaignNode.NodeType.BRAND
    })

    data_list.append({
        'id': 3,
        'name': 'Dog',
        'parent': 1,
        'node_type': ShoppingCampaignNode.NodeType.BRAND
    })

    data_list.append({
        'id': 4,
        'name': 'Lion',
        'parent': 2,
        'node_type': ShoppingCampaignNode.NodeType.PRODUCT
    })
    data_list.append({
        'id': 5,
        'name': 'Fast',
        'parent': 2,
        'node_type': ShoppingCampaignNode.NodeType.CATEGORY
    })
    data_list.append({
        'id': 6,
        'name': 'Cheetah',
        'parent': 5,
        'node_type': ShoppingCampaignNode.NodeType.PRODUCT
    })
    data_list.append({
        'id': 7,
        'name': 'Wolf',
        'parent': 3,
        'node_type': ShoppingCampaignNode.NodeType.PRODUCT
    })
    data_list.append({
        'id': 8,
        'name': 'Male',
        'parent': 6,
        'node_type': ShoppingCampaignNode.NodeType.GENDER
    })
    data_list.append({
        'id': 9,
        'name': 'Female',
        'parent': 6,
        'node_type': ShoppingCampaignNode.NodeType.GENDER
    })

    [sc.create_node(d) for d in data_list]
    sc.show(line_type="ascii-em")

    print sc.get_category_level(9)
    print sc.get_category_level(7)
    print sc.get_category_level(8)


