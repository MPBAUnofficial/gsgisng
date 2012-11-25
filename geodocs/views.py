from django.views.decorators.http import require_POST
from tojson import render_to_json, login_required_json
from .forms import *
from django.forms.formsets import formset_factory
from django.http import \
    HttpResponse, HttpResponseBadRequest, \
    HttpResponseNotFound, HttpResponseForbidden
from django.views.decorators.csrf import csrf_exempt
from django.db import transaction, IntegrityError
from django.utils.translation import ugettext as _
from django.conf import settings

from geodocs_settings import GEODOCS_NO_CSRF_PROTECTION


@require_POST
@login_required_json(accept_basic_auth=True)
@render_to_json(mimetype='text/html') # Actually returns JSON: fix for most browsers that expect html as the response for a multipart form, whatever the reason is
@transaction.commit_on_success
def new(request):
    form = PointForm(request.POST)
    if not form.is_valid():
        return {'success': False,
                'error_at': 'point',
                'errors': form.errors}, {'cls': HttpResponseBadRequest}
    else:
        pt = form.save(request.user)
        form = ImageFormSet(request.POST, request.FILES,
                            prefix='images')
        if not form.is_valid():
            return {'success': False,
                    'error_at': 'images',
                    'errors': form.errors
                   }, {'cls': HttpResponseBadRequest}
        form.save(pt)
        form = DocumentFormSet(request.POST, request.FILES,
                               prefix='docs')
        if not form.is_valid():
            return {'success': False,
                    'error_at': 'docs',
                    'errors': form.errors
                   }, {'cls': HttpResponseBadRequest}
        form.save(pt)
        return {'success': True, 'pk': pt.pk}


@login_required_json(accept_basic_auth=True)
@render_to_json()
def getinfo(request, pk):
    try:
        d = {'success': True}
        pt = Point.objects.get(pk=pk)
        d.update({'pk': pk,
                  'data': pt.as_dict()})
        return d
    except Point.DoesNotExist:
        return ({'success': False,
                 'message': _('Point {0} does not exist').format(pk)},
                {'cls': HttpResponseNotFound})


@require_POST
@login_required_json(accept_basic_auth=True)
@render_to_json()
@transaction.commit_on_success
def point_del(request, pk):
    try:
        pt = Point.objects.get(pk=pk)
    except Point.DoesNotExist:
        return ({'success': False,
                 'message': _('Point {0} does not exist').format(pk)},
                {'cls': HttpResponseNotFound})
    else:
        if (request.user.is_staff or request.user == pt.user):
            pt.delete()
            return {'success': True}
        else:
            return {'success': False,
                    'message': _('You are not allowed to delete this object. '
                                 'You are neither the owner, nor a staff '
                                 'member.')}, {'cls': HttpResponseForbidden}


@require_POST
@login_required_json(accept_basic_auth=True)
@render_to_json()
@transaction.commit_on_success
def _item_del(request, cls, get_dict):
    '''Deletes cls item with primary key pk, after doing apporpriate checks
    
    cls should be either Image or Document
    '''
    try:
        item = cls.objects.get(**get_dict)
    except cls.DoesNotExist:
        return ({'success': False,
                 'message': _('There is no such {model_verbose_name}')\
                     .format(model_verbose_name=cls._meta.verbose_name),
                },
                {'cls': HttpResponseNotFound})
    else:
        if (request.user.is_staff or request.user == item.point.user):
            item.delete()
            return {'success': True}
        else:
            return {'success': False,
                    'message': _('You are not allowed to delete this object. '
                                 'You are neither the owner, nor a staff '
                                 'member.')}


def doc_del(request, url):
    doc_url = url.replace(settings.MEDIA_URL, '', 1)
    return _item_del(request, Document, {'doc': doc_url})


def img_del(request, url):
    img_url = url.replace(settings.MEDIA_URL, '', 1)
    return _item_del(request, Image, {'image': img_url})


if GEODOCS_NO_CSRF_PROTECTION:
    new = csrf_exempt(new)
    point_del = csrf_exempt(point_del)
    doc_del = csrf_exempt(doc_del)
    img_del = csrf_exempt(img_del)


