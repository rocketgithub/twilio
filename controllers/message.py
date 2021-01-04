# -*- coding: utf-8 -*-

import logging
import pprint
import werkzeug

from odoo import http
from odoo.http import request

_logger = logging.getLogger(__name__)

class TwilioController(http.Controller):

    @http.route([
        '/twilio/webhook',
    ], type='http', auth='none', csrf=False)
    def twilio_webhook(self, **post):
        """ Webhook """
        _logger.info('Twilio: mensaje %s', pprint.pformat(post))
        request.env['twilio.phone_alias'].sudo().message_process(post)
        return str("""
<?xml version="1.0" encoding="UTF-8"?>
<Response></Response>
""")
