def get_system_catalogs(catalog_class, group_index):
    return catalog_class.objects.filter(related_user_set__isnull=True).filter(group=group_index)

def get_user_catalogs(user, catalog_class, group_index):
    return catalog_class.objects.filter(related_user_set__user=user).filter(group=group_index)
