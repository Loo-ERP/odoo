# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import tools
from odoo import api, fields, models


class SaleReport(models.Model):
    _name = "sale.report"
    _description = "Sales Analysis Report"
    _auto = False
    _rec_name = 'date'
    _order = 'date desc'

    @api.model
    def _get_done_states(self):
        return ['sale', 'done', 'paid']

    name = fields.Char('Order Reference', readonly=True)
    date = fields.Datetime('Order Date', readonly=True)
    confirmation_date = fields.Datetime('Confirmation Date', readonly=True)
    product_id = fields.Many2one('product.product', 'Product Variant', readonly=True)
    product_uom = fields.Many2one('uom.uom', 'Unit of Measure', readonly=True)
    product_uom_qty = fields.Float('Qty Ordered', readonly=True)
    qty_delivered = fields.Float('Qty Delivered', readonly=True)
    qty_to_invoice = fields.Float('Qty To Invoice', readonly=True)
    qty_invoiced = fields.Float('Qty Invoiced', readonly=True)
    partner_id = fields.Many2one('res.partner', 'Customer', readonly=True)
    company_id = fields.Many2one('res.company', 'Company', readonly=True)
    user_id = fields.Many2one('res.users', 'Salesperson', readonly=True)
    price_total = fields.Float('Total', readonly=True)
    price_subtotal = fields.Float('Untaxed Total', readonly=True)
    price_tax = fields.Float('Amount Tax', readonly=True)
    untaxed_amount_to_invoice = fields.Float('Untaxed Amount To Invoice', readonly=True)
    untaxed_amount_invoiced = fields.Float('Untaxed Amount Invoiced', readonly=True)
    product_tmpl_id = fields.Many2one('product.template', 'Product', readonly=True)
    categ_id = fields.Many2one('product.category', 'Product Category', readonly=True)
    nbr = fields.Integer('# of Lines', readonly=True)
    pricelist_id = fields.Many2one('product.pricelist', 'Pricelist', readonly=True)
    analytic_account_id = fields.Many2one('account.analytic.account', 'Analytic Account', readonly=True)
    team_id = fields.Many2one('crm.team', 'Sales Team', readonly=True, oldname='section_id')
    country_id = fields.Many2one('res.country', 'Customer Country', readonly=True)
    commercial_partner_id = fields.Many2one('res.partner', 'Customer Entity', readonly=True)
    state = fields.Selection([
        ('draft', 'Draft Quotation'),
        ('sent', 'Quotation Sent'),
        ('sale', 'Sales Order'),
        ('done', 'Sales Done'),
        ('open', 'Open'),
        ('in_payment', 'In Payment'),
        ('paid', 'Paid'),
        ('cancel', 'Cancelled'),
        ], string='Status', readonly=True)
    weight = fields.Float('Gross Weight', readonly=True)
    volume = fields.Float('Volume', readonly=True)

    discount = fields.Float('Discount %', readonly=True)
    discount_amount = fields.Float('Discount Amount', readonly=True)

    order_id = fields.Many2one('sale.order', 'Order #', readonly=True)
    document_type = fields.Selection([
        ('sale_order', 'Invoice'),
        ('pos_order', 'Pos Order'),
        ('refund', 'Credit Note'),
        ], string='Document Type', readonly=True)

    def _select_sales(self, fields={}):
        select_sales = """
            min(l.id) as id,
            l.product_id as product_id,
            t.uom_id as product_uom,
            sum(l.product_uom_qty / u.factor * u2.factor) as product_uom_qty,
            sum(l.qty_delivered / u.factor * u2.factor) as qty_delivered,
            sum(l.qty_invoiced / u.factor * u2.factor) as qty_invoiced,
            sum(l.qty_to_invoice / u.factor * u2.factor) as qty_to_invoice,
            sum(l.price_total / CASE COALESCE(s.currency_rate, 0) WHEN 0 THEN 1.0 ELSE s.currency_rate END) as price_total,
            sum(l.price_subtotal / CASE COALESCE(s.currency_rate, 0) WHEN 0 THEN 1.0 ELSE s.currency_rate END) as price_subtotal,
            sum(l.price_tax / CASE COALESCE(s.currency_rate, 0) WHEN 0 THEN 1.0 ELSE s.currency_rate END) as price_tax,
            sum(l.untaxed_amount_to_invoice / CASE COALESCE(s.currency_rate, 0) WHEN 0 THEN 1.0 ELSE s.currency_rate END) as untaxed_amount_to_invoice,
            sum(l.untaxed_amount_invoiced / CASE COALESCE(s.currency_rate, 0) WHEN 0 THEN 1.0 ELSE s.currency_rate END) as untaxed_amount_invoiced,
            count(*) as nbr,
            'sale_order' AS document_type,
            s.name as name,
            s.date_order as date,
            s.confirmation_date as confirmation_date,
            s.state as state,
            s.partner_id as partner_id,
            s.user_id as user_id,
            s.company_id as company_id,
            extract(epoch from avg(date_trunc('day',s.date_order)-date_trunc('day',s.create_date)))/(24*60*60)::decimal(16,2) as delay,
            t.categ_id as categ_id,
            s.pricelist_id as pricelist_id,
            s.analytic_account_id as analytic_account_id,
            s.team_id as team_id,
            p.product_tmpl_id,
            partner.country_id as country_id,
            partner.commercial_partner_id as commercial_partner_id,
            sum(p.weight * l.product_uom_qty / u.factor * u2.factor) as weight,
            sum(p.volume * l.product_uom_qty / u.factor * u2.factor) as volume,
            l.discount as discount,
            sum((l.price_unit * l.product_uom_qty * l.discount / 100.0 / CASE COALESCE(s.currency_rate, 0) WHEN 0 THEN 1.0 ELSE s.currency_rate END)) as discount_amount,
            s.id as order_id
        """

        for field in fields.values():
            select_sales += field
        return select_sales

    def _from_sales(self, from_clause=''):
        from_sales = """
            sale_order_line l
                  join sale_order s on (l.order_id=s.id)
                  join res_partner partner on s.partner_id = partner.id
                    left join product_product p on (l.product_id=p.id)
                        left join product_template t on (p.product_tmpl_id=t.id)
                left join uom_uom u on (u.id=l.product_uom)
                left join uom_uom u2 on (u2.id=t.uom_id)
                left join product_pricelist pp on (s.pricelist_id = pp.id)
            %s
        """ % from_clause
        return from_sales

    def _where_sales(self):
        where_sales = "WHERE l.product_id IS NOT NULL"
        return where_sales

    def _groupby_sales(self, groupby=''):
        groupby_sales = """
            l.product_id,
            l.order_id,
            t.uom_id,
            t.categ_id,
            s.name,
            s.date_order,
            s.confirmation_date,
            s.partner_id,
            s.user_id,
            s.state,
            s.company_id,
            s.pricelist_id,
            s.analytic_account_id,
            s.team_id,
            p.product_tmpl_id,
            partner.country_id,
            partner.commercial_partner_id,
            l.discount,
            s.id %s
        """ % (groupby)
        return groupby_sales

    def _select_refund(self, fields={}):
        select_refund = """
            min(ail.id) as id,
            ail.product_id as product_id,
            t.uom_id as product_uom,
            sum(-ail.quantity / u.factor * u2.factor) as product_uom_qty,
            sum(-ail.quantity / u.factor * u2.factor) as qty_delivered,
            sum(-ail.quantity / u.factor * u2.factor) as qty_invoiced,
            sum(0) as qty_to_invoice,
            sum(-ail.price_total) as price_total,
            sum(-ail.price_subtotal) as price_subtotal,
            sum(-(ail.price_total-ail.price_subtotal)) as price_tax,
            0 as untaxed_amount_to_invoice,
            sum(-ail.price_subtotal) as untaxed_amount_invoiced,
            count(*) as nbr,
            'refund' AS document_type,
            ai.name as name,
            to_timestamp(CONCAT(to_char(ai.date_invoice, 'dd-mm-YYYY'), ' 12:00:00'), 'dd-mm-YYYY HH24:MI:SS') AT TIME ZONE 'UTC' as date,
            to_timestamp(CONCAT(to_char(ai.date_invoice, 'dd-mm-YYYY'), ' 12:00:00'), 'dd-mm-YYYY HH24:MI:SS') AT TIME ZONE 'UTC' as confirmation_date,
            ai.state as state,
            ai.partner_id as partner_id,
            ai.user_id as user_id,
            ai.company_id as company_id,
            extract(epoch from avg(date_trunc('day',ai.date_invoice)-date_trunc('day',ai.create_date)))/(24*60*60)::decimal(16,2) as delay,
            t.categ_id as categ_id,
            NULL as pricelist_id,
            ail.account_analytic_id as analytic_account_id,
            ai.team_id as team_id,
            p.product_tmpl_id,
            ai_partner.country_id as country_id,
            ai_partner.commercial_partner_id as commercial_partner_id,
            sum(p.weight * ail.quantity / u.factor * u2.factor) as weight,
            sum(p.volume * ail.quantity / u.factor * u2.factor) as volume,
            ail.discount as discount,
            sum(ail.price_unit * ail.discount / 100.0) as discount_amount,
            NULL as order_id
        """

        for field in fields.keys():
            select_refund += ', NULL AS %s' % (field)
        return select_refund

    def _from_refund(self, from_clause=''):
        from_refund = """
            account_invoice_line ail
                  join account_invoice ai on (ail.invoice_id=ai.id)
                  join res_partner ai_partner on ai.partner_id = ai_partner.id
                    left join product_product p on (ail.product_id=p.id)
                        left join product_template t on (p.product_tmpl_id=t.id)
                left join uom_uom u on (u.id=ail.uom_id)
                left join uom_uom u2 on (u2.id=t.uom_id)
        """
        return from_refund

    def _where_refund(self):
        where_refund = """
            WHERE ail.account_id IS NOT NULL AND ai.type = 'out_refund'
        """
        return where_refund

    def _groupby_refund(self, groupby=''):
        groupby_refund = """
            ail.product_id,
            ail.invoice_id,
            t.uom_id,
            t.categ_id,
            ai.name,
            ai.date_invoice,
            ai.partner_id,
            ai.user_id,
            ai.state,
            ai.company_id,
            ail.account_analytic_id,
            ai.team_id,
            p.product_tmpl_id,
            ai_partner.country_id,
            ai_partner.commercial_partner_id,
            ail.discount,
            ai.id
        """
        return groupby_refund

    def _query(self, with_clause='', fields={}, groupby='', from_clause=''):
        with_ = ("WITH %s" % with_clause) if with_clause else ""
        select_ = self._select_sales(fields)
        from_ = self._from_sales(from_clause)
        where_ = self._where_sales()
        groupby_ = self._groupby_sales(groupby)

        select_refund = self._select_refund(fields)
        from_refund = self._from_refund(from_clause)
        where_refund = self._where_refund()
        groupby_refund = self._groupby_refund(groupby)

        sql_invoice = '(SELECT %s FROM %s %s GROUP BY %s)' % (select_, from_, where_, groupby_)
        sql_refund = '(SELECT %s FROM %s %s GROUP BY %s)' % (select_refund, from_refund, where_refund, groupby_refund)

        return '%s (%s UNION ALL %s)' % (with_, sql_invoice, sql_refund)

    @api.model_cr
    def init(self):
        # self._table = sale_report
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute("""CREATE or REPLACE VIEW %s as (%s)""" % (self._table, self._query()))

class SaleOrderReportProforma(models.AbstractModel):
    _name = 'report.sale.report_saleproforma'
    _description = 'Proforma Report'

    @api.multi
    def _get_report_values(self, docids, data=None):
        docs = self.env['sale.order'].browse(docids)
        return {
            'doc_ids': docs.ids,
            'doc_model': 'sale.order',
            'docs': docs,
            'proforma': True
        }
