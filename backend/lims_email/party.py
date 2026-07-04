# This file is part of lims_email module for Tryton.
# The COPYRIGHT file at the top level of this repository contains
# the full copyright notices and license terms.

from trytond.model import fields
from trytond.pool import PoolMeta


class Party(metaclass=PoolMeta):
    __name__ = 'party.party'

    email_report = fields.Boolean('Automatic sending of Report by Email')
    result_report_format = fields.Many2One('lims.result_report.format',
        'Results Report Name Format')

    @staticmethod
    def default_email_report():
        return False
