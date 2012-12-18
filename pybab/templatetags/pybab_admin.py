import django
from django.conf import settings
from django.contrib.admin.util import lookup_field, display_for_field
from django.contrib.admin.views.main import EMPTY_CHANGELIST_VALUE
from django.core.exceptions import ObjectDoesNotExist
from django.db import models
from django.utils.html import escape, conditional_escape
from django.utils.safestring import mark_safe
from django.utils.encoding import smart_unicode, force_unicode
from django.template import Library

from django.contrib.admin.templatetags.admin_list import _boolean_icon, result_headers


if django.VERSION >= (1, 2, 3):
    from django.contrib.admin.templatetags.admin_list import result_hidden_fields
else:
    result_hidden_fields = lambda cl: []


register = Library()


PYBAB_ADMIN_LEVEL_INDENT = getattr(settings, 'PYBAB_ADMIN_LEVEL_INDENT', 15)


###
# Ripped from contrib.admin's (1.3.1) items_for_result tag.
# The only difference is we're indenting nodes according to their level.
def pybab_items_for_result(cl, result, form):
    """
    Generates the actual list of data.
    """
    first = True
    pk = cl.lookup_opts.pk.attname

    ##### PYBAB ADDITION START
    # figure out which field to indent
    pybab_indent_field = getattr(cl.model_admin, 'pybab_indent_field', None)
    if not pybab_indent_field:
        for field_name in cl.list_display:
            try:
                f = cl.lookup_opts.get_field(field_name)
            except models.FieldDoesNotExist:
                if pybab_indent_field is None:
                    attr = getattr(result, field_name, None)
                    if callable(attr):
                        # first callable field, use this if we can't find any model fields
                        pybab_indent_field = field_name
            else:
                # first model field, use this one
                pybab_indent_field = field_name
                break
    ##### PYBAB ADDITION END

    for field_name in cl.list_display:
        row_class = ''
        try:
            f, attr, value = lookup_field(field_name, result, cl.model_admin)
        except (AttributeError, ObjectDoesNotExist):
            result_repr = EMPTY_CHANGELIST_VALUE
        else:
            if f is None:
                if field_name == u'action_checkbox':
                    row_class = ' class="action-checkbox"'
                allow_tags = getattr(attr, 'allow_tags', False)
                boolean = getattr(attr, 'boolean', False)
                if boolean:
                    allow_tags = True
                    result_repr = _boolean_icon(value)
                else:
                    result_repr = smart_unicode(value)
                # Strip HTML tags in the resulting text, except if the
                # function has an "allow_tags" attribute set to True.
                if not allow_tags:
                    result_repr = escape(result_repr)
                else:
                    result_repr = mark_safe(result_repr)
            else:
                if isinstance(f.rel, models.ManyToOneRel):
                    field_val = getattr(result, f.name)
                    if field_val is None:
                        result_repr = EMPTY_CHANGELIST_VALUE
                    else:
                        result_repr = escape(field_val)
                else:
                    result_repr = display_for_field(value, f)
                if isinstance(f, models.DateField)\
                or isinstance(f, models.TimeField)\
                or isinstance(f, models.ForeignKey):
                    row_class = ' class="nowrap"'
        if force_unicode(result_repr) == '':
            result_repr = mark_safe('&nbsp;')

        ##### PYBAB ADDITION START
        if field_name == pybab_indent_field:
            level = result.level
            padding_attr = ' style="padding-left:%spx"' % (5 + PYBAB_ADMIN_LEVEL_INDENT * level)
        else:
            padding_attr = ''
        ##### PYBAB ADDITION END

        # If list_display_links not defined, add the link tag to the first field
        if (first and not cl.list_display_links) or field_name in cl.list_display_links:
            table_tag = {True: 'th', False: 'td'}[first]
            first = False
            url = cl.url_for_result(result)
            # Convert the pk to something that can be used in Javascript.
            # Problem cases are long ints (23L) and non-ASCII strings.
            if cl.to_field:
                attr = str(cl.to_field)
            else:
                attr = pk
            value = result.serializable_value(attr)
            result_id = repr(force_unicode(value))[1:]

            ##### PYBAB SUBSTITUTION START
            yield mark_safe(u'<%s%s%s><a href="%s"%s>%s</a></%s>' % \
                (table_tag, row_class, padding_attr, url, (cl.is_popup and ' onclick="opener.dismissRelatedLookupPopup(window, %s); return false;"' % result_id or ''), conditional_escape(result_repr), table_tag))
            ##### PYBAB SUBSTITUTION END

        else:
            # By default the fields come from ModelAdmin.list_editable, but if we pull
            # the fields out of the form instead of list_editable custom admins
            # can provide fields on a per request basis
            if (form and field_name in form.fields and not (
                    field_name == cl.model._meta.pk.name and
                        form[cl.model._meta.pk.name].is_hidden)):
                bf = form[field_name]
                result_repr = mark_safe(force_unicode(bf.errors) + force_unicode(bf))
            else:
                result_repr = conditional_escape(result_repr)

            ##### PYBAB SUBSTITUTION START
            yield mark_safe(u'<td%s%s>%s</td>' % (row_class, padding_attr, result_repr))
            ##### PYBAB SUBSTITUTION END

    if form and not form[cl.model._meta.pk.name].is_hidden:
        yield mark_safe(u'<td>%s</td>' % force_unicode(form[cl.model._meta.pk.name]))


def pybab_results(cl):
    if cl.formset:
        for res, form in zip(cl.result_list, cl.formset.forms):
            yield list(pybab_items_for_result(cl, res, form))
    else:
        #NOTE: this call a new defined method ('results'), it is not django specified
        for res in cl.results():
            yield list(pybab_items_for_result(cl, res, None))


def pybab_result_list(cl):
    """
    Displays the headers and data list together
    """
    return {'cl': cl,
            'result_hidden_fields': list(result_hidden_fields(cl)),
            'result_headers': list(result_headers(cl)),
            'results': list(pybab_results(cl))}

# custom template is merely so we can strip out sortable-ness from the column headers
# Based on admin/change_list_results.html (1.3.1)
#pybab_result_list = register.inclusion_tag("admin/pybab/pybab_change_list_results.html")(pybab_result_list)
pybab_result_list = register.inclusion_tag("admin/change_list_results.html")(pybab_result_list)
