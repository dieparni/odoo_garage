"""Rapport CA garage — vue SQL pour le reporting."""

from odoo import fields, models, tools


class GarageReportRevenue(models.Model):
    """Vue SQL agrégée du chiffre d'affaires par activité et période."""

    _name = 'garage.report.revenue'
    _description = 'Rapport CA garage'
    _auto = False
    _order = 'date desc'
    _rec_name = 'date'

    date = fields.Date(string="Date", readonly=True)
    month = fields.Char(string="Mois", readonly=True)
    year = fields.Char(string="Année", readonly=True)
    activity_type = fields.Selection([
        ('bodywork', 'Carrosserie'),
        ('paint', 'Peinture'),
        ('mechanic', 'Mécanique'),
        ('parts', 'Pièces'),
        ('subcontract', 'Sous-traitance'),
    ], string="Activité", readonly=True)
    revenue = fields.Monetary(string="CA HT", readonly=True, currency_field='currency_id')
    cost = fields.Monetary(string="Coût", readonly=True, currency_field='currency_id')
    margin = fields.Monetary(string="Marge", readonly=True, currency_field='currency_id')
    margin_rate = fields.Float(string="Taux marge (%)", readonly=True)
    ro_count = fields.Integer(string="Nombre d'OR", readonly=True)

    # === Dimensions d'analyse ===
    vehicle_id = fields.Many2one('fleet.vehicle', string="Véhicule", readonly=True)
    customer_id = fields.Many2one('res.partner', string="Client", readonly=True)
    repair_order_id = fields.Many2one('garage.repair.order', string="OR", readonly=True)
    company_id = fields.Many2one('res.company', string="Société", readonly=True)
    currency_id = fields.Many2one('res.currency', string="Devise", readonly=True)
    state = fields.Selection([
        ('delivered', 'Livré'),
        ('invoiced', 'Facturé'),
    ], string="Statut OR", readonly=True)

    def init(self):
        """Crée la vue SQL pour le reporting CA."""
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute("""
            CREATE OR REPLACE VIEW %s AS (
                SELECT
                    MIN(rol.id) AS id,
                    ro.actual_end_date::date AS date,
                    to_char(ro.actual_end_date, 'YYYY-MM') AS month,
                    to_char(ro.actual_end_date, 'YYYY') AS year,
                    CASE
                        WHEN rol.line_type = 'labor_body' THEN 'bodywork'
                        WHEN rol.line_type IN ('labor_paint', 'paint_material') THEN 'paint'
                        WHEN rol.line_type = 'labor_mech' THEN 'mechanic'
                        WHEN rol.line_type = 'parts' THEN 'parts'
                        WHEN rol.line_type = 'subcontract' THEN 'subcontract'
                        ELSE 'mechanic'
                    END AS activity_type,
                    SUM(rol.amount_total) AS revenue,
                    0 AS cost,
                    SUM(rol.amount_total) AS margin,
                    CASE
                        WHEN SUM(rol.amount_total) > 0 THEN 100.0
                        ELSE 0
                    END AS margin_rate,
                    COUNT(DISTINCT ro.id) AS ro_count,
                    ro.vehicle_id,
                    ro.customer_id,
                    ro.id AS repair_order_id,
                    ro.company_id,
                    ro.currency_id,
                    ro.state
                FROM garage_repair_order_line rol
                JOIN garage_repair_order ro ON ro.id = rol.repair_order_id
                WHERE ro.state IN ('delivered', 'invoiced')
                  AND ro.actual_end_date IS NOT NULL
                GROUP BY
                    ro.actual_end_date::date,
                    to_char(ro.actual_end_date, 'YYYY-MM'),
                    to_char(ro.actual_end_date, 'YYYY'),
                    CASE
                        WHEN rol.line_type = 'labor_body' THEN 'bodywork'
                        WHEN rol.line_type IN ('labor_paint', 'paint_material') THEN 'paint'
                        WHEN rol.line_type = 'labor_mech' THEN 'mechanic'
                        WHEN rol.line_type = 'parts' THEN 'parts'
                        WHEN rol.line_type = 'subcontract' THEN 'subcontract'
                        ELSE 'mechanic'
                    END,
                    ro.vehicle_id,
                    ro.customer_id,
                    ro.id,
                    ro.company_id,
                    ro.currency_id,
                    ro.state
            )
        """ % self._table)


class GarageReportActivity(models.Model):
    """Vue SQL agrégée de l'activité atelier (KPIs opérationnels)."""

    _name = 'garage.report.activity'
    _description = 'Rapport activité atelier'
    _auto = False
    _order = 'date desc'
    _rec_name = 'date'

    date = fields.Date(string="Date", readonly=True)
    month = fields.Char(string="Mois", readonly=True)
    year = fields.Char(string="Année", readonly=True)

    ro_count = fields.Integer(string="Nombre d'OR", readonly=True)
    total_allocated_hours = fields.Float(string="Heures allouées", readonly=True)
    total_worked_hours = fields.Float(string="Heures travaillées", readonly=True)
    productivity_rate = fields.Float(string="Taux productivité (%)", readonly=True)
    avg_repair_days = fields.Float(string="Délai moyen réparation (j)", readonly=True)
    amount_untaxed = fields.Monetary(string="CA HT", readonly=True, currency_field='currency_id')

    company_id = fields.Many2one('res.company', string="Société", readonly=True)
    currency_id = fields.Many2one('res.currency', string="Devise", readonly=True)

    def init(self):
        """Crée la vue SQL pour les KPIs activité atelier."""
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute("""
            CREATE OR REPLACE VIEW %s AS (
                SELECT
                    MIN(ro.id) AS id,
                    ro.actual_end_date::date AS date,
                    to_char(ro.actual_end_date, 'YYYY-MM') AS month,
                    to_char(ro.actual_end_date, 'YYYY') AS year,
                    COUNT(ro.id) AS ro_count,
                    SUM(ro.total_allocated_hours) AS total_allocated_hours,
                    SUM(ro.total_worked_hours) AS total_worked_hours,
                    CASE
                        WHEN SUM(ro.total_allocated_hours) > 0
                        THEN SUM(ro.total_worked_hours) / SUM(ro.total_allocated_hours) * 100
                        ELSE 0
                    END AS productivity_rate,
                    AVG(
                        EXTRACT(EPOCH FROM (ro.actual_end_date - ro.actual_start_date))
                        / 86400.0
                    ) AS avg_repair_days,
                    SUM(ro.amount_untaxed) AS amount_untaxed,
                    ro.company_id,
                    ro.currency_id
                FROM garage_repair_order ro
                WHERE ro.state IN ('delivered', 'invoiced')
                  AND ro.actual_end_date IS NOT NULL
                  AND ro.actual_start_date IS NOT NULL
                GROUP BY
                    ro.actual_end_date::date,
                    to_char(ro.actual_end_date, 'YYYY-MM'),
                    to_char(ro.actual_end_date, 'YYYY'),
                    ro.company_id,
                    ro.currency_id
            )
        """ % self._table)
