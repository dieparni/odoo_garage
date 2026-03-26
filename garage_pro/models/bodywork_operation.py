"""Opérations de carrosserie liées aux ordres de réparation."""

from odoo import api, fields, models
from odoo.exceptions import UserError

from .constants import DAMAGE_ZONES, DAMAGE_LEVELS


class GarageBodyworkOperation(models.Model):
    """Opération de carrosserie détaillée sur un OR."""

    _name = 'garage.bodywork.operation'
    _description = 'Opération de carrosserie'
    _inherit = ['mail.thread']
    _order = 'repair_order_id, id'

    repair_order_id = fields.Many2one(
        'garage.repair.order',
        string="Ordre de réparation",
        required=True,
        ondelete='cascade',
    )
    ro_line_id = fields.Many2one(
        'garage.repair.order.line',
        string="Ligne OR",
    )

    name = fields.Char(string="Description", required=True)
    operation_type = fields.Selection([
        ('straighten', 'Redressage'),
        ('replace', 'Remplacement panneau'),
        ('weld', 'Soudure'),
        ('fill', 'Masticage / ponçage'),
        ('frame', 'Mise sur marbre (châssis)'),
        ('glass', 'Remplacement vitrage'),
        ('trim', 'Garniture / habillage'),
        ('pdr', 'Débosselage sans peinture (PDR)'),
        ('disassembly', 'Démontage'),
        ('reassembly', 'Remontage'),
        ('other', 'Autre'),
    ], string="Type d'opération", required=True)

    damage_zone = fields.Selection(
        DAMAGE_ZONES,
        string="Zone",
    )
    damage_level = fields.Selection(
        DAMAGE_LEVELS,
        string="Niveau de dommage",
    )

    allocated_time = fields.Float(string="Temps alloué (h)")
    actual_time = fields.Float(string="Temps réel (h)")
    technician_id = fields.Many2one('hr.employee', string="Carrossier")

    state = fields.Selection([
        ('todo', 'À faire'),
        ('in_progress', 'En cours'),
        ('done', 'Terminé'),
        ('blocked', 'Bloqué'),
    ], default='todo', tracking=True, string="Statut")
    blocked_reason = fields.Char(string="Raison blocage")

    requires_painting = fields.Boolean(
        string="Nécessite peinture",
        default=True,
        help="Si coché, génère automatiquement une opération peinture liée",
    )
    paint_operation_id = fields.Many2one(
        'garage.paint.operation',
        string="Opération peinture liée",
    )

    photo_before_ids = fields.Many2many(
        'ir.attachment',
        'bodywork_photo_before_rel',
        'bodywork_id',
        'attachment_id',
        string="Photos avant",
    )
    photo_after_ids = fields.Many2many(
        'ir.attachment',
        'bodywork_photo_after_rel',
        'bodywork_id',
        'attachment_id',
        string="Photos après",
    )
    notes = fields.Text(string="Notes techniques")

    # ------------------------------------------------------------------
    # Workflow
    # ------------------------------------------------------------------

    def action_start(self):
        """À faire → En cours. Vérifie l'habilitation VE si nécessaire."""
        self._check_ev_certification()
        self.write({'state': 'in_progress'})

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

    def action_done(self):
        """En cours → Terminé. Crée l'opération peinture liée si nécessaire."""
        for rec in self:
            rec.state = 'done'
            if rec.requires_painting and not rec.paint_operation_id:
                paint_op = self.env['garage.paint.operation'].create({
                    'repair_order_id': rec.repair_order_id.id,
                    'bodywork_operation_id': rec.id,
                    'name': f"Peinture — {rec.name}",
                    'operation_type': 'full_panel',
                    'zone': rec.damage_zone,
                    'state': 'waiting',
                })
                rec.paint_operation_id = paint_op

    def action_block(self):
        """Bloquer l'opération."""
        self.write({'state': 'blocked'})

    def action_unblock(self):
        """Débloquer → En cours."""
        self.write({'state': 'in_progress', 'blocked_reason': False})
