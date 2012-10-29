from django.views.decorators.http import require_POST
from tojson import render_to_json
from .forms import *
from django.forms.formsets import formset_factory
from django.http import \
    HttpResponse, HttpResponseBadRequest, \
    HttpResponseNotFound
from django.views.decorators.csrf import csrf_exempt
from django.db import transaction
from geodocs_settings import GEODOCS_NO_CSRF_PROTECTION

@render_to_json()
@require_POST
@transaction.commit_on_success
def new(request):
    form = PointForm(request.POST)
    if not form.is_valid():
        return {'success': False,
                'error_at': 'point',
                'errors': form.errors}, {'cls': HttpResponseBadRequest}
    else:
        pt = form.save()
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
                 'message': 'Point {0} does not exist'.format(pk)},
                {'cls': HttpResponseNotFound})


@require_POST
@render_to_json()
@transaction.commit_on_success
def point_del(request, pk):
    try:
        pt = Point.objects.get(pk=pk)
        pt.delete()
        return {'success': True}
    except Point.DoesNotExist:
        return ({'success': False,
                 'message': 'Point {0} does not exist'.format(pk)},
                {'cls': HttpResponseNotFound})
    

if GEODOCS_NO_CSRF_PROTECTION:
    new = csrf_exempt(new)
    point_del = csrf_exempt(point_del)

def display(request):
    '''Displays a form for 'new/'. Only active if settings.DEBUG is true'''
    return HttpResponse(u"""
<form enctype="multipart/form-data" method="post" action="/new/">
%s
%s
%s
<input type="submit" />
</form>
""" % (unicode(PointForm()),
       unicode(ImageFormSet(prefix='images')),
       unicode(DocumentFormSet(prefix='docs')),)
                        )
