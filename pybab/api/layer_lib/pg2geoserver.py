import urllib, urllib2, urlparse
import os

workspace_xml = "<workspace><name>{ws_name}</name></workspace>"
datastore_xml = """
<dataStore>
<name>{ds_name}</name>
<connectionParameters>
     <host>{pg_host}</host>
     <port>{pg_port}</port>
     <database>{database}</database>
     <schema>{schema}</schema>
     <user>{user}</user>
     <passwd>{password}</passwd>
     <dbtype>postgis</dbtype>
</connectionParameters>
</dataStore>
"""
layer_xml = "<featureType><name>{name}</name></featureType>"
style_xml = "<style><name>{name}</name><filename>{name}.sld</filename></style>"

class Pg2Geoserver(object):
    def __init__(self, geoserver_url, username, password):
        """Sets the connection with geoserver"""
        self.geoserver_url = geoserver_url

        manager = urllib2.HTTPPasswordMgrWithDefaultRealm()
        manager.add_password(None, geoserver_url, username, password)
        handler = urllib2.HTTPBasicAuthHandler(manager)
        opener = urllib2.build_opener(handler)
        urllib2.install_opener(opener)

    def create_workspace(self, name):
        """Creates a workspace with the specified name.
        If already existing, does nothing.
        Raises urllib2.HTTPError if something went wrong in the request.
        Raises urllib2.URLError if the geoserver is unreachable.
        Returns true if the workspace is created, false if already existing"""

        headers = {'Content-type' : 'text/xml'}
        data = workspace_xml.format(ws_name=name)
        url = urlparse.urljoin(self.geoserver_url,
                               "/geoserver/rest/workspaces")
        req = urllib2.Request(url, data, headers)
        try:
            response = urllib2.urlopen(req)
        except urllib2.HTTPError, e:
            if not hasattr(e, 'read') or "already exists" not in e.read():
                raise
            else:
                return False
        else:
            return True

    def create_datastore(self, workspace, name,
                         pg_host, pg_port, database,
                         schema, user, password):
        """Creates a datastore with the given name in the given workspace,
        pointing to the postgis server specified by the parameters.
        Raises urllib2.HTTPError if something goes wrong.
        Raises urllib2.URLError if the geoserver is unreachable.
        """
        headers = {'Content-type' : 'text/xml'}
        data = datastore_xml.format(ds_name=name,
                                    pg_host=pg_host,
                                    pg_port=pg_port,
                                    database=database,
                                    schema=schema,
                                    user=user,
                                    password=password)
        url = urlparse.urljoin(self.geoserver_url,
                               os.path.join("/geoserver/rest/workspaces/",
                                            workspace,
                                            "datastores")
                               )
        req = urllib2.Request(url, data, headers)
        response = urllib2.urlopen(req)

        return True

    def create_layer(self, workspace, datastore, name):
        """Publics the layer with the given name of the given datastore.
        Raises urllib2.HTTPError if something goes wrong.
        Raises urllib2.URLError if the geoserver is unreachable.
        """
        headers = {'Content-type' : 'text/xml'}
        data = layer_xml.format(name=name)
        url = urlparse.urljoin(self.geoserver_url,
                               os.path.join("/geoserver/rest/workspaces/",
                                            workspace,
                                            "datastores",
                                            datastore,
                                            "featuretypes")
                               )
        req = urllib2.Request(url, data, headers)
        response = urllib2.urlopen(req)

        return True

    def delete_layer(self, layer_name):
        """Deletes the layer with the given name from geoserver"""
        headers = {'Content-type' : 'text/xml'}
        url = urlparse.urljoin(self.geoserver_url,
                               os.path.join("/geoserver/rest/layers/",
                                            urllib.quote_plus(layer_name))
                               )
        req = urllib2.Request(url, headers=headers)
        req.get_method = lambda: 'DELETE'
        response = urllib2.urlopen(req)
        return True

    def create_style(self, style_name, xml):
        """Publics the style with the given name on the geoserver.
        Raises urllib2.HTTPError if something goes wrong.
        Raises urllib2.URLError if the geoserver is unreachable.
        """
        #create style
        headers = {'Content-type' : 'text/xml'}
        data = style_xml.format(name=style_name)
        url = urlparse.urljoin(self.geoserver_url,
                               "/geoserver/rest/styles/"
                               )
        req = urllib2.Request(url, data, headers)
        response = urllib2.urlopen(req)
        #define style
        headers = {'Content-type' : 'application/vnd.ogc.sld+xml'}
        data = xml
        url = urlparse.urljoin(self.geoserver_url,
                               os.path.join("/geoserver/rest/styles/",
                                            urllib.quote_plus(style_name))
                               )
        req = urllib2.Request(url, data, headers)
        req.get_method = lambda: 'PUT'
        try:
            response = urllib2.urlopen(req)
        except (urllib2.HTTPError,urllib2.URLError) as e:
            #if the xml is not valid, delete the whole style
            self.delete_style(style_name)
            raise e
        return True

    def delete_style(self, style_name):
        """Deletes the style with the given name from geoserver"""
        headers = {'Content-type' : 'text/xml'}
        url = urlparse.urljoin(self.geoserver_url,
                               os.path.join("/geoserver/rest/styles/",
                                            urllib.quote_plus(style_name))
                               )
        req = urllib2.Request(url, headers=headers)
        req.get_method = lambda: 'DELETE'
        response = urllib2.urlopen(req)
        return True
