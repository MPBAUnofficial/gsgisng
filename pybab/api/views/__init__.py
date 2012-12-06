__all__ = ['upload_layer','delete_layer','upload_layer','delete_style',
           'layer_form', 'list_layers', 'list_styles',
           'catalog_indicator',
           'catalog_statistical']

from .layer_views import upload_layer,delete_layer,upload_style,delete_style,layer_form,list_layers,list_styles
from .indicator_views import catalog_indicator 
from .statistical_views import catalog_statistical
