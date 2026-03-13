from odoo import fields, models, tools


class BeerHlSalesReport(models.Model):
    _name = 'x_beer_hl_sales_report'
    _description = 'Beer hL Sales Report'
    _auto = False
    _rec_name = 'product_id'
    _order = 'date desc, id desc'

    date = fields.Date(string='Date', readonly=True)
    partner_id = fields.Many2one('res.partner', string='Customer', readonly=True)
    product_id = fields.Many2one('product.product', string='Product', readonly=True)
    product_tmpl_id = fields.Many2one('product.template', string='Product Template', readonly=True)
    company_id = fields.Many2one('res.company', string='Company', readonly=True)
    source = fields.Selection([
        ('invoice', 'Invoice'),
        ('pos', 'POS'),
    ], string='Source', readonly=True)
    quantity = fields.Float(string='Quantity', readonly=True)
    hl_per_unit = fields.Float(string='hL per Unit', readonly=True, digits=(16, 6))
    hl_total = fields.Float(string='Sold hL', readonly=True, digits=(16, 6))
    amount_untaxed = fields.Float(string='Untaxed Amount', readonly=True)

    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute(f"""
            CREATE OR REPLACE VIEW {self._table} AS (
                WITH invoice_lines AS (
                    SELECT
                        aml.id AS source_line_id,
                        am.invoice_date::date AS date,
                        aml.partner_id AS partner_id,
                        aml.product_id AS product_id,
                        pp.product_tmpl_id AS product_tmpl_id,
                        aml.company_id AS company_id,
                        'invoice'::varchar AS source,
                        CASE
                            WHEN am.move_type = 'out_refund' THEN -aml.quantity
                            ELSE aml.quantity
                        END AS quantity,
                        COALESCE(pt.x_studio_inhalt_in_hl, 0.0) AS hl_per_unit,
                        CASE
                            WHEN am.move_type = 'out_refund' THEN -aml.quantity
                            ELSE aml.quantity
                        END * COALESCE(pt.x_studio_inhalt_in_hl, 0.0) AS hl_total,
                        CASE
                            WHEN am.move_type = 'out_refund' THEN -aml.price_subtotal
                            ELSE aml.price_subtotal
                        END AS amount_untaxed
                    FROM account_move_line aml
                    JOIN account_move am ON am.id = aml.move_id
                    JOIN product_product pp ON pp.id = aml.product_id
                    JOIN product_template pt ON pt.id = pp.product_tmpl_id
                    WHERE am.state = 'posted'
                      AND am.move_type IN ('out_invoice', 'out_refund')
                      AND aml.display_type IS NULL
                      AND aml.product_id IS NOT NULL
                      AND COALESCE(pt.x_studio_inhalt_in_hl, 0.0) <> 0.0
                ),
                pos_lines AS (
                    SELECT
                        pol.id AS source_line_id,
                        po.date_order::date AS date,
                        po.partner_id AS partner_id,
                        pol.product_id AS product_id,
                        pp.product_tmpl_id AS product_tmpl_id,
                        po.company_id AS company_id,
                        'pos'::varchar AS source,
                        pol.qty AS quantity,
                        COALESCE(pt.x_studio_inhalt_in_hl, 0.0) AS hl_per_unit,
                        pol.qty * COALESCE(pt.x_studio_inhalt_in_hl, 0.0) AS hl_total,
                        pol.price_subtotal AS amount_untaxed
                    FROM pos_order_line pol
                    JOIN pos_order po ON po.id = pol.order_id
                    JOIN product_product pp ON pp.id = pol.product_id
                    JOIN product_template pt ON pt.id = pp.product_tmpl_id
                    WHERE po.state IN ('paid', 'done', 'invoiced')
                      AND pol.product_id IS NOT NULL
                      AND COALESCE(pt.x_studio_inhalt_in_hl, 0.0) <> 0.0
                ),
                combined AS (
                    SELECT * FROM invoice_lines
                    UNION ALL
                    SELECT * FROM pos_lines
                )
                SELECT
                    row_number() OVER (ORDER BY date, source, source_line_id) AS id,
                    date,
                    partner_id,
                    product_id,
                    product_tmpl_id,
                    company_id,
                    source,
                    quantity,
                    hl_per_unit,
                    hl_total,
                    amount_untaxed
                FROM combined
            )
        """)
