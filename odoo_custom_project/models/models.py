import datetime

from odoo import models, fields, api
from odoo import _
from odoo.exceptions import UserError, AccessError, ValidationError


class ProjectType(models.Model):
    _name = 'project.type'
    _description = 'Project Stage'
    _order = 'sequence, id'

    name = fields.Char(string='Stage Name', readonly=True)
    description = fields.Text(string='Description', )
    sequence = fields.Integer(string='Sequence', default=1)
    fold = fields.Boolean(string='Folded in Kanban',
                          help='This stage is folded in the kanban view when '
                               'there are no records in that stage to display.')
    in_progres_trace = fields.Boolean(string='Trace date In Progres',
                                      default=False)
    end_data_trace = fields.Boolean(string='Trace date Finish',
                                    default=False)
    cancel_stage = fields.Boolean(string='Cancel stage', default=False)
    new_stage = fields.Boolean(string='For Potential', default=False)

    def write(self, values):
        stages_in_progr = self.env['project.type'].search(
            [('in_progres_trace', '=', 'True')])
        stage_end_data = self.env['project.type'].search(
            [('end_data_trace', '=', 'True')])
        cancel_stage = self.env['project.type'].search(
            [('cancel_stage', '=', 'True')])
        if (stages_in_progr and values.get('in_progres_trace') is True) or (
                stage_end_data and values.get('end_data_trace') is True) or (
                cancel_stage and values.get('cancel_stage') is True):
            raise ValidationError(
                """There can be only one Stage with the propertys like 'Track Date In Robot', 'Track Completion Date', 'Canceled'.""")
        res = super(ProjectType, self).write(values)
        return res


