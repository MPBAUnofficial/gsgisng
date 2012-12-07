__all__ = ['catalog_layer',
           #'delete_style', 'list_styles',
           'catalog_indicator',
           'catalog_statistical',
           'metadata']

#from .layer_views import list_styles, delete_style
from .new_layer_views import catalog_layer
from .indicator_views import catalog_indicator 
from .statistical_views import catalog_statistical
from .metadata_views import metadata
