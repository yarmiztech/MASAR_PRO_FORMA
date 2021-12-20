from odoo import models,fields,api
from datetime import datetime


from uuid import uuid4
import qrcode
import base64
import logging

from lxml import etree

class ProFormaInvoice(models.Model):
    _inherit = 'pro.forma.invoice'


    def default_bank_details(self):
        bank_details = self.env.company.partner_id.bank_ids
        if bank_details:
            return bank_details[0].id
        else:
            return None


    company_bank_id = fields.Many2one('res.partner.bank',default=default_bank_details)
    po_number = fields.Char('PO Number')
    po_date = fields.Date('PO Date')
    delivery_location = fields.Char('Delivery Location')
    delivery_note_number = fields.Char('Delivery Note No')


    # def print_einvoice(self):
    #     return self.env.ref('masar_arabia_einvoice.masar_arabic_einvoice_report_1').report_action(self)

    def total_amount_to_words(self):
        self.check_amount_in_words = self.currency_id.amount_to_text(self.amount_total)
        return self.check_amount_in_words


    def total_price_subtotal(self):
        total = 0.00
        for price in self.invoice_line_ids:
            if price.discount:
                qty_unit_price = price.quantity * price.price_unit
                total+=qty_unit_price
            else:
                # total = self.amount_untaxed
                qty_unit_price = price.quantity * price.price_unit
                total+=qty_unit_price

        return total


    def total_discount(self):
        discount = 0.00
        total = 0.00
        for dis in self.invoice_line_ids:
            if dis.discount != 0.00:
                total = dis.quantity * dis.price_unit
                discount+= total*(dis.discount/100)
            else:
                ''
        return discount






class ProFormaInvoiceLine(models.Model):
    _inherit = 'pro.forma.invoice.line'

    def compute_tax(self):
        amount = 0
        for tax in self.tax_ids:
            amount = amount + tax.amount
        return ((self.quantity * self.price_unit)/100) * amount


    def total_amount(self):
        total = 0.00
        total_amount = 0.00
        for vat in self:

            total = vat.price_subtotal * 0.15
            total_amount =total + vat.price_subtotal
        return total_amount


    def product_arabic(self):
        for products in self:
            product = products.product_id.name
            product_template = self.env['product.template'].search([('name','=',product)])
            for ar in product_template:
                return ar.arabic


    def line_price_subtotal(self):
        for price in self:
            if price.discount != 0.00:
                qty_price = price.quantity * price.price_unit
                return qty_price
            else:
                return price.price_subtotal










