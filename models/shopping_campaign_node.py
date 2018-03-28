from enum import Enum
import treelib

SPLIT_THRESHOLD = 500

class ShoppingCampaignNode(treelib.Node):

    class NodeType(Enum):
        CATEGORY = 'category'
        BRAND = 'brand'
        COLOR = 'color'
        SIZE = 'size'
        PRODUCT = 'product'
        GENDER = 'gender'


    is_segment = False
    node_type = NodeType.PRODUCT
    clicks = 0

    def __init__(self, id, name):
        super(ShoppingCampaignNode, self).__init__(name, id)

    def factory(self, payload):
        for k, v in payload.iteritems():
            setattr(self, k, v)
    