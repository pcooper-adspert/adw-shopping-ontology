from enum import Enum
from treelib import Node, Tree

SPLIT_THRESHOLD = 500


class ShoppingCampaignNode(Node):

    class NodeType(str, Enum):
        CATEGORY = 'category'
        BRAND = 'brand'
        COLOR = 'color'
        SIZE = 'size'
        PRODUCT = 'product'
        GENDER = 'gender'

    node_type = NodeType.PRODUCT
    clicks = 0

    def __init__(self, id, name):
        super(ShoppingCampaignNode, self).__init__(name, id)

    def factory(self, payload):
        for k, v in payload.iteritems():
            setattr(self, k, v)
