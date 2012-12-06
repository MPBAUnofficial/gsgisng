from pybab.models import CatalogStatistical, StatisticalGroup
from tojson import render_to_json
from .commons import login_required_json_default, get_subtree_for

@login_required_json_default
@render_to_json()
def catalog_statistical(request, tree_index):
    user = request.user
    if request.method == 'GET':
        return get_subtree_for(user, int(tree_index), StatisticalGroup, CatalogStatistical)

