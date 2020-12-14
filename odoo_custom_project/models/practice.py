from odoo import fields, models, api


class Practice (models.Model):
    _name = 'practice.practice'
    _description = 'Practice'

    name = fields.Char(string="Name", required=True)
    description = fields.Text(string="Description")
