from django.http import HttpResponseForbidden, \
        HttpResponseBadRequest, HttpResponseNotFound
from django.utils.translation import ugettext as _

from tojson import render_to_json
from pybab.models import CatalogLayer, LayerGroup

from .commons import login_required_json_default, get_subtree_for
from ..models import UserLayerLink
from ..forms import ShapeForm
from ..layer_settings import MAX_LAYER_UPLOADS

@login_required_json_default
@render_to_json()
def catalog_layer(request, index):
    user = request.user

    if request.method == 'GET':
       return get_subtree_for(user, int(index), LayerGroup, CatalogLayer)
    elif request.method == 'POST':
        return _upload_layer(request, user, index)
    elif request.method == 'DELETE':
        return _delete_layer(user, index)
    else:
        error_msg = u"request type \"{req_type}\"is not supported".format(
                req_type=request.method)
        return {'success' : False,
                'message' : _(error_msg)}, {'cls':HttpResponseForbidden}

def _upload_layer(request, user, index):
    if user.userlayer_set.count() > MAX_LAYER_UPLOADS:
        error_msg = u"too many layers uploaded. max number is {}".format(
                MAX_LAYER_UPLOADS)
        return {'success':False,
                'message':_(error_msg)}, {'cls':HttpResponseForbidden}
    shape_form = ShapeForm(request.POST, request.FILES, user=user)
    if shape_form.is_valid():
        shape_form.save()
        return {'success':True}
    else:
        return {'success':False,
                'message': shape_form.errors}, {'cls':HttpResponseBadRequest}


def _delete_layer(user, index):
    try:
        catalog_layer = CatalogLayer.objects.get(pk=index)
    except CatalogLayer.DoesNotExist:
        error_msg = u"layer with id '{}' does not exist".format(index)
        return {'success':False,
                'message': _(error_msg)}, {'cls':HttpResponseNotFound}

    if catalog_layer.related_user_set.exists():
        error_msg = u"layer with id '{}' is public, you can not delete it."
        return {'success':False,
                'message': _(error_msg)}, {'cls':HttpResponseForbidden}
    else:
        try:
            catalog_layer.related_user_set.get(user=user)
        #TODO: change with catalog_layer.related_user_set.DoesNotExist 
        except UserLayerLink.DoesNotExist:
            error_msg = u"layer with id '{}' does not belong to the current user."
            return {'success':False,
                    'message': _(error_msg)}, {'cls':HttpResponseForbidden}
        #This will also delete UserLayerLink as a result of the CASCADE trigger.
        catalog_layer.delete()
        return {'success':True}