class Project(models.Model):
    _description = "Project"
    _inherit = "project.project"

    int_reference = fields.Char(string='Project number',
                                # readonly=True
                                )
    date_start = fields.Date(string='Date start', )
    date_end = fields.Date(string='Date end', )
    project_partner_id = fields.Many2one('res.users',
                                         string='Project partner',
                                         default=lambda self: self.env.user,
                                         tracking=True)
    type_payments = fields.Selection(
        selection=[
            ('standard_bid', 'Standart bid'),
            ('spec_bid', 'Special bid'),
            ('fixed_bid', 'Fixed bid'),
            ('fixed_price', 'Fixed price'),
            ('fixed_month_payment', 'Fixed monthly payment'),
            ('cap', 'CAP')],
        string='Type payment',
        default='standard_bid',
        required=True)
    need_check = fields.Boolean(string='Partner invoice approve',
                                default=False)
    fixed_rate = fields.Float(string='Fixed rate', default=0.00)
    budget = fields.Integer(string='Project budget', required=True,
                            default=0.00)
    used_budget = fields.Monetary(string='Used budget', readonly=True,
                                  related="partner_id.total_invoiced")
    input_lang = fields.Selection(selection=[
        ('ukr', 'ukrainian'),
        ('rus', 'russian'),
        ('eng', 'english'), ],
        string='Language filling',
        default='ukr')
    paymant_currency_id = fields.Many2one('res.currency',
                                          string="Payment currency",
                                          default=lambda self: self.env.ref(
                                              'base.USD'))
    cancel_reasons = fields.Char("Cancel reason")
    date_in_progres = fields.Date(string='Date in “In progress”', )
    date_finish = fields.Date(string='Date in "Finish"', )
    description = fields.Text("Description")
    condition = fields.Text("Project terms")
    project_partner_ids = fields.One2many('vkp.project.team', 'project_id',
                                          string="Project team")
    project_stage_id = fields.Many2one('project.type', string='Stage',
                               ondelete='restrict',
                               default=lambda self: self.env[
                                   'project.type'].search(
                                   [("name", "=", "Потенційній проект")], limit=1))
    in_cancel_stage = fields.Boolean(string='in_cancel_stage', default=False)
    in_new_stage = fields.Boolean(string='in_new_stage', default=False)
    exclude_from_report = fields.Boolean(string='Exclude from report',
                                         default=False)
    budget_diff = fields.Float(default=0.00)
    email_budget_sent = fields.Integer(default=0)
    practice_ids = fields.Many2many('practice.practice',
                                    'practice_practice_project', 'project_id',
                                    'practice_practice_id',
                                    string='Practice', copy=False
                                    )
    title_of_works = fields.Char(string='Title of works')

    invoice_count = fields.Integer(string='Invoice', compute='_invoice_count')
    name = fields.Char(readonly=True)

    @api.onchange('partner_id')
    def onchange_partner_id(self):
        partner_projects = self.search(
            [('partner_id', '=', self.partner_id.id)])
        if partner_projects:
            old_reference = self.search(
                        [('id', '=', max(partner_projects.ids))]).int_reference
            if old_reference and old_reference.isdigit():
                copy_ref = int(old_reference) + 1
                if copy_ref < 10:
                    new_reference = f'0{copy_ref}'
                else:
                    new_reference = str(copy_ref)
                self.int_reference = new_reference
            else:
                self.int_reference = '01'
        else:
            self.int_reference = '01'

    def _invoice_count(self):
        self.invoice_count = self.env['account.move'].search_count(
            [('project_id', '=', self.id)])

    def action_invoice(self, context=None):
        action_id = self.env.ref('account.action_move_out_invoice_type').read()[
            0]
        if action_id:
            action_id['domain'] = [('project_id', '=', self.id)]
            return action_id

    @api.model
    def create(self, vals):
        partner_code = self.env['res.partner'].browse([vals['partner_id']]).partner_code
        if vals.get('int_reference') and vals.get('partner_id') and vals.get(
                'title_of_works') and partner_code:
            name = partner_code + '-' + vals.get(
                'int_reference') + '-' + vals.get('title_of_works')
            vals.update({'name': name})
        res = super(Project, self).create(vals)
        partners = {res.user_id, res.project_partner_id}
        for par in partners:
            employee = self.env['hr.employee'].search([('user_id', '=', par.id)])
            project_team = self.env['vkp.project.team'].search([('project_id', '=', res.id)])
            if employee.id not in project_team.partner_id.ids:
                self.env['vkp.project.team'].create(
                    {'project_id': res.id,
                     'partner_id': employee.id,
                     'rate': employee.timesheet_cost,
                     'currency_id': employee.currency_id.id
                     })
        return res

    @api.constrains('budget')
    def _check_budget(self):
        for record in self:
            if record.type_payments == 'fixed_price' and record.budget <= 0:
                raise ValidationError(
                    "Field 'Budget'is required.")

    @api.onchange('project_stage_id')
    def onchange_project_stage_id(self):
        cancel_stage = self.env['project.type'].search(
            [('cancel_stage', '=', 'True')])
        if self.project_stage_id.id and self.project_stage_id.id == cancel_stage.id:
            template = self.env.ref(
                'vkp_project_ext.email_template_used_budget')
            self.send_email(template)
            self.in_cancel_stage = True
        else:
            self.in_cancel_stage = False
        new_stage = self.env['project.type'].search(
            [('new_stage', '=', 'True')])
        self.in_new_stage = True if self.project_stage_id.id == new_stage.id else False

    @api.onchange('used_budget')
    def onchange_used_budget(self):
        if self.budget:
            template = self.env.ref(
                'vkp_project_ext.email_template_used_budget')
            res = round((self.used_budget/self.budget)*100)
            self.budget_diff = res
            if 50 <= res <= 70 and self.email_budget_sent not in [50, 70, 100]:
                self.send_email(template)
                self.write({'email_budget_sent': 50})
            if 70 <= res <= 100 and self.email_budget_sent not in [70, 100]:
                self.send_email(template)
                self.write({'email_budget_sent': 70})
            if res >= 100 and self.email_budget_sent not in [100]:
                self.write({'email_budget_sent': 100})
                self.send_email(template)

    @api.model
    def send_email(self, template, _logger=None):
        if self.ids[0]:
            res_id = self.ids[0]
            if template and res_id:
                template.with_context().send_mail(
                    res_id, force_send=True)
            else:
                _logger.warning(
                    "No email template found, id {0}.".format(template.id))
        return True

    def write(self, values):
        stage_in_progres = self.env['project.type'].search(
            [('in_progres_trace', '=', 'True')])
        stage_end_data = self.env['project.type'].search(
            [('end_data_trace', '=', 'True')])
        if 'project_stage_id' in values and values.get(
                'project_stage_id') == stage_in_progres.id:
            values.update({'date_in_progres': datetime.datetime.today()})
        if 'project_stage_id' in values and values.get(
                                    'project_stage_id') == stage_end_data.id:
            values.update({'date_finish': datetime.datetime.today()})

        if self.project_partner_ids and values.get('type_payments') == 'fixed_bid':
            for partner in self.project_partner_ids:
                partner.rate = values.get('fixed_rate') or self.fixed_rate

        if values.get('user_id') or values.get('project_partner_id'):
            partners = {values.get('user_id'), values.get('project_partner_id')}
            for par in partners:
                if par:
                    employee = self.env['hr.employee'].search([('user_id', '=', par)])
                    project_team = self.env['vkp.project.team'].search([('project_id', '=', self.id)])
                    if employee.id not in project_team.partner_id.ids:
                        self.env['vkp.project.team'].create(
                            {'project_id': self.id,
                             'partner_id': employee.id,
                             'rate': employee.timesheet_cost,
                             'currency_id': employee.currency_id.id
                             })
        res = super(Project, self).write(values)
        return res

    @api.onchange('fixed_rate', 'paymant_currency_id')
    def onchange_fixed_rate(self):
        if self.type_payments == 'fixed_bid' and self.fixed_rate:
            for partner in self.project_partner_ids:
                partner.write({'rate': self.fixed_rate,

                               'currency_id': self.paymant_currency_id})

    @api.onchange('type_payments')
    def onchange_type_payments(self):
        # ! will be refactored !
        if self.project_partner_ids:
            for partner in self.project_partner_ids:
                if self.type_payments == 'standard_bid':
                    if partner.partner_id.user_id:
                        partner.write({'rate': partner.partner_id.timesheet_cost or False,
                           'currency_id': partner.partner_id.rate_currency_id.id,
                           'project_type_payments': self.type_payments,
                           })
                    else:
                        partner.write({'rate': 0.0,
                                  'currency_id': self.env.company.currency_id.id,
                                   'project_type_payments': self.type_payments,
                                   })

                elif self.type_payments == 'spec_bid':
                    if partner.partner_id.user_id:
                        partner.write(
                            {'rate': partner.partner_id.timesheet_cost or False,
                         'currency_id': partner.partner_id.rate_currency_id.id,
                         'project_type_payments': self.type_payments,
                         })
                    else:
                        partner.write({'rate': 0.0,
                                   'currency_id': self.env.company.currency_id.id,
                                   'project_type_payments': self.type_payments,
                                   })

                elif self.type_payments == 'fixed_bid':
                    if partner.partner_id.user_id:
                        partner.write(
                            {'project_type_payments': self.type_payments,
                             'rate': self.fixed_rate or partner.partner_id.timesheet_cost,
                             'currency_id': self.paymant_currency_id or
                                    partner.partner_id.rate_currency_id.id})
                    else:
                        partner.write({'project_type_payments': self.type_payments})

                elif self.type_payments in ['fixed_price',
                                            'fixed_month_payment', 'cap']:
                    partner.write({'rate': partner.partner_id.timesheet_cost,
                               'currency_id': self.env.company.currency_id.id,
                               'project_type_payments': self.type_payments,
                               })


class VkpProjectTeam(models.Model):
    _name = "vkp.project.team"
    _description = "Vkp Project Team"

    _sql_constraints = [
        ('partner_id', 'unique(project_id, partner_id)',
         "Партнер вже існує в Проектній команді.")]

    project_id = fields.Many2one('project.project', string='Project',
                                 required=True)
    partner_id = fields.Many2one('hr.employee', string='Project partner',
                                 required=True)
    rate = fields.Float(string='Rate', default=0.00, store=True)
    currency_id = fields.Many2one('res.currency', string="Currency", store=True)
    project_type_payments = fields.Selection(
        selection=[
            ('standard_bid', 'Standart bid'),
            ('spec_bid', 'Special bid'),
            ('fixed_bid', 'Fixed bid'),
            ('fixed_price', 'Fixed price'),
            ('fixed_month_payment', 'Fixed monthly payment'),
            ('cap', 'CAP')],
        string='Type payment',
        default='standard_bid')

    @api.onchange('partner_id')
    def onchange_partner_id(self):
        if self.partner_id:
            self.rate = self.partner_id.timesheet_cost
            self.currency_id = self.partner_id.rate_currency_id.id or self.env.company.currency_id.id
            self.project_type_payments = self.project_id.type_payments
