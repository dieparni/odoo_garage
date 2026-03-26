"""Plan d'entretien véhicule — préconisations constructeur."""

from dateutil.relativedelta import relativedelta

from odoo import api, fields, models


class GarageMaintenancePlan(models.Model):
    """Plan d'entretien global pour un véhicule."""

    _name = 'garage.maintenance.plan'
    _description = "Plan d'entretien véhicule"
    _order = 'vehicle_id'

    vehicle_id = fields.Many2one(
        'fleet.vehicle',
        string="Véhicule",
        required=True,
    )
    name = fields.Char(
        string="Nom",
        compute='_compute_name',
        store=True,
    )
    item_ids = fields.One2many(
        'garage.maintenance.plan.item',
        'plan_id',
        string="Points d'entretien",
    )
    notes = fields.Text(string="Notes constructeur")

    @api.depends('vehicle_id', 'vehicle_id.name')
    def _compute_name(self):
        for rec in self:
            if rec.vehicle_id:
                rec.name = f"Plan entretien — {rec.vehicle_id.name}"
            else:
                rec.name = "Plan entretien"


class GarageMaintenancePlanItem(models.Model):
    """Point individuel du plan d'entretien."""

    _name = 'garage.maintenance.plan.item'
    _description = "Point du plan d'entretien"
    _order = 'next_due_km, next_due_date'

    plan_id = fields.Many2one(
        'garage.maintenance.plan',
        ondelete='cascade',
        required=True,
    )
    name = fields.Char(string="Opération", required=True)
    interval_km = fields.Integer(string="Intervalle (km)", help="Ex: 15000")
    interval_months = fields.Integer(string="Intervalle (mois)", help="Ex: 12")
    last_done_km = fields.Integer(string="Dernier entretien (km)")
    last_done_date = fields.Date(string="Dernier entretien (date)")
    next_due_km = fields.Integer(
        string="Prochain (km)",
        compute='_compute_next',
        store=True,
    )
    next_due_date = fields.Date(
        string="Prochain (date)",
        compute='_compute_next',
        store=True,
    )
    is_overdue = fields.Boolean(
        string="En retard",
        compute='_compute_overdue',
    )

    @api.depends('last_done_km', 'interval_km', 'last_done_date',
                 'interval_months')
    def _compute_next(self):
        for rec in self:
            if rec.interval_km:
                rec.next_due_km = (rec.last_done_km or 0) + rec.interval_km
            else:
                rec.next_due_km = 0
            if rec.interval_months:
                base_date = rec.last_done_date or fields.Date.today()
                rec.next_due_date = (
                    base_date + relativedelta(months=rec.interval_months)
                )
            else:
                rec.next_due_date = False

    @api.depends('next_due_km', 'next_due_date')
    def _compute_overdue(self):
        today = fields.Date.today()
        for rec in self:
            overdue = False
            if rec.next_due_date and rec.next_due_date < today:
                overdue = True
            rec.is_overdue = overdue

    # ------------------------------------------------------------------
    # Crons
    # ------------------------------------------------------------------

    @api.model
    def cron_maintenance_alerts(self):
        """Alerte : entretien à venir dans les 30 prochains jours."""
        today = fields.Date.today()
        limit = today + relativedelta(days=30)
        items = self.search([
            ('next_due_date', '!=', False),
            ('next_due_date', '<=', limit),
            ('next_due_date', '>=', today),
        ])
        for item in items:
            vehicle = item.plan_id.vehicle_id
            if vehicle:
                vehicle.activity_schedule(
                    'mail.mail_activity_data_todo',
                    date_deadline=item.next_due_date,
                    summary="Entretien à planifier : %s — %s" % (
                        item.name, vehicle.license_plate
                    ),
                )
