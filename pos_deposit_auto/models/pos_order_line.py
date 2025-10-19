# -*- coding: utf-8 -*-
from odoo import api, fields, models

class PosOrderLine(models.Model):
    _inherit = "pos.order.line"

    is_deposit = fields.Boolean(string="Is Deposit", default=False, index=True)
    linked_main_line_id = fields.Many2one("pos.order.line", string="Linked Main Line", ondelete="set null", index=True)