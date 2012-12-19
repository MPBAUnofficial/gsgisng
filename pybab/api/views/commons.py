from django.http import HttpResponseNotFound
from django.utils.translation import ugettext as _

from pybab.commons import dict_join
from tojson import login_required_json

from ..models import get_system_catalogs, get_user_catalogs

def _to_dict(model_instance, *args):
    result = model_instance.to_dict()
    for arg in args:
        if callable(arg):
            result.update(arg(model_instance))
        else:
            result.update(arg)
    return result

def get_subtree_for(user, group_index, group_class, catalog_class, extra_data=None):
    """
    Given a user and a tree index, it return all the json to send to the client.
    """
    try:
        root = group_class.objects.get(pk=group_index)
    except group_class.DoesNotExist:
        return {'success':'false',
                'message':'{0} is not a valid index for {1}'.format(group_index, group_class.__name__)},\
               {'cls': HttpResponseNotFound}

    folders = [dict_join(f.to_dict(), {'leaf':False}) for f in root.children]

    public_catalogs = [_to_dict(cat, {'leaf':True, 'public':True}, *extra_data)
            for cat in get_system_catalogs(catalog_class, group_index)]

    private_catalogs = [_to_dict(cat, {'leaf':True,'public':False}, *extra_data)
            for cat in get_user_catalogs(user, catalog_class, group_index)]

    return {'success':'true',
            'requested':root.to_dict(),
            'data':list(folders) + list(public_catalogs) + list(private_catalogs)}

login_required_json_default = login_required_json({'success': False, 'message':_("Logging in is required for this action")})

