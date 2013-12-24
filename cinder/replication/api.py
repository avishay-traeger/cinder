# Copyright (C) 2013 Hewlett-Packard Development Company, L.P.
# All Rights Reserved.
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

"""
Handles all requests relating to volume replication.
"""


from cinder.db import base
from cinder import exception
from cinder.openstack.common import excutils
from cinder.openstack.common import log as logging
from cinder import policy
from cinder.volume import api as volume_api


LOG = logging.getLogger(__name__)


def check_policy(context, action):
    target = {
        'project_id': context.project_id,
        'user_id': context.user_id,
    }
    _action = 'replication:%s' % action
    policy.enforce(context, _action, target)


class API(base.Base):
    """API for interacting volume replication relationships."""

    def __init__(self, db_driver=None):
        super(API, self).__init__(db_driver)
        self.volume_api = volume_api.API()

    def get(self, context, relationship_id):
        check_policy(context, 'get')
        rv = self.db.replication_relationship_get(context, relationship_id)
        return dict(rv.iteritems())

    def get_all(self, context, marker=None, limit=None, sort_key='id',
                sort_dir='desc', filters={}):
        check_policy(context, 'get_all')
        try:
            if limit is not None:
                limit = int(limit)
                if limit < 0:
                    msg = _('limit param must be positive')
                    raise exception.InvalidInput(reason=msg)
        except ValueError:
            msg = _('limit param must be an integer')
            raise exception.InvalidInput(reason=msg)

        rels = self.db.replication_relationship_get_all(context, marker,
                                                        limit, sort_key,
                                                        sort_dir)
        if filters:
            LOG.debug(_("Searching by: %s") % str(filters))
            result = []
            not_found = object()
            for rel in rels:
                for opt, value in filters.iteritems():
                    if rel.get(opt, not_found) == value:
                        result.append(rel)
            rels = result

        return rels

    #def swap(self, context, relationship_id):
