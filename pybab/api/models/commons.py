def get_system_catalogs( catalog_class ):
    return catalog_class.objects.filter(related_user_set__isnull=True)

def get_user_catalogs( user, catalog_class ):
    return catalog_class.objects.filter(related_user_set__user__pk=user.pk)
