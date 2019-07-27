import treelib
from treelib import Node, Tree

from models.shopping_campaign_node import ShoppingCampaignNode


class ShoppingCampaign(Tree):
    
    def __init__(self):
        super(ShoppingCampaign, self).__init__()
        self.create_root_node()

    def create_node(self, data):
        
        try:
            node = ShoppingCampaignNode(data['id'], data['name'])
            node.factory(data)
        except KeyError:
            print "Node not created, malformed data provided"

        try:
            super(ShoppingCampaign, self).add_node(node, parent=data.get('parent', 0))
        except Exception:
            print data
            raise

    def create_root_node(self):
        super(ShoppingCampaign, self).create_node('Animals', 1)

    def get_ancestors(self, node, include_root=False):
        root = 1
        ancestors = []
        while node.identifier != root:
            if node.identifier == 1:
                ancestors.append(1)
                return ancestors
            else:
                print node
                node = self.get_node(node.parent)
                if not include_root and node.identifier == 1:
                    continue
                ancestors.append(node.identifier)

        return ancestors

    def get_category_level(self, node_id):
        """ Return at what category level the given `node` is at.
            (type, subtype or sub-subtype etc) """
        node = self.get_node(node_id)
        ancestors = self.get_ancestors(node, False)
        print ancestors
        level = len([n for n in ancestors if self.get_node(n).node_type ==
            ShoppingCampaignNode.NodeType.CATEGORY])

        return level

    def split_leaf(self, node_id):
        node = self.get_node(node_id)
        if node.is_segment:
            # cannot split on a segment
            return None
        
        # make a bunch of



