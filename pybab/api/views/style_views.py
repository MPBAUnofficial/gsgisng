from functools import partial
from django.db import models
from django.http import HttpResponseForbidden, \
        HttpResponseBadRequest, HttpResponseNotFound
from django.utils.translation import ugettext as _

from tojson import render_to_json
from pybab.commons import dict_join

from .commons import login_required_json_default
from ..layer_settings import MAX_STYLE_UPLOADS
from ..models import UserStyle

from ..forms import UserStyleForm

add_to_dicts = lambda l, d:list(map(partial(dict_join, d), l))

@login_required_json_default
@render_to_json()
def styles(request, index=0):
    user = request.user

    if request.method == 'GET':
        return _list_styles(user)
    elif request.method == 'POST':
        return _upload_style(request, user)
    elif request.method == 'DELETE':
        return _delete_style(index)
    else:
        error_msg = u"request type \"{req_type}\"is not supported".format(
                req_type=request.method)
        return {'success' : False,
                'message' : _(error_msg)}, {'cls':HttpResponseForbidden}

def _list_styles(user):
    """Returns a json where styles is the list of the user styles"""
    user_styles = add_to_dicts(
            [style.to_dict() for style in user.userstyle_set.all()],
            {'public':False})

    public_styles = add_to_dicts(
            [style.to_dict() for style in UserStyle.objects.filter(user__isnull=True)],
            {'public': True})

    return {'success':True,
            'data':user_styles + public_styles}

def _upload_style(request, user):
    """Returns a json with the result of the request,
    if it failed the error is reported"""
    if user.userstyle_set.count() > MAX_STYLE_UPLOADS:
        return {'success': False,
                'errors': _(u"You have too many styles uploaded, \
                              delete some of them.")
                }, {'cls': HttpResponseForbidden}
    form = UserStyleForm(request.POST, user=user)
    if form.is_valid():
        form.save()
        return {'success': True}
    else:
        return {'success': False,
                'errors': form.errors}, {'cls': HttpResponseBadRequest}

def _delete_style(pk):
    try:
        style = UserStyle.objects.get(pk=pk)
    except UserStyle.DoesNotExist:
        return ({'success': False,
                 'message': 'Style {} does not exist'.format(pk)},
                {'cls': HttpResponseNotFound})
    try:
        style.delete()
    except models.ProtectedError as e:
        msg = ("Cannot delete the style '{}' because "
               "it is associate to the following layer: ").format(style.label)
        msg += " ".join(["'"+s.layer.name+"'" for s in style.userlayerlink_set.all()])
        return ({'success': False,
                 'message': msg},
                {'cls': HttpResponseBadRequest})
    return {'success': True}




