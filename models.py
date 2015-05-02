from xml.etree import ElementTree
from collections import OrderedDict

from django.contrib.gis.db import models

TYPE_MAPPING = {
    'float': models.FloatField,
    'double': models.FloatField,
    'string': models.CharField,
    'geometry': models.GeometryField,
    'oid': models.IntegerField, # should be 32-bit integer for ObjectID
}

class XML(type):
    '''
    Mixin to create a GeoDjango model from GIS metadata; use like so. ::

        import os

        from django.contrib.gis.db import models

        class Parish(models.Model, metaclass = XML):
            source = os.path.join(os.path.dirname(__name__), 'parishes_USGS_1998.shp.xml')

    Hopefully unnecessary...
    http://davidwilson.me/2013/09/30/Colorado-Geology-GeoDjango-Tutorial/
    '''
    def __new__(cls, name, bases, namespace):
        if 'source' not in namespace:
            msg = 'You must set "source" to the geospatial metadata file name.'
            raise AttributeError(msg)
        namespace.update(_postpare(namespace.pop('source')))
        return type.__new__(cls, name, bases, namespace)

def _postpare(source):
    metadata = ElementTree.parse(source)

    attrs = metadata.findall('eainfo/detailed/attr')
    namespace = OrderedDict(map(_field, attrs))

    namespace['Meta'] = {}
    name = metadata.findtext('idinfo/citation/citeinfo/ftname')
    verbose_name = metadata.findtext('idinfo/citation/citeinfo/title')
    if verbose_name:
        namespace['Meta']['verbose_name'] = str(verbose_name)
    elif name:
        namespace['Meta']['verbose_name'] = str(name)

    return namespace

def _get(obj, default = None):
    return obj if obj else default

def _field(attr):
    key = str(_get(attr.findtext('attlabel'), attr.findtext('attalias')))
    Class = TYPE_MAPPING[_get(attr.findtext('attrtype'), 'String').lower()]
    attwidth = attr.findtext('attwidth')
    kwargs = {
        'max_length': None if attwidth == None else int(attwidth),
        'verbose_name': str(attr.findtext('attrdef')),
    }
    return (key, Class(**kwargs))

# What's the difference between 'attalias' and 'attrlabl'?
#
# Dunno what 'attscale' and 'attrdefs' are for.
#
# I guess 'atprecis' and 'atnumdec' have something to do with
# precisiion of numbers.
#
# I think 'attrdomv' is a comment about things that aren't encoded
# in the schema.
