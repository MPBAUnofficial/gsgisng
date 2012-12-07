from django.http import HttpResponseBadRequest, HttpResponseForbidden
from django.utils.translation import ugettext as _

from tojson import render_to_json
from pybab.models import CatalogStatistical, StatisticalGroup

from .commons import login_required_json_default, get_subtree_for
from ..forms import UserStatisticalLinkForm

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
    else:
        error_msg = u"request type \"{req_type}\"is not supported".format(
                req_type=request.method)
        return {'success' : False,
                'message' : _(error_msg)}, {'cls':HttpResponseForbidden} 

                     

