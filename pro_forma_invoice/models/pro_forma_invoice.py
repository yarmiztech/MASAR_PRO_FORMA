from odoo import models,fields,api,_
from datetime import datetime
from uuid import uuid4
import qrcode
import base64
import logging
from lxml import etree
import werkzeug.urls
try:
    import qrcode
except ImportError:
    qrcode = None

class ProFormaInvoice(models.Model):
    _name = 'pro.forma.invoice'

    name = fields.Char('Pro-Forma Invoice')
    partner_id = fields.Many2one('res.partner',string="Customer")
    payment_reference = fields.Char()
    partner_bank_id = fields.Many2one('res.partner.bank')
    invoice_date = fields.Date()
    arabic_date = fields.Char()
    invoice_payment_term_id = fields.Many2one('account.payment.term')
    invoice_due_date = fields.Date()
    invoice_line_ids = fields.One2many('pro.forma.invoice.line','invoice_id')
    amount_untaxed = fields.Float(compute='compute_untaxed_amount_total')
    ar_amount_untaxed = fields.Char()
    discount = fields.Float(compute='compute_discount')
    ar_discount = fields.Char()
    amount_tax = fields.Float(compute='compute_tax')
    ar_amount_tax = fields.Char()
    amount_total = fields.Float(compute='compute_amount_total')
    ar_amount_total = fields.Char()
    amount_total_word_ar = fields.Char()
    state = fields.Selection([('draft','Draft'),('done','Done')],default="draft")
    advance_amount = fields.Float()
    advance_bool = fields.Boolean()
    company_id = fields.Many2one('res.company', required=True, default=lambda self: self.env.company)
    datetime_field = fields.Datetime(string="Create Date", default=lambda self: fields.Datetime.now())
    decoded_data = fields.Char('Decoded Data')
    qr_image = fields.Binary(string="QR Image")
    advance_id = fields.Many2one('account.payment')
    currency_id = fields.Many2one('res.currency', related='company_id.currency_id')




    def view_advance(self):
        contract_obj = self.advance_id
        contract_ids = []
        for each in contract_obj:
            contract_ids.append(each.id)
        # contract_ids = []
        # contract_ids.append(self.sale_id)
        view_id = self.env.ref('account.view_account_payment_form').id
        if contract_ids:
            if len(contract_ids) <= 1:
                value = {
                    'view_type': 'form',
                    'view_mode': 'form',
                    'res_model': 'account.payment',
                    'view_id': view_id,
                    'type': 'ir.actions.act_window',
                    'name': _('Advance'),
                    'res_id': contract_ids and contract_ids[0]
                }
            else:
                value = {
                    'domain': str([('id', 'in', contract_ids)]),
                    'view_type': 'form',
                    'view_mode': 'tree,form',
                    'res_model': 'account.payment',
                    'view_id': False,
                    'type': 'ir.actions.act_window',
                    'name': _('Advance'),
                    'res_id': contract_ids
                }

            return value



    def testing(self):
        leng = len(self.company_id.name)
        company_name = self.company_id.name
        if 42 > leng:
            for r in range(42-leng):
                if len(company_name) != 42:
                   company_name +=' '
                else:
                    break
        else:
            if 42 < leng:
                company_name = company_name[:42]
        vat_leng = len(self.company_id.vat)
        vat_name = self.company_id.vat
        if 17 > vat_leng:
            for r in range(15 - vat_leng):
                if len(vat_name) != 15:
                    vat_name += ' '
                else:
                    break
        else:
            if 17 < leng:
                vat_name = vat_name[:17]

        amount_total = str(self.amount_total)
        amount_leng = len(str(self.amount_total))
        if len(amount_total) < 17:
            for r in range(17-amount_leng):
                if len(amount_total) != 17:
                   amount_total +=' '
                else:
                    break

        tax_leng = len(str(self.amount_tax))
        amount_tax_total = str(self.amount_tax)
        if len(amount_tax_total) < 17:
            for r in range(17-tax_leng):
                if len(amount_tax_total) != 17:
                   amount_tax_total +=' '
                else:
                    break
        TimeAndDate = str(self.invoice_date) + "T" + str(self.datetime_field.time()) + "Z"
        time_length = len(str(self.invoice_date) + "T" + str(self.datetime_field.time()) + "Z")

        Data = str(chr(1)) + str(chr(leng)) + self.company_id.name
        Data += (str(chr(2))) + (str(chr(vat_leng))) + vat_name
        Data += (str(chr(3))) + (str(chr(time_length))) + TimeAndDate
        Data += (str(chr(4))) + (str(chr(len(str(self.amount_total))))) + str(self.amount_total)
        Data += (str(chr(5))) + (str(chr(len(str(self.amount_tax))))) + str(self.amount_tax)
        data = Data
        import base64
        print(data)
        mou = base64.b64encode(bytes(data, 'utf-8'))
        self.decoded_data = str(mou.decode())
        qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=20,
                border=4,
            )
        data_im = str(mou.decode())
        qr.add_data(data_im)
        qr.make(fit=True)
        img = qr.make_image()

        import io
        import base64

        temp = io.BytesIO()
        img.save(temp, format="PNG")
        qr_image = base64.b64encode(temp.getvalue())
        self.qr_image = qr_image
        print(mou.decode())
        return str(mou.decode())




    @api.depends('invoice_line_ids')
    def compute_discount(self):
        for invoice in self:
            discount = 0
            for line in invoice.invoice_line_ids:
                discount = discount + (((line.quantity * line.price_unit)/100)*line.discount)
            invoice.discount = discount

    def create_advance_payment(self):
        return {
            'name': 'Advance Payment',
            'view_mode': 'form',
            'res_model': 'account.payment',
            'view_id': self.env.ref('account.view_account_payment_form').id,
            'type': 'ir.actions.act_window',
            'context': {
                'default_payment_type': 'inbound',
                'default_partner_id': self.partner_id.id,
                'default_partner_type': 'customer',
                'search_default_inbound_filter': 1,
                'default_pro_invoice_id': self.id,
                'default_pro_invoice_visibility': True,
                'default_move_journal_types': ('bank', 'cash'),
                'default_amount':self.advance_amount
            },

        }

    # @api.depends('amount_total','advance_amount')
    # def compute_residual_amount(self):
    #     for line in self:
    #         line.amount_residual = line.amount_total - line.advance_amount

    @api.depends('amount_untaxed','amount_tax','advance_amount')
    def compute_amount_total(self):
        for invoice in self:
            invoice.amount_total = invoice.advance_amount + invoice.amount_tax

    @api.depends('invoice_line_ids')
    def compute_untaxed_amount_total(self):
        for invoice in self:
            untaxed_amount = 0
            for line in invoice.invoice_line_ids:
                untaxed_amount = untaxed_amount + line.price_subtotal
            invoice.amount_untaxed = untaxed_amount



    @api.depends('invoice_line_ids','advance_amount')
    def compute_tax(self):
        for invoice in self:
            percentage = 0
            for line in invoice.invoice_line_ids:
                for line_tax in line.tax_ids:
                    percentage = line_tax.amount
            invoice.amount_tax = (invoice.advance_amount / 100) * percentage




    def pro_forma_done(self):
        self.state = 'done'





