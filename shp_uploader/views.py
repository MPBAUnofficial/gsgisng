from django.http import HttpResponseRedirect, HttpResponseBadRequest
from django.http import HttpResponseRedirect, HttpResponseForbidden
from django.shortcuts import render
from django.views.decorators.http import require_POST
from django.conf import settings
from django.db import connection, transaction, utils
from django.utils.translation import ugettext as _
from shp_uploader import shp_uploader_settings
from forms import ShapeForm, UserStyleForm
from shp_uploader.models import UserLayer, UserStyle
import shutil, tempfile
import zipfile
import urllib2
import os, time
from tojson import render_to_json, login_required_json
#internal libraries
import create_ws_ds
from pg2geoserver import Pg2Geoserver
import ogr2ogr

def _unzip_save(zip_file, layer):
    """Unzip the file given to a temporary directory: the path is returned"""
    zip = zipfile.ZipFile(zip_file)
    dir = tempfile.mkdtemp()
    #extract the 4 shape files to dir
    for member in zip.namelist():
        if member.lower().endswith((".shp",".dbf",".prj",".shx")):
            _, extension = os.path.splitext(member)
            path = os.path.join(dir, layer+extension)
            source = zip.open(member)
            target = file(path, "wb")
            shutil.copyfileobj(source, target)
            source.close()
            target.close()
    zip.close()
    return dir

def _upload2pg(dir, epsg_code):
    """Tries to upload the shapefile to postgres. If something went wrong
    it returns the problem, returns True otherwise"""
    db_conf = settings.DATABASES['default']
    schema = shp_uploader_settings.SCHEMA_USER_UPLOADS
    #maybe better to use a system with ogr2ogr?
    args = ['ogr2ogr.py',
        '-f', 'PostgreSQL',
        'PG:host={} user={} dbname={} password={} active_schema={}\
        '.format(db_conf['HOST'],db_conf['USER'],db_conf['NAME'],
                 db_conf['PASSWORD'],schema),
        '-a_srs', 'EPSG:'+str(epsg_code),
        '-lco', 'PRECISION=NO',
        dir]
    try:
        return ogr2ogr.main(args)
    except Exception, e:
        #the module ogr2ogr doesn't specify witch exception could be
        #raised, try the generic one
        return e.message

def _toGeoserver(layer_name):
    """Tries to index the shapefile in geoserver. If something went wrong
    it returns the problem, returns True otherwise"""
    geoserver_url = shp_uploader_settings.GEOSERVER_URL
    username = shp_uploader_settings.GEOSERVER_USER
    password = shp_uploader_settings.GEOSERVER_PASSWORD
    p2g = Pg2Geoserver(geoserver_url,username,password)
    workspace = shp_uploader_settings.WORKSPACE_USER_UPLOADS
    datastore = shp_uploader_settings.DATASTORE_USER_UPLOADS
    try:
        p2g.create_layer(workspace=workspace,
                         datastore=datastore,
                         name=layer_name)
    except urllib2.HTTPError, e:
        #maybe the workspace or the datastore were deleted: tries to create them
        #and index the layer again
        try:
            create_ws_ds.create_ws_ds()
        except create_ws_ds.WorkspaceCreationFailed as e:
            return "Failed to create workspace: "+str(e)
        except create_ws_ds.DatastoreCreationFailed as e:
            return "Failed to create datastore: "+str(e)
        else:
            try:
                p2g.create_layer(workspace=workspace,
                                 datastore=datastore,
                                 name=layer_name)
            except urllib2.HTTPError, e:
                return "Failed to index the layer: "+e.read()
    except urllib2.URLError, e:
        return e.reason
    return True

def _delete_layer_postgis(schema,layer_name):
    """Remove layer from postgis"""
    cursor = connection.cursor()
    query = "DROP TABLE {}.{};".format(schema,layer_name)
    with transaction.commit_on_success():
        try:
            cursor.execute(query)
        except django.db.utils.DatabaseError, e:
            #if the layer could not be elimitade do nothing
            print e
    return

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
    form = ShapeForm(request.POST, request.FILES)
    if form.is_valid():
        layer_label = form.cleaned_data['layer_name']
        layer_id = layer_label + str(user.id) + str(int(time.time()))
        #unzip the file
        dir = _unzip_save(request.FILES['shape_zip'],
                          layer_id)
        #store the shape in postgis
        res = _upload2pg(dir, form.cleaned_data['epsg_code'])
        if not res==True:
            msg = "Failed to store the layer in postgis."
            msg += "Check the EPSG code {} and if the shape is valid.".format(
                form.cleaned_data['epsg_code'])
            return {'success': False,
                    'errors': [msg]}, {'cls': HttpResponseBadRequest}
        else:
            #delete directory with the shape
            shutil.rmtree(dir)
            #index on geoserver
            res = _toGeoserver(layer_id)
            if res==True:
                ul = UserLayer(
                    user = user,
                    layer_name = layer_id,
                    style = form.cleaned_data['style'],
                    label = layer_label,
                    schema = shp_uploader_settings.SCHEMA_USER_UPLOADS,
                    workspace = shp_uploader_settings.WORKSPACE_USER_UPLOADS,
                    datastore = shp_uploader_settings.DATASTORE_USER_UPLOADS)
                ul.save()
                return {'success': True}
            else:
                _delete_layer_postgis(shp_uploader_settings.SCHEMA_USER_UPLOADS, layer_id)
                msg = "Failed to index the layer on geoserver."
                msg += "The reason was: "+str(res)
                return {'success': False,
                        'errors': [msg]}, {'cls': HttpResponseBadRequest}
    else:
        return {'success': False,
                'errors': form.errors}, {'cls': HttpResponseBadRequest}

def _remove_layer_geoserver(layer):
    #remove layer from geoserver
    geoserver_url = shp_uploader_settings.GEOSERVER_URL
    username = shp_uploader_settings.GEOSERVER_USER
    password = shp_uploader_settings.GEOSERVER_PASSWORD
    p2g = Pg2Geoserver(geoserver_url,username,password)
    try:
        p2g.delete_layer(layer_name=layer.layer_name)
    except (urllib2.HTTPError, urllib2.URLError), e:
        #if there were problems do nothing:
        #go on with the elminiation of the layer
        print e

@login_required_json({'success': False,
                      'msg' :  _(u'Logging in is required')})
@render_to_json()
def delete_shp(request, pk):
    try:
        layer = UserLayer.objects.get(pk=pk)
    except UserLayer.DoesNotExist:
        return ({'success': False,
                 'message': 'Layer {} does not exist'.format(pk)},
                {'cls': HttpResponseNotFound})
    _remove_layer_geoserver(layer)
    _delete_layer_postgis(layer.schema, layer.layer_name)
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

def display(request):
    '''Displays a form for 'upload'. Only active if settings.DEBUG is true'''
    return render(request,
                  "shp_uploader/upload.html",
                  {'shape_form': ShapeForm(), 'user_form': UserStyleForm()})

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

def _remove_style_geoserver(style):
    #remove style from geoserver
    geoserver_url = shp_uploader_settings.GEOSERVER_URL
    username = shp_uploader_settings.GEOSERVER_USER
    password = shp_uploader_settings.GEOSERVER_PASSWORD
    p2g = Pg2Geoserver(geoserver_url,username,password)
    try:
        p2g.delete_style(style_name=style.name)
    except (urllib2.HTTPError, urllib2.URLError), e:
        #if there were problems do nothing:
        #go on with the elminiation of the style
        print e

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
    _remove_style_geoserver(style)
    style.delete()
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
