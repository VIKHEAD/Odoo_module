from odoo import fields, models, api


class Task(models.Model):
    _inherit = "project.task"
    _description = "Task"

    # product_ids = fields.Many2many(
    #         'product.template', 'product_template_prject_task', 'task_id', 'product_template_id',
    #         'Products', copy=False, check_company=True)
    practice_ids = fields.Many2many('practice.practice',
                                    'practice_prject_task', 'task_id',
                                    'practice_practice_id',
                                    string='Practice', copy=False)

    projects_practice_ids = fields.Many2many(related="project_id.practice_ids")
