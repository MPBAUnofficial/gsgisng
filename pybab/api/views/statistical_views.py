from pybab.models import CatalogStatistical, StatisticalGroup
from tojson import render_to_json
from .commons import login_required_json_default, get_subtree_for

from pybab.api.forms import UserStatisticalLinkForm
from django.http import HttpResponseBadRequest

@login_required_json_default
@render_to_json()
def catalog_statistical(request, index):
    user = request.user
    if request.method == 'GET':
        return get_subtree_for(user, int(index), StatisticalGroup, CatalogStatistical)
    elif request.method == 'POST':

        statistical_form = UserStatisticalLinkForm(request.POST)

        if statistical_form.is_valid():
            statistical_form.save()
            return {'success': True}
        else:
            return {'success': False,
                    'message': statistical_form.errors }, { 'cls': HttpResponseBadRequest}   
                     

