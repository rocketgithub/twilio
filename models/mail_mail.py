# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models


class MailMail(models.Model):
    _inherit = 'mail.mail'

    phone_alias_id = fields.Many2one('twilio.phone_alias', "Twilio Phone Alias", readonly=True, index=True)
