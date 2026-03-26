"""Compagnies d'assurance et barèmes agréés."""

from odoo import api, fields, models


class GarageInsuranceCompany(models.Model):
    """Compagnie d'assurance avec barèmes et conditions de convention."""

    _name = 'garage.insurance.company'
    _description = "Compagnie d'assurance"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'name'

    name = fields.Char(string="Nom", required=True, tracking=True)
    partner_id = fields.Many2one(
        'res.partner',
        string="Contact Odoo",
        required=True,
        help="Le contact res.partner correspondant (pour facturation)",
        domain="[('is_company', '=', True)]",
    )
    code = fields.Char(
        string="Code interne",
        help="Code court (ex: AXA, ETH, AG)",
    )
    active = fields.Boolean(default=True)

    # === CONTACTS ===
    expert_contact_ids = fields.One2many(
        'garage.insurance.expert',
        'company_id',
        string="Experts agréés",
    )
    main_contact_name = fields.Char(string="Contact principal")
    main_contact_phone = fields.Char(string="Téléphone contact")
    main_contact_email = fields.Char(string="Email contact")
    claims_email = fields.Char(
        string="Email déclaration sinistres",
        help="Email pour envoyer les devis et documents",
    )
    portal_url = fields.Char(string="URL portail en ligne")

    # === BARÈMES & TARIFICATION ===
    hourly_rate_bodywork = fields.Monetary(
        string="Taux horaire carrosserie agréé (€/h)",
        currency_field='currency_id',
        tracking=True,
    )
    hourly_rate_paint = fields.Monetary(
        string="Taux horaire peinture agréé (€/h)",
        currency_field='currency_id',
    )
    hourly_rate_mechanic = fields.Monetary(
        string="Taux horaire mécanique agréé (€/h)",
        currency_field='currency_id',
    )
    parts_coefficient = fields.Float(
        string="Coefficient pièces",
        default=1.0,
        help="Coefficient appliqué sur le prix catalogue des pièces",
    )
    paint_material_rate = fields.Float(
        string="Taux matière peinture (€/h peinte)",
        help="Forfait matière peinture par heure de peinture allouée",
    )
    allows_aftermarket_parts = fields.Boolean(
        string="Accepte pièces aftermarket",
        default=False,
    )
    allows_used_parts = fields.Boolean(
        string="Accepte pièces d'occasion",
        default=False,
    )
    max_vehicle_age_used_parts = fields.Integer(
        string="Âge max véhicule pour pièces neuves (ans)",
        help="Au-delà de cet âge, l'assurance impose des pièces d'occasion",
    )

    # === CONDITIONS ===
    payment_term_id = fields.Many2one(
        'account.payment.term',
        string="Conditions de paiement",
    )
    average_payment_days = fields.Integer(
        string="Délai moyen constaté (jours)",
        help="Délai réel moyen de paiement observé",
    )
    convention_type = fields.Selection([
        ('direct', 'Convention directe (tiers payant)'),
        ('indirect', 'Indirect (via assuré)'),
        ('mixed', 'Mixte'),
    ], string="Type de convention", default='indirect')

    # === STATS ===
    claim_ids = fields.One2many(
        'garage.insurance.claim',
        'insurance_company_id',
        string="Sinistres",
    )
    claim_count = fields.Integer(compute='_compute_claim_count')

    currency_id = fields.Many2one(
        'res.currency',
        default=lambda self: self.env.company.currency_id,
    )

    # === NOTES ===
    notes = fields.Html(string="Notes / Particularités")

    # ------------------------------------------------------------------
    # Compute
    # ------------------------------------------------------------------

    def _compute_claim_count(self):
        for rec in self:
            rec.claim_count = self.env['garage.insurance.claim'].search_count([
                ('insurance_company_id', '=', rec.id),
            ])

    # ------------------------------------------------------------------
    # Actions
    # ------------------------------------------------------------------

    def action_view_claims(self):
        """Ouvre la liste des sinistres de cette compagnie."""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Sinistres',
            'res_model': 'garage.insurance.claim',
            'view_mode': 'tree,form',
            'domain': [('insurance_company_id', '=', self.id)],
        }