@render_to_json()
@login_required_json(accept_basic_auth=True)
def my_points(request):
    d = {'success': True}
    d['list'] = [pt.as_dict() for pt in request.user.point_set.all()]
    return d
    

@csrf_exempt
@require_POST
@render_to_json()
@login_required_json(accept_default_auth=False, accept_basic_auth=True)
@transaction.commit_on_success
def new_single(request):
    form = PointForm(request.POST)
    if not form.is_valid():
        return {'success': False,
                'errors': form.errors}, {'cls': HttpResponseBadRequest}
    else:
        pt = form.save(request.user)
        return {'success': True,
                'pk': pt.pk}


@csrf_exempt
@require_POST
@render_to_json()
@login_required_json(accept_default_auth=False, accept_basic_auth=True)
@transaction.commit_on_success
def new_image(request, point_pk):
    try:
        pt = Point.objects.get(pk=point_pk)
    except Point.DoesNotExist:
        return ({'success': False,
                 'message': _('Point {0} does not exist').format(pk)},
                {'cls': HttpResponseNotFound})
    else:
        if request.user != pt.user:
            return ({'success': False,
                     'message': _('Forbidden: you are not this point\'s owner')},
                    {'cls': HttpResponseForbidden})
        form = ImageForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                form.save(pt)
            except IntegrityError:
                return ({'success': False,
                         'message': _('Uploaded image already exists')},
                        {'cls': HttpResponseBadRequest})
            else:
                return {'success': True}
        else:
            return {'success': False,
                    'errors': form.errors}, {'cls': HttpResponseBadRequest}


#@csrf_exempt
#@require_POST
#@render_to_json()
#@login_required_json(accept_default_auth=False, accept_basic_auth=True)
#@transaction.commit_on_success
#def new_doc(request, point_pk):
#    return ({'success': False,
#             'message': 'Only photos are allowed to be uploaded from mobile'},
#            {'status_code': 501})


@login_required_json(accept_basic_auth=True)
def display(request):
    '''Displays testing forms. Only active if settings.DEBUG is true'''
    return HttpResponse("""
You are <b>%s</b> <br/><br/> 
""" % (request.user.username if request.user.is_authenticated() else "NOBODY") + u"""
<form enctype="multipart/form-data" method="post" action="/new/">
%s
%s
%s
<input type="submit" />
</form>
""" % (unicode(PointForm()),
       unicode(ImageFormSet(prefix='images')),
       unicode(DocumentFormSet(prefix='docs')),
       ) + u"""

<hr/>
<form enctype="multipart/form-data" method="post" action="/new-point/">
%s
<input type="submit" />
</form>
<hr/>

<form enctype="multipart/form-data" method="post" action="/new-image/%d/">
%s
<input type="submit" />
</form>

<hr/>
<form enctype="multipart/form-data" method="post" action="/new-doc/%d/">
%s
<input type="submit" />
</form>

""" % (unicode(PointForm()),
       int(request.GET['pt'] if 'pt' in request.GET else '-1'),
       unicode(ImageForm()),
       int(request.GET['pt'] if 'pt' in request.GET else '-1'),
       unicode(DocumentForm()),
       ) + u"""

<form enctype="multipart/form-data" method="post" action="/delete/%d/">
<input type="submit" value="Delete point" />
</form>
<form enctype="multipart/form-data" method="post" action="/delete-image/%d/">
<input type="submit" value="Delete image %d" />
</form>
<form enctype="multipart/form-data" method="post" action="/delete-doc/%d/">
<input type="submit" value="Delete doc %d" />
</form>
""" % (int(request.GET['pt'] if 'pt' in request.GET else '-1'),
       int(request.GET['img'] if 'img' in request.GET else '-1'),
       int(request.GET['img'] if 'img' in request.GET else '-1'),
       int(request.GET['doc'] if 'doc' in request.GET else '-1'),
       int(request.GET['doc'] if 'doc' in request.GET else '-1'),)

                        )
