"""Poste de travail atelier — ressource planifiable."""

from odoo import fields, models


class GarageWorkshopPost(models.Model):
    """Chaque poste physique de l'atelier (pont, cabine, marbre…)."""

    _name = 'garage.workshop.post'
    _description = 'Poste de travail atelier'
    _inherit = ['mail.thread']
    _order = 'sequence, name'

    name = fields.Char(
        string="Nom du poste",
        required=True,
        tracking=True,
    )
    code = fields.Char(string="Code court")
    sequence = fields.Integer(default=10)
    post_type = fields.Selection([
        ('body_lift', 'Pont carrosserie'),
        ('mech_lift', 'Pont mécanique'),
        ('frame_bench', 'Marbre de redressage'),
        ('paint_booth', 'Cabine de peinture'),
        ('paint_prep', 'Zone préparation peinture'),
        ('welding', 'Poste de soudure'),
        ('diag', 'Poste diagnostic'),
        ('wash', 'Zone lavage'),
        ('general', 'Zone polyvalente'),
    ], string="Type de poste", required=True, tracking=True)
    capacity = fields.Integer(
        string="Capacité simultanée",
        default=1,
        help="Nombre de véhicules simultanés (1 pour un pont, 2+ pour une zone ouverte)",
    )
    is_bottleneck = fields.Boolean(
        string="Goulot d'étranglement",
        help="Si coché, ce poste est priorisé dans la planification (ex : cabine peinture)",
    )
    active = fields.Boolean(default=True)
    color = fields.Integer(string="Couleur (Kanban)")
    notes = fields.Text(string="Notes (équipement, limitations)")

    planning_slot_ids = fields.One2many(
        'garage.planning.slot',
        'post_id',
        string="Créneaux planifiés",
    )
