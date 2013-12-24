# Copyright 2013 IBM Corp.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

import webob
from webob import exc

from cinder.api import common
from cinder.api import extensions
from cinder.api.openstack import wsgi
from cinder.api.views import replications as replication_view
from cinder.api import xmlutil

from cinder import exception
from cinder.openstack.common import log as logging
from cinder import replication as replicationAPI
from cinder import utils

LOG = logging.getLogger(__name__)


def make_relationship(elem):
    elem.set('id')
    elem.set('primary_id')
    elem.set('secondary_id')
    elem.set('status')
    elem.set('extended_status')


class ReplicationTemplate(xmlutil.TemplateBuilder):
    def construct(self):
        root = xmlutil.TemplateElement('relationship', selector='relationship')
        make_relationship(root)
        alias = Volume_replication.alias
        namespace = Volume_replication.namespace
        return xmlutil.MasterTemplate(root, 1, nsmap={alias: namespace})


class ReplicationsTemplate(xmlutil.TemplateBuilder):
    def construct(self):
        root = xmlutil.TemplateElement('relationships')
        elem = xmlutil.SubTemplateElement(root, 'relationship',
                                          selector='relationships')
        make_relationship(elem)
        alias = Volume_replication.alias
        namespace = Volume_replication.namespace
        return xmlutil.MasterTemplate(root, 1, nsmap={alias: namespace})


class SwapDeserializer(wsgi.MetadataXMLDeserializer):
    def default(self, string):
        dom = utils.safe_minidom_parse_string(string)
        relationship = self._extract_relationship(dom)
        return {'body': {'relationship': relationship}}

    def _extract_relationship(self, node):
        rep = {}
        replication_node = self.find_first_child_named(node, 'relationship')
        rel_id = replication_node.getAttribute('relationship_id')
        if rel_id:
            rep['relationship_id'] = rel_id
        return rep


class VolumeReplicationController(wsgi.Controller):
    """The Volume Replication API controller for the Openstack API."""

    _view_builder_class = replication_view.ViewBuilder

    def __init__(self):
        super(VolumeReplicationController, self).__init__()
        self.replication_api = replicationAPI.API()

    @wsgi.serializers(xml=ReplicationTemplate)
    def show(self, req, id):
        """Return data about replication relationships."""
        context = req.environ['cinder.context']

        try:
            relationship = self.replication_api.get(context,
                                                    relationship_id=id)
        except exception.ReplicationRelationshipNotFound as error:
            raise exc.HTTPNotFound(explanation=error.msg)

        return self._view_builder.detail(req, relationship)

    @wsgi.serializers(xml=ReplicationsTemplate)
    def index(self, req):
        """Returns a summary list of replication relationships."""
        return self._get_relationships(req, is_detail=False)

    @wsgi.serializers(xml=ReplicationsTemplate)
    def detail(self, req):
        """Returns a detailed list of replication relationships."""
        return self._get_relationships(req, is_detail=True)

    def _get_relationships(self, req, is_detail):
        """Returns a list of replications, transformed through view builder."""
        context = req.environ['cinder.context']

        params = req.params.copy()
        marker = params.pop('marker', None)
        limit = params.pop('limit', None)
        sort_key = params.pop('sort_key', 'id')
        sort_dir = params.pop('sort_dir', 'desc')
        params.pop('offset', None)

        filters = params
        allowed_filters = ['primary_id', 'secondary_id', 'status']
        unknown_opts = [opt for opt in filters if opt not in allowed_filters]
        if unknown_opts:
            bad_opts = ", ".join(unknown_opts)
            log_msg = _("Removing options '%s' from query") % bad_opts
            LOG.debug(log_msg)
            for opt in unknown_opts:
                del filters[opt]

        reps = self.replication_api.get_all(context, marker=marker,
                                            limit=limit, sort_key=sort_key,
                                            sort_dir=sort_dir, filters=filters)

        reps = [dict(rep.iteritems()) for rep in reps]
        limited_list = common.limited(reps, req)

        if is_detail:
            relationships = self._view_builder.detail_list(req, limited_list)
        else:
            relationships = self._view_builder.summary_list(req, limited_list)

        return relationships

    @wsgi.response(202)
    @wsgi.serializers(xml=ReplicationTemplate)
    @wsgi.deserializers(xml=SwapDeserializer)
    def swap(self, req, body):
        """Swap roles of volumes in a replication relationship."""
        LOG.debug(_('Swapping volume replication roles: %s'), body)
        if not self.is_valid_body(body, 'relationship'):
            raise exc.HTTPBadRequest()

        context = req.environ['cinder.context']

        try:
            relationship = body['relationship']
            relationship_id = relationship['relationship_id']
        except KeyError:
            msg = _("Incorrect request body format")
            raise exc.HTTPBadRequest(explanation=msg)

        LOG.audit(_("Swapping replication roles of relationship %s"),
                  relationship_id,
                  context=context)

        try:
            self.replication_api.swap(context, relationship_id)
        except exception.ReplicationRelationshipNotFound as error:
            raise exc.HTTPNotFound(explanation=error.msg)

        return webob.Response(status_int=202)


class Volume_replication(extensions.ExtensionDescriptor):
    """Volume replication management support"""

    name = "VolumeReplication"
    alias = "os-volume-replication"
    namespace = "http://docs.openstack.org/volume/ext/volume-replication/" + \
                "api/v1.1"
    updated = "2013-12-23T00:00:00+00:00"

    def get_resources(self):
        resources = []
        res = extensions.ResourceExtension(Volume_replication.alias,
                                           VolumeReplicationController(),
                                           collection_actions={'detail':
                                                               'GET'},
                                           member_actions={'swap': 'POST'})
        resources.append(res)
        return resources
