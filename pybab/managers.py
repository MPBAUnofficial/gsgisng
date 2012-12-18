from django.db import models

class GroupModelManager(models.Manager):
    def subtree_sorted_indented(self, parent, to_exclude=()):
        """Returns the subtree starting with parent, without nodes in the list
        to exclude. The subtree is returned in order of reppresentation, with
        basic indentation as label"""
        def aux(group,level):
            if group in to_exclude:
                return []
            ret = [(group.id, "---"*level + " " + group.name)]
            for child in group.children:
                    ret += aux(child,level+1)
            return ret
        return aux(parent,0)

    def tree_sorted_levels(self):
        """Returns the tree sorted by visualization order, with information about
        the level of the node"""
        def aux(group,level):
            #ret = [(group, level)]
            group.level = level
            ret = [group]
            for child in group.children:
                    ret += aux(child,level+1)
            return ret
        return aux(self.get(id=self.model.ROOT_ID),0)
