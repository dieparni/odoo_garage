"""Opérations de peinture liées aux ordres de réparation."""

from odoo import api, fields, models
from odoo.exceptions import UserError

from .constants import DAMAGE_ZONES


class GaragePaintOperation(models.Model):
    """Opération de peinture avec suivi cabine et consommation."""

    _name = 'garage.paint.operation'
    _description = 'Opération de peinture'
    _inherit = ['mail.thread']
    _order = 'repair_order_id, id'

    repair_order_id = fields.Many2one(
        'garage.repair.order',
        string="Ordre de réparation",
        required=True,
        ondelete='cascade',
    )
    bodywork_operation_id = fields.Many2one(
        'garage.bodywork.operation',
        string="Opération carrosserie liée",
    )

    name = fields.Char(string="Description", required=True)
    operation_type = fields.Selection([
        ('primer', 'Apprêtage'),
        ('sanding', 'Ponçage'),
        ('base_coat', 'Application base'),
        ('clear_coat', 'Vernis'),
        ('blend', 'Raccord (dégradé)'),
        ('full_panel', 'Peinture complète panneau'),
        ('full_vehicle', 'Peinture complète véhicule'),
        ('touch_up', 'Retouche'),
        ('polish', 'Polissage / lustrage'),
    ], string="Type d'opération", required=True)

    zone = fields.Selection(
        DAMAGE_ZONES,
        string="Zone peinte",
    )

    # === TEINTE ===
    paint_code = fields.Char(
        string="Code peinture",
        related='repair_order_id.vehicle_id.paint_code',
    )
    formula_id = fields.Many2one(
        'garage.paint.formula',
        string="Formule teinte utilisée",
    )
    paint_system_id = fields.Many2one(
        'garage.paint.system',
        string="Système peinture",
        related='repair_order_id.vehicle_id.paint_system_id',
    )

    # === CABINE ===
    booth_slot_start = fields.Datetime(string="Créneau cabine début")
    booth_slot_end = fields.Datetime(string="Créneau cabine fin")
    booth_temperature = fields.Float(string="Température cabine (°C)")
    booth_humidity = fields.Float(string="Hygrométrie (%)")

    # === CONSOMMATION PRODUITS ===
    product_consumption_ids = fields.One2many(
        'garage.paint.consumption',
        'paint_operation_id',
        string="Consommation produits",
    )
    total_product_cost = fields.Monetary(
        string="Coût produits total",
        compute='_compute_total_cost',
        store=True,
        currency_field='currency_id',
    )

    # === TEMPS ===
    allocated_time = fields.Float(string="Temps alloué (h)")
    actual_time = fields.Float(string="Temps réel (h)")
    technician_id = fields.Many2one('hr.employee', string="Peintre")

    state = fields.Selection([
        ('waiting', 'En attente carrosserie'),
        ('prep', 'Préparation'),
        ('booth', 'En cabine'),
        ('drying', 'Séchage'),
        ('polish', 'Polissage'),
        ('done', 'Terminé'),
        ('rework', 'Reprise'),
    ], default='waiting', tracking=True, string="Statut")

    quality_notes = fields.Text(string="Notes qualité peinture")
    currency_id = fields.Many2one(
        'res.currency',
        default=lambda self: self.env.company.currency_id,
    )

    # ------------------------------------------------------------------
    # Compute
    # ------------------------------------------------------------------

    @api.depends('product_consumption_ids.total_cost')
    def _compute_total_cost(self):
        for rec in self:
            rec.total_product_cost = sum(
                rec.product_consumption_ids.mapped('total_cost')
            )

    # ------------------------------------------------------------------
    # Workflow
    # ------------------------------------------------------------------

    def action_start_prep(self):
        """En attente → Préparation. Vérifie l'habilitation VE si nécessaire."""
        self._check_ev_certification()
        self.write({'state': 'prep'})

    def _check_ev_certification(self):
        """Vérifie que le technicien a l'habilitation VE si le véhicule est électrique."""
        for rec in self:
            vehicle = rec.repair_order_id.vehicle_id
            if (vehicle.is_electric
                    and rec.technician_id
                    and not rec.technician_id.has_ev_certification):
                raise UserError(
                    "Le technicien %s n'a pas l'habilitation véhicule "
                    "électrique requise pour intervenir sur %s."
                    % (rec.technician_id.name, vehicle.license_plate)
                )

    def action_enter_booth(self):
        """Préparation → En cabine."""
        self.write({'state': 'booth'})

    def action_drying(self):
        """En cabine → Séchage."""
        self.write({'state': 'drying'})

    def action_polish(self):
        """Séchage → Polissage."""
        self.write({'state': 'polish'})

    def action_done(self):
        """Polissage → Terminé."""
        self.write({'state': 'done'})

    def action_rework(self):
        """Reprise qualité → retour en préparation."""
        self.write({'state': 'rework'})

    def action_restart(self):
        """Reprise → Préparation."""
        self.write({'state': 'prep'})
