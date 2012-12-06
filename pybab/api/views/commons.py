from django.http import HttpResponseNotFound
from django.utils.translation import ugettext as _

from tojson import login_required_json

from ..models import get_system_catalogs, get_user_catalogs

def _add_to_dicts( dict_list, key, value ):
    new_dict_list = [d.copy() for d in dict_list]
    for d in new_dict_list:
        d[key]=value

    return new_dict_list 

def get_subtree_for(user, group_index, group_class, catalog_class):
    """
    Given a user and a tree index, it return all the json to send to the client.
    """
    try:
        root = group_class.objects.get(pk=group_index)
    except group_class.DoesNotExist:
        return {'success':'false',
                'message':'{} is not a valid index for {}'.format(group_index, group_class.__name__)},\
               {'cls': HttpResponseNotFound}

    folders = [f.to_dict() for f in root.children]
    public_catalogs = _add_to_dicts(
            [cat.to_dict() for cat in get_system_catalogs(catalog_class, (group_index + 1))], 'public', True)
    private_catalogs = _add_to_dicts(
            [cat.to_dict() for cat in get_user_catalogs(user, catalog_class, (group_index + 1))], 'public', False)

    return {'success':'true',
            'requested':root.to_dict(),
            'data':list(folders) + list(public_catalogs) + list(private_catalogs)}

login_required_json_default = login_required_json({'success': False, 'message':_("Logging in is required for this action")})

