from openerp import models, fields,api,tools
from odoo.exceptions import AccessError
from odoo.sql_db import TestCursor
from odoo.tools import config
from odoo.tools.misc import find_in_path
from odoo.http import request
from odoo.tools.safe_eval import safe_eval
from odoo.exceptions import UserError
from base64 import b64decode
from logging import getLogger
from PIL import Image
from io import StringIO
from PyPDF2 import PdfFileWriter, PdfFileReader
from PyPDF2.utils import PdfReadError


class ResCompany(models.Model):
    _inherit = "res.company"

    company_header_bgcolor = fields.Char( 'Company Header Back ground Color:')
    company_header_fontcolor = fields.Char( 'Company Header Font Color:',default= "#000000")
    report_header_bgcolor = fields.Char('Report Header Back Ground Color')
    report_header_fontcolor = fields.Char(' Report Header Font Color')
    title_bgcolor = fields.Char('Title Back Ground Color')
    title_fontcolor = fields.Char('Title Font Color')
    subtitle_bgcolor = fields.Char('Subtitle Back Ground Color')
    subtitle_fontcolor =fields.Char('Subtitle Font Color')
    text_bgcolor= fields.Char('Text Back Ground')
    text_fontcolor = fields.Char('Text Font Color')
    company_header_bgcolor1 = fields.Char( 'Company Header Back ground Color:')
    company_header_fontcolor1 = fields.Char( 'Company Header Font Color:')
    report_header_bgcolor1 = fields.Char('Report Header Back Ground Color')
    report_header_fontcolor1 = fields.Char(' Report Header Font Color')
    title_bgcolor1 = fields.Char('Title Back Ground Color')
    title_fontcolor1 = fields.Char('Title Font Color')
    subtitle_bgcolor1 = fields.Char('Subtitle Back Ground Color')
    subtitle_fontcolor1 =fields.Char('Subtitle Font Color')
    text_bgcolor1 = fields.Char('Text Back Ground')
    text_fontcolor1 = fields.Char('Text Font Color')
