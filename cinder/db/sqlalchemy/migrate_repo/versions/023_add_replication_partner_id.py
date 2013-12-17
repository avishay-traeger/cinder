# vim: tabstop=4 shiftwidth=4 softtabstop=4

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

from sqlalchemy import Boolean, Column, DateTime, Enum
from sqlalchemy import MetaData, String, Table, ForeignKey

from cinder.openstack.common import log as logging

LOG = logging.getLogger(__name__)


def upgrade(migrate_engine):
    meta = MetaData()
    meta.bind = migrate_engine

    replication = Table(
        'replication', meta,
        Column('created_at', DateTime(timezone=False)),
        Column('updated_at', DateTime(timezone=False)),
        Column('deleted_at', DateTime(timezone=False)),
        Column('deleted', Boolean),
        Column('id', String(36), primary_key=True, nullable=False),
        Column('primary_id', String(36)),
        Column('secondary_id', String(36)),
        Column('mirror_status', Enum('error', 'starting', 'copying',
                                     'active', 'stopping', 'deleting')),
        Column('extended_status', String(255)),
        mysql_engine='InnoDB',
        mysql_charset='utf8'
    )

    try:
        replication.create()
    except Exception:
        LOG.error(_("Table |%s| not created!"), repr(replication))
        raise


def downgrade(migrate_engine):
    meta = MetaData()
    meta.bind = migrate_engine
    replication = Table('replication',
                        meta,
                        autoload=True)
    try:
        replication.drop()
    except Exception:
        LOG.error(_("replication table not dropped"))
