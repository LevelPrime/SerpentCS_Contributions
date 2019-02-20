# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

# 1:  imports of odoo
from odoo import models, fields, api, _


class LabelPrint(models.Model):
    _name = "label.print"

    name = fields.Char("Name", size=64, required=True, index=True)
    model_id = fields.Many2one('ir.model', 'Model', required=True, index=True)
    field_ids = fields.One2many("label.print.field", 'report_id',
                                string='Fields')
    ref_ir_act_report = fields.Many2one('ir.actions.act_window',
                                        'Sidebar action', readonly=True,
                                        help="""Sidebar action to make this
                                        template available on records
                                        of the related document model""")
    ref_ir_value = fields.Many2one('ir.values', 'Sidebar button',
                                   readonly=True,
                                   help="Sidebar button to open the \
                                   sidebar action")
    model_list = fields.Char('Model List', size=256)
    paperformat_id = fields.Many2one('report.paperformat', string='Paper Format')
    single_page = fields.Boolean(string='Single page label')
    report_id = fields.Many2one('ir.actions.report.xml', string='Report')

    @api.onchange('model_id')
    def onchange_model(self):
        model_list = []
        if self.model_id:
            model_obj = self.env['ir.model']
            current_model = self.model_id.model
            model_list.append(current_model)
            active_model_obj = self.env[self.model_id.model]
            if active_model_obj._inherits:
                for key, val in active_model_obj._inherits.items():
                    model_ids = model_obj.search([('model', '=', key)])
                    if model_ids:
                        model_list.append(key)
        self.model_list = model_list

    @api.onchange('paperformat_id')
    def onchange_paperformat_id(self):
        if self.report_id:
            self.report_id.sudo().paperformat_id = self.paperformat_id

    @api.model
    def create(self, vals):
        label = super(LabelPrint, self).create(vals)
        label.report_id = label.create_label_report()
        return label

    def create_label_report(self):
        paperformat_id = None
        if self.paperformat_id:
            paperformat_id = self.paperformat_id.id

        report = None
        if self.report_id:
            report = self.report_id.id

        report_id = self.env['ir.actions.report.xml'].create({
            'name': 'Label {}'.format(self.name),
            'model': 'label.config',
            'report_type': 'qweb-pdf',
            'paperformat_id': paperformat_id,
            'report_id': report,
            'report_name': 'label.report_label',
        })
        return report_id

    @api.multi
    def create_action(self):
        vals = {}
        action_obj = self.env['ir.actions.act_window']
        for data in self.browse(self.ids):
            src_obj = data.model_id.model
            button_name = _('Label (%s)') % data.name
            vals['ref_ir_act_report'] = action_obj.create({
                'name': button_name,
                'type': 'ir.actions.act_window',
                'res_model': 'label.print.wizard',
                'src_model': src_obj,
                'view_type': 'form',
                'context': "{'label_print' : %d}" % (data.id),
                'view_mode': 'form,tree',
                'target': 'new',
            })
            id_temp = vals['ref_ir_act_report'].id
            vals['ref_ir_value'] = self.env['ir.values'].create({
                'name': button_name,
                'model': src_obj,
                'key2': 'client_action_multi',
                'value': "ir.actions.act_window," + str(id_temp),
                'object': True,
            })
        self.write({
            'ref_ir_act_report': vals.get('ref_ir_act_report', False).id,
            'ref_ir_value': vals.get('ref_ir_value', False).id,
        })
        return True

    @api.multi
    def unlink_action(self):
        for template in self:
            if template.ref_ir_act_report.id:
                template.ref_ir_act_report.unlink()
            if template.ref_ir_value.id:
                template.ref_ir_value.unlink()
        return True

    @api.multi
    def unlink(self):
        for label in self:
            if label.report_id:
                label.report_id.unlink()
        return super(LabelPrint, self).unlink()


class LabelPrintField(models.Model):
    _name = "label.print.field"
    _rec_name = "sequence"
    _order = "sequence"

    sequence = fields.Integer("Sequence", required=True)
    field_id = fields.Many2one('ir.model.fields', 'Fields', required=False)
    report_id = fields.Many2one('label.print', 'Report')
    type = fields.Selection([('normal', 'Normal'), ('barcode', 'Barcode'),
                             ('image', 'Image')],
                            'Type', required=True, default='normal')
    python_expression = fields.Boolean('Python Expression')
    python_field = fields.Char('Fields')
    fontsize = fields.Float("Font Size", default=8.0)
    position = fields.Selection([('left', 'Left'), ('right', 'Right'),
                                 ('top', 'Top'), ('bottom', 'Bottom')],
                                'Position')
    nolabel = fields.Boolean('No Label')
    newline = fields.Boolean('New Line', deafult=True)
    field_class = fields.Char(string='HTML class')
    field_style = fields.Char(string='HTML Style')


class IrModelFields(models.Model):
    _inherit = 'ir.model.fields'

    @api.model
    def name_search(self, name='', args=None, operator='ilike', limit=None):
        if 'model_list' in self._context.keys():
            data = self._context['model_list']
            args.append(('model', 'in', eval(data)))
        ret_vat = super(IrModelFields, self).name_search(name=name,
                                                         args=args,
                                                         operator=operator,
                                                         limit=limit)
        return ret_vat
