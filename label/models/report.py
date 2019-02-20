# coding=utf-8

from odoo import models, api

class Report(models.Model):
    _inherit = "report"

    @api.model
    def _get_report_from_name(self, report_name):
        if self._context.get('report_id', None):
            report_obj = self.env['ir.actions.report.xml']
            context = self.env['res.users'].context_get()
            report = report_obj.with_context(context).browse(
                int(self._context.get('report_id')))
        else:
            report = super(Report, self)._get_report_from_name(report_name)

        return report