# -*- coding: utf-8 -*-

import logging

from odoo import api, fields, models, tools, _
from odoo.exceptions import UserError
from odoo.addons.phone_validation.tools import phone_validation
from odoo.tools.safe_eval import safe_eval
from datetime import timedelta


_logger = logging.getLogger(__name__)

class PhoneAlias(models.Model):
    """A Message Alias is a mapping of an email address with a given Odoo Document
       model. It is used by Twilio when processing incoming messages
       sent to the system. If the recipient phone of the message matches
       a Message Alias, the message will be either processed following the rules
       of that alias. If the message is a reply it will be attached to the
       existing discussion on the corresponding record, otherwise a new
       record of the corresponding model will be created.
     """
     
    _name = 'twilio.phone_alias'
    _description = "Phone Alias"
    _order = 'priority'

    name = fields.Char('Name', required=True)
    active = fields.Boolean('Active', default=True)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('done', 'Enabled'),
    ], string='Status', index=True, copy=False, default='draft')
    phone_number = fields.Char(string='Phone Number', required=True, readonly=True, help="Hostname or IP of the mail server", states={'draft': [('readonly', False)]})
    date = fields.Datetime(string='Last Message Date', readonly=True)
    secret = fields.Char(string='Secret', readonly=True, states={'draft': [('readonly', False)]})
    object_id = fields.Many2one('ir.model', string="Create a New Record", required=True, help="Process each incoming message as part of a conversation "
                                                                                "corresponding to this document type. This will create "
                                                                                "new documents for new conversations, or attach follow-up "
                                                                                "emails to the existing conversations (documents).")
    defaults = fields.Text('Default Values', required=True, default='{}',
                                 help="A Python dictionary that will be evaluated to provide "
                                      "default values when creating new records for this alias.")
    priority = fields.Integer(string='Server Priority', readonly=True, states={'draft': [('readonly', False)]}, help="Defines the order of processing, lower values mean higher priority", default=5)
    message_ids = fields.One2many('mail.mail', 'phone_alias_id', string='Messages', readonly=True)
#    attach = fields.Boolean('Keep Attachments', help="Whether attachments should be downloaded. "
#                                                     "If not enabled, incoming emails will be stripped of any attachments before being processed", default=True)
#    original = fields.Boolean('Keep Original', help="Whether a full original copy of each email should be kept for reference "
#                                                    "and attached to each processed message. This will usually double the size of your message database.")

    def button_done(self):
        for alias in self:
            alias.write({'state': 'done'})
        return True

    def button_draft(self):
        for alias in self:
            alias.write({'state': 'draft'})
        return True
        
    @api.model
    def message_process(self, twilio_data):
        if 'To' in twilio_data:
            to = twilio_data['To'].replace('whatsapp:', '')
            fr = twilio_data['From'].replace('whatsapp:', '')
            
            fr = phone_validation.phone_format(
                fr,
                None,
                None,
                force_format='INTERNATIONAL',
                raise_exception=False
            )
            
            alias = self.search([('phone_number','=',to), ('active','=',True), ('state','=','done')])
            
            if alias:
                _logger.warn(fr)
                author = self.env['res.partner'].search(['|', ('phone','=',fr), ('mobile','=',fr)])
                
                # Create a new partner if one doesn't exist yet with that phone
                if len(author) == 0:
                    author = self.env['res.partner'].with_context(mail_create_nosubscribe=True).with_user(1).sudo().create({'name': fr, 'mobile': fr});

                # Find if there is an object with the same from phone number that
                # has received an inboud message in the last 24 hours.
                min_date = fields.Datetime.now() - timedelta(days=23)
                _logger.warn(min_date)

                messages = self.env['mail.message'].sudo().search([
                    ('message_type','=','sms'),
                    ('author_id','=',author.id),
                    ('model','=',alias.object_id.model),
                    ('create_date','>',min_date)
                ], order='create_date desc')

                Model = self.env[alias.object_id.model].with_context(mail_create_nosubscribe=True, mail_create_nolog=True)
                ModelCtx = Model.with_user(1).sudo()

                # 1. If it is a reply to an existing object
                if len(messages) > 0:
                    message = messages[0]
                    _logger.warn('si existe')
                    _logger.warn(messages)
                    _logger.warn(message.res_id)
                    
                    thread = ModelCtx.browse(message.res_id)
                    subtype_id = self.env['ir.model.data'].xmlid_to_res_id('mail.mt_comment')
                    new_msg = thread.message_post(
                        body = twilio_data['Body'],
                        author_id = author.id,
                        message_type = 'sms',
                        subtype_id=subtype_id
                    )

                # 2. Handle new incoming message by checking aliases and applying their settings
                else:
                    _logger.warn('no existe')
                    thread = ModelCtx.message_new({'body': twilio_data['Body']}, safe_eval(alias.defaults).update({'name': twilio_data['Body']}))
            else:
                _logger.warn("No Twilio message alias for "+to)
