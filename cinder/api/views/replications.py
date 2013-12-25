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

from cinder.api import common
from cinder.openstack.common import log as logging


LOG = logging.getLogger(__name__)


class ViewBuilder(common.ViewBuilder):
    """Model volume replication API responses as a python dictionary."""

    _collection_name = "os-volume-replication"

    def __init__(self):
        """Initialize view builder."""
        super(ViewBuilder, self).__init__()

    def summary_list(self, request, replications):
        """Show a list of replications without many details."""
        return self._list_view(self.summary, request, replications)

    def detail_list(self, request, replications):
        """Detailed view of a list of replications ."""
        return self._list_view(self.detail, request, replications)

    def summary(self, request, relationship):
        """Generic, non-detailed view of a relationship."""
        return {
            'relationship': {
                'id': relationship['id'],
                'primary_id': relationship['primary_id'],
                'status': relationship['status'],
                'links': self._get_links(request,
                                         relationship['id']),
            },
        }

    def detail(self, request, relationship):
        """Detailed view of a single relationship."""
        return {
            'relationship': {
                'id': relationship['id'],
                'primary_id': relationship['primary_id'],
                'secondary_id': relationship['secondary_id'],
                'status': relationship['status'],
                'extended_status': relationship['extended_status'],
                'links': self._get_links(request, relationship['id']),
            }
        }

    def _list_view(self, func, request, relationships):
        """Provide a view for a list of relationships."""
        r_list = [func(request, rel)['relationship'] for rel in
                  relationships]
        r_links = self._get_collection_links(request, relationships,
                                             self._collection_name)
        r_dict = dict(relationships=r_list)

        if r_links:
            r_dict['relationships_links'] = r_links

        return r_dict