class ProFormaInvoiceLine(models.Model):
    _name = 'pro.forma.invoice.line'

    invoice_id = fields.Many2one('pro.forma.invoice')
    product_id = fields.Many2one('product.product')
    name = fields.Char('Label')
    vat_category = fields.Selection([
        ('AE', 'Vat Reverse Charge'),
        ('E', 'Exempt from Tax'),
        ('S', 'Standard rate'),
        ('Z', 'Zero rated goods'),
        ('G', 'Free export item, VAT not charged'),
        ('O', 'Services outside scope of tax'),
        ('EEA', 'VAT exempt for'),
        ('K', 'intra-community supply of goods and services'),
        ('L', 'Canary Islands general indirect tax'),
        ('M', 'Tax for production, services and importation in Ceuta and Melilla'),
        ('B', 'Transferred (VAT)'),
    ], string='VAT CATEGORY', default="S", store=True)
    discount = fields.Float()
    quantity = fields.Float(default=1)
    price_unit = fields.Float()
    tax_ids = fields.Many2many('account.tax')
    price_subtotal = fields.Float()

    @api.onchange('product_id')
    def compute_name(self):
        self.name = self.product_id.name
        self.tax_ids = [(6, 0, self.product_id.taxes_id.ids)]
        self.price_unit = self.product_id.lst_price

    @api.onchange('discount','price_unit','quantity')
    def compute_subtotal(self):
        self.price_subtotal = (self.quantity * self.price_unit)
        self.price_subtotal = self.price_subtotal - ((self.price_subtotal/100) * self.discount)




class AccountPayment(models.Model):
    _inherit = 'account.payment'

    pro_invoice_id = fields.Many2one('pro.forma.invoice')
    pro_invoice_visibility = fields.Boolean()

    def action_post(self):
        res = super(AccountPayment, self).action_post()
        self.pro_invoice_id.advance_amount = self.amount
        self.pro_invoice_id.advance_bool = True
        self.pro_invoice_id.advance_id = self.id
        return res