from django.http import HttpResponseBadRequest
from django.utils.translation import ugettext as _
from tojson import render_to_json
from pybab.models import Catalog
from .commons import login_required_json_default

@login_required_json_default
@render_to_json()
def metadata(request, index):
    try:
        catalog = Catalog.objects.get(pk=index)
    except Catalog.DoesNotExist:
        error_msg = u"catalog with id '{0}' does not exist".format(
                index)
        return {'success':False,
                'message':_(error_msg)}, {'cls':HttpResponseBadRequest}
   
    if not catalog.has_metadata:
        error_msg = u"catalog with id '{0}' does not have metadata".format(
                index)
        return {'success':False,
                'message':_(error_msg)}, {'cls':HttpResponseBadRequest}
    else:
        return {'success':True,
                'data':catalog.metadata_set.get().to_dict()}
