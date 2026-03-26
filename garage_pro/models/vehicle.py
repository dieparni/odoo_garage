"""Extension du modèle fleet.vehicle avec les champs spécifiques garage."""

import re

from dateutil.relativedelta import relativedelta

from odoo import api, fields, models
from odoo.exceptions import ValidationError


class GarageVehicle(models.Model):
    """Extension fleet.vehicle pour gestion atelier carrosserie/peinture/mécanique."""

    _inherit = 'fleet.vehicle'

    # === IDENTIFICATION ===
    # vin_sn existe déjà dans fleet.vehicle — on l'utilise comme VIN
    first_registration_date = fields.Date(
        string="Date 1ère immatriculation",
        tracking=True,
    )
    registration_country_id = fields.Many2one(
        'res.country',
        string="Pays d'immatriculation",
    )
    garage_ref = fields.Char(
        string="Référence garage",
        readonly=True,
        copy=False,
        default='Nouveau',
    )

    # === CARROSSERIE / PEINTURE ===
    paint_code = fields.Char(
        string="Code peinture constructeur",
        help="Code couleur fabricant (ex: LY9T, 475, etc.)",
        tracking=True,
    )
    paint_color_name = fields.Char(
        string="Nom de la teinte",
        help="Nom commercial de la couleur (ex: Noir Mythic, Blanc Glacier)",
    )
    paint_system_id = fields.Many2one(
        'garage.paint.system',
        string="Système peinture",
        help="Fabricant peinture utilisé (Standox, Sikkens, PPG...)",
    )
    body_type = fields.Selection([
        ('sedan', 'Berline'),
        ('break', 'Break'),
        ('suv', 'SUV / Crossover'),
        ('coupe', 'Coupé'),
        ('cabriolet', 'Cabriolet'),
        ('monospace', 'Monospace'),
        ('utilitaire', 'Utilitaire'),
        ('pickup', 'Pick-up'),
        ('citadine', 'Citadine'),
        ('other', 'Autre'),
    ], string="Type de carrosserie")

    # === MÉCANIQUE ===
    engine_code = fields.Char(string="Code moteur")
    engine_displacement = fields.Integer(string="Cylindrée (cm³)")
    power_kw = fields.Integer(string="Puissance (kW)")
    power_cv = fields.Integer(
        string="Puissance (CV)",
        compute='_compute_power_cv',
        store=True,
    )
    transmission_type = fields.Selection([
        ('manual', 'Manuelle'),
        ('automatic', 'Automatique'),
        ('semi_auto', 'Semi-automatique'),
        ('cvt', 'CVT'),
    ], string="Boîte de vitesses")
    drive_type = fields.Selection([
        ('fwd', 'Traction (FWD)'),
        ('rwd', 'Propulsion (RWD)'),
        ('awd', 'Intégrale (AWD)'),
        ('4wd', '4x4 (4WD)'),
    ], string="Type de transmission")

    # === ÉLECTRIQUE / HYBRIDE ===
    is_electric = fields.Boolean(
        string="Véhicule électrique/hybride",
        compute='_compute_is_electric',
        store=True,
    )
    battery_capacity_kwh = fields.Float(string="Capacité batterie (kWh)")
    charge_connector_type = fields.Selection([
        ('type1', 'Type 1 (J1772)'),
        ('type2', 'Type 2 (Mennekes)'),
        ('ccs', 'CCS Combo'),
        ('chademo', 'CHAdeMO'),
        ('tesla', 'Tesla'),
    ], string="Type de connecteur")

    # === CONTRÔLE TECHNIQUE ===
    ct_last_date = fields.Date(string="Dernier contrôle technique")
    ct_next_date = fields.Date(
        string="Prochain contrôle technique",
        compute='_compute_ct_next',
        store=True,
    )
    ct_result = fields.Selection([
        ('pass', 'Favorable'),
        ('pass_remarks', 'Favorable avec remarques'),
        ('fail', 'Défavorable'),
        ('dangerous', 'Dangereux'),
    ], string="Résultat dernier CT")

    # === GARANTIE ===
    warranty_end_date = fields.Date(string="Fin de garantie constructeur")
    is_under_warranty = fields.Boolean(
        string="Sous garantie",
        compute='_compute_warranty',
        store=True,
    )

    # === PROPRIÉTÉ ===
    ownership_type = fields.Selection([
        ('private', 'Propriété privée'),
        ('leasing', 'Leasing'),
        ('lld', 'Location longue durée'),
        ('fleet', 'Flotte entreprise'),
        ('rental', 'Location courte durée'),
    ], string="Type de propriété", default='private')
    leasing_company_id = fields.Many2one(
        'res.partner',
        string="Société de leasing",
        domain="[('is_leasing_company', '=', True)]",
    )
    owner_id = fields.Many2one(
        'res.partner',
        string="Propriétaire réel",
        help="Différent du conducteur si leasing ou flotte",
        tracking=True,
    )

    # === NOTES ===
    internal_notes = fields.Html(string="Notes internes")

    _sql_constraints = [
        ('vin_sn_unique', 'UNIQUE(vin_sn)',
         'Ce numéro VIN/châssis existe déjà dans le système.'),
    ]

    # ------------------------------------------------------------------
    # Compute
    # ------------------------------------------------------------------

    @api.depends('power_kw')
    def _compute_power_cv(self):
        """Conversion kW → CV (1 kW ≈ 1.36 CV)."""
        for rec in self:
            rec.power_cv = round(rec.power_kw * 1.36) if rec.power_kw else 0

    @api.depends('fuel_type')
    def _compute_is_electric(self):
        """Détecte les véhicules électriques ou hybrides rechargeables."""
        electric_types = ('electric', 'full_hybrid', 'plug_in_hybrid_diesel',
                          'plug_in_hybrid_gasoline')
        for rec in self:
            rec.is_electric = rec.fuel_type in electric_types

    @api.depends('ct_last_date')
    def _compute_ct_next(self):
        """Prochain CT = dernier CT + 1 an (règle BE/LU simplifiée)."""
        for rec in self:
            if rec.ct_last_date:
                rec.ct_next_date = rec.ct_last_date + relativedelta(years=1)
            else:
                rec.ct_next_date = False

    @api.depends('warranty_end_date')
    def _compute_warranty(self):
        """Vérifie si le véhicule est encore sous garantie constructeur."""
        today = fields.Date.today()
        for rec in self:
            rec.is_under_warranty = bool(
                rec.warranty_end_date and rec.warranty_end_date >= today
            )

    # ------------------------------------------------------------------
    # Contraintes
    # ------------------------------------------------------------------

    @api.constrains('vin_sn')
    def _check_vin(self):
        """Validation format VIN : 17 caractères alphanumériques, pas de I, O, Q."""
        for rec in self:
            if rec.vin_sn:
                vin = rec.vin_sn.strip().upper()
                if len(vin) != 17:
                    raise ValidationError(
                        "Le VIN doit contenir exactement 17 caractères."
                    )
                if not re.match(r'^[A-HJ-NPR-Z0-9]{17}$', vin):
                    raise ValidationError(
                        "Le VIN contient des caractères invalides "
                        "(I, O, Q interdits)."
                    )
                # Normaliser en majuscules
                if rec.vin_sn != vin:
                    rec.vin_sn = vin

    # ------------------------------------------------------------------
    # CRUD
    # ------------------------------------------------------------------

    @api.model_create_multi
    def create(self, vals_list):
        """Attribue une référence garage séquentielle à la création."""
        for vals in vals_list:
            if vals.get('garage_ref', 'Nouveau') == 'Nouveau':
                vals['garage_ref'] = self.env['ir.sequence'].next_by_code(
                    'garage.vehicle'
                ) or 'Nouveau'
        return super().create(vals_list)
