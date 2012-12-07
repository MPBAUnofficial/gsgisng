from django.http import HttpResponseBadRequest

from tojson import render_to_json

from pybab.models import CatalogIndicator, IndicatorGroup

from .commons import login_required_json_default, get_subtree_for
from ..forms import UserIndicatorLinkForm


@login_required_json_default
@render_to_json()
def catalog_indicator(request, index):
    user = request.user
    if request.method == 'GET':
        return get_subtree_for(user, int(index), IndicatorGroup, CatalogIndicator)
    elif request.method == 'POST':
        indicator_form = UserIndicatorLinkForm(request.POST)
    
        if indicator_form.is_valid():
            indicator_form.save()
            return {'success': True}
        else: 
            return {'success': False,
                    'message': indicator_form.errors }, { 'cls': HttpResponseBadRequest}   


