from django.http import HttpResponseBadRequest, HttpResponseForbidden
from django.http import HttpResponseNotFound
from django.shortcuts import render
from django.views.decorators.http import require_POST
from django.db import models
from django.utils.translation import ugettext as _
from shp_uploader import shp_uploader_settings
from pybab.models import CatalogLayer
from forms import ShapeForm, UserStyleForm
from shp_uploader.models import UserLayer, UserStyle
from tojson import render_to_json, login_required_json

@login_required_json({'success': False,
                      'msg' :  _(u'Logging in is required')})
@render_to_json()
@require_POST
def upload_shp(request):
    """Returns a json with the result of the request,
    if it failed the error is reported"""
    user = request.user
    if len(user.userlayer_set.all())>shp_uploader_settings.MAX_LAYER_UPLOADS:
        return {'success': False,
                'errors': _(u"You have too many layers uploaded, \
                              delete some of them.")
                },{'cls': HttpResponseForbidden}
    form = ShapeForm(
        user,
        request.POST,
        request.FILES)
    if form.is_valid():
        userStyle = form.cleaned_data["style"]
        catalogLayer = form.save()
        userLayer = UserLayer()

        userLayer.style = userStyle
        userLayer.layer = catalogLayer
        userLayer.user = user
        userLayer.save()

        return {'success': True}
    else:
        return {'success': False,
                'errors': form.errors}, {'cls': HttpResponseBadRequest}

@login_required_json({'success': False,
                      'msg' :  _(u'Logging in is required')})
@render_to_json()
def delete_shp(request, pk):
    try:
        layer = UserLayer.objects.get(pk=pk).layer
    except UserLayer.DoesNotExist:
        return ({'success': False,
                 'message': 'Layer {} does not exist'.format(pk)},
                {'cls': HttpResponseNotFound})
    #notes that this will delete also the user layer as a consequence of the
    #CASCADE trigger
    layer.delete()
    return {'success': True}

@login_required_json({'success': False,
                      'msg' :  _(u'Logging in is required')})
@render_to_json()
def list_shps(request):
    """Returns a json where layers is the list of the user layers"""
    user = request.user
    layers = [layer.as_dict() for layer in user.userlayer_set.all()]
    return {'success': True,
            'layers' : layers}

@login_required_json({'success': False,
                      'msg' :  _(u'Logging in is required')})
@render_to_json()
@require_POST
def upload_style(request):
    """Returns a json with the result of the request,
    if it failed the error is reported"""
    user = request.user
    if len(user.userstyle_set.all())>shp_uploader_settings.MAX_STYLE_UPLOADS:
        return {'success': False,
                'errors': _(u"You have too many styles uploaded, \
                              delete some of them.")
                }, {'cls': HttpResponseForbidden}
    form = UserStyleForm(request.POST, instance=UserStyle(user=request.user))
    if form.is_valid():
        form.save()
        return {'success': True}
    else:
        return {'success': False,
                'errors': form.errors}, {'cls': HttpResponseBadRequest}

@login_required_json({'success': False,
                      'msg' :  _(u'Logging in is required')})
@render_to_json()
def delete_style(request, pk):
    try:
        style = UserStyle.objects.get(pk=pk)
    except UserStyle.DoesNotExist:
        return ({'success': False,
                 'message': 'Style {} does not exist'.format(pk)},
                {'cls': HttpResponseNotFound})
    try:
        style.delete()
    except models.ProtectedError, e:
        msg = ("Cannot delete the style '{}' because "
               "it is associate to the following layer: ").format(style.label)
        msg += " ".join(["'"+s.layer.name+"'" for s in style.userlayer_set.all()])
        return ({'success': False,
                 'message': msg},
                {'cls': HttpResponseBadRequest})
    return {'success': True}

@login_required_json({'success': False,
                      'msg' :  _(u'Logging in is required')})
@render_to_json()
def list_styles(request):
    """Returns a json where styles is the list of the user styles"""
    user = request.user
    styles = [style.as_dict() for style in user.userstyle_set.all()]
    #add default styles (with user=None)
    styles += [style.as_dict() for style in
               UserStyle.objects.filter(user__isnull = True)]
    return {'success': True,
            'styles' : styles}

def display(request):
    '''Displays a form for 'upload'. Only active if settings.DEBUG is true'''
    return render(request,
                  "shp_uploader/upload.html",
                  {'shape_form': ShapeForm(), 'user_form': UserStyleForm()})

