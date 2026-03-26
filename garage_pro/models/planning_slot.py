"""Créneau planning atelier — lie un OR, un poste et un technicien."""

from odoo import api, fields, models
from odoo.exceptions import ValidationError


class GaragePlanningSlot(models.Model):
    """Créneau de planning liant un OR, un poste, un technicien et un horaire."""

    _name = 'garage.planning.slot'
    _description = 'Créneau planning atelier'
    _inherit = ['mail.thread']
    _order = 'start_datetime'

    # === LIENS ===
    repair_order_id = fields.Many2one(
        'garage.repair.order',
        string="Ordre de réparation",
        required=True,
        ondelete='cascade',
    )
    post_id = fields.Many2one(
        'garage.workshop.post',
        string="Poste de travail",
        required=True,
    )
    technician_id = fields.Many2one(
        'hr.employee',
        string="Technicien",
        domain="[('is_garage_technician', '=', True)]",
    )
    operation_type = fields.Selection([
        ('body', 'Carrosserie'),
        ('paint_prep', 'Préparation peinture'),
        ('paint_booth', 'Cabine peinture'),
        ('mechanic', 'Mécanique'),
        ('reassembly', 'Remontage'),
        ('qc', 'Contrôle qualité'),
        ('wash', 'Nettoyage'),
    ], string="Type d'opération")

    # === HORAIRE ===
    start_datetime = fields.Datetime(string="Début", required=True)
    end_datetime = fields.Datetime(string="Fin", required=True)
    duration_hours = fields.Float(
        string="Durée (h)",
        compute='_compute_duration',
        store=True,
    )

    # === STATUT ===
    state = fields.Selection([
        ('planned', 'Planifié'),
        ('in_progress', 'En cours'),
        ('done', 'Terminé'),
        ('cancelled', 'Annulé'),
    ], default='planned', tracking=True, string="Statut")

    # === CHAMPS RELATIONNELS (pour vues) ===
    vehicle_plate = fields.Char(
        related='repair_order_id.vehicle_id.license_plate',
        store=True,
        string="Plaque",
    )
    customer_name = fields.Char(
        related='repair_order_id.customer_id.name',
        store=True,
        string="Client",
    )
    color = fields.Integer(related='post_id.color')

    notes = fields.Text(string="Notes")

    # ------------------------------------------------------------------
    # Compute
    # ------------------------------------------------------------------

    @api.depends('start_datetime', 'end_datetime')
    def _compute_duration(self):
        for rec in self:
            if rec.start_datetime and rec.end_datetime:
                delta = rec.end_datetime - rec.start_datetime
                rec.duration_hours = delta.total_seconds() / 3600.0
            else:
                rec.duration_hours = 0.0

    # ------------------------------------------------------------------
    # Contraintes
    # ------------------------------------------------------------------

    @api.constrains('start_datetime', 'end_datetime')
    def _check_dates(self):
        for rec in self:
            if rec.start_datetime and rec.end_datetime and rec.end_datetime <= rec.start_datetime:
                raise ValidationError("La date de fin doit être postérieure à la date de début.")

    @api.constrains('post_id', 'start_datetime', 'end_datetime')
    def _check_no_overlap(self):
        """Vérifie qu'il n'y a pas de chevauchement sur un poste à capacité 1."""
        for rec in self:
            if rec.post_id.capacity <= 1:
                overlapping = self.search([
                    ('post_id', '=', rec.post_id.id),
                    ('id', '!=', rec.id),
                    ('state', '!=', 'cancelled'),
                    ('start_datetime', '<', rec.end_datetime),
                    ('end_datetime', '>', rec.start_datetime),
                ])
                if overlapping:
                    raise ValidationError(
                        "Le poste « %s » est déjà occupé sur ce créneau par l'OR %s."
                        % (rec.post_id.name, overlapping[0].repair_order_id.name)
                    )

    # ------------------------------------------------------------------
    # Actions workflow
    # ------------------------------------------------------------------

    def action_start(self):
        """Planifié → En cours."""
        self.write({'state': 'in_progress'})

    def action_done(self):
        """En cours → Terminé."""
        self.write({'state': 'done'})

    def action_cancel(self):
        """Annuler le créneau."""
        self.write({'state': 'cancelled'})

    def action_reset(self):
        """Remettre en planifié."""
        self.write({'state': 'planned'})
