"""Bon de sous-traitance — travaux délégués à un partenaire externe."""

from odoo import api, fields, models


class GarageSubcontractOrder(models.Model):
    """Bon de sous-traitance lié à un OR."""

    _name = 'garage.subcontract.order'
    _description = 'Bon de sous-traitance'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'create_date desc'

    name = fields.Char(
        string="Référence",
        default='Nouveau',
        readonly=True,
        copy=False,
    )
    repair_order_id = fields.Many2one(
        'garage.repair.order',
        string="Ordre de réparation",
        required=True,
        ondelete='cascade',
    )
    subcontractor_id = fields.Many2one(
        'res.partner',
        string="Sous-traitant",
        required=True,
        domain="[('is_subcontractor', '=', True)]",
        tracking=True,
    )

    service_type = fields.Selection([
        ('pdr', 'Débosselage sans peinture (PDR)'),
        ('glass', 'Vitrage'),
        ('upholstery', 'Sellerie / Garnissage'),
        ('electronics', 'Électronique embarquée'),
        ('adas_calibration', 'Calibration ADAS (caméras)'),
        ('aircon', 'Climatisation spécialisée'),
        ('geometry', 'Géométrie spécialisée'),
        ('towing', 'Remorquage / dépannage'),
        ('painting', 'Peinture externe'),
        ('other', 'Autre'),
    ], string="Type de service", required=True, tracking=True)

    description = fields.Html(string="Description des travaux")
    estimated_cost = fields.Monetary(
        string="Coût estimé",
        currency_field='currency_id',
    )
    actual_cost = fields.Monetary(
        string="Coût réel",
        currency_field='currency_id',
    )

    state = fields.Selection([
        ('draft', 'Brouillon'),
        ('sent', 'Envoyé'),
        ('in_progress', 'En cours'),
        ('done', 'Terminé'),
        ('invoiced', 'Facturé'),
        ('cancelled', 'Annulé'),
    ], default='draft', tracking=True, string="Statut")

    send_date = fields.Date(string="Date d'envoi")
    expected_return_date = fields.Date(string="Retour prévu")
    actual_return_date = fields.Date(string="Retour réel")
    is_late = fields.Boolean(
        string="En retard",
        compute='_compute_is_late',
        store=True,
    )

    send_type = fields.Selection([
        ('vehicle', 'Véhicule envoyé chez le sous-traitant'),
        ('part', 'Pièce envoyée'),
        ('on_site', 'Intervention sur place'),
    ], string="Mode", default='on_site')

    quality_ok = fields.Boolean(string="Qualité validée")
    quality_notes = fields.Text(string="Notes qualité")
    purchase_order_id = fields.Many2one(
        'purchase.order',
        string="Bon de commande achat",
    )

    currency_id = fields.Many2one(
        'res.currency',
        default=lambda self: self.env.company.currency_id,
    )
    company_id = fields.Many2one(
        'res.company',
        default=lambda self: self.env.company,
    )

    # Champs relationnels pour les vues
    vehicle_id = fields.Many2one(
        related='repair_order_id.vehicle_id',
        store=True,
        string="Véhicule",
    )

    # ------------------------------------------------------------------
    # Compute
    # ------------------------------------------------------------------

    @api.depends('expected_return_date', 'actual_return_date', 'state')
    def _compute_is_late(self):
        today = fields.Date.today()
        for rec in self:
            if rec.state in ('done', 'invoiced', 'cancelled'):
                rec.is_late = False
            elif rec.expected_return_date and not rec.actual_return_date:
                rec.is_late = today > rec.expected_return_date
            else:
                rec.is_late = False

    # ------------------------------------------------------------------
    # CRUD
    # ------------------------------------------------------------------

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', 'Nouveau') == 'Nouveau':
                vals['name'] = self.env['ir.sequence'].next_by_code(
                    'garage.subcontract.order'
                ) or 'Nouveau'
        return super().create(vals_list)

    # ------------------------------------------------------------------
    # Workflow actions
    # ------------------------------------------------------------------

    def action_send(self):
        """Brouillon → Envoyé."""
        self.write({
            'state': 'sent',
            'send_date': fields.Date.today(),
        })

    def action_start(self):
        """Envoyé → En cours."""
        self.write({'state': 'in_progress'})

    def action_done(self):
        """En cours → Terminé."""
        self.write({
            'state': 'done',
            'actual_return_date': fields.Date.today(),
        })

    def action_invoice(self):
        """Terminé → Facturé."""
        self.write({'state': 'invoiced'})

    def action_cancel(self):
        """Annuler le bon."""
        self.write({'state': 'cancelled'})

    def action_reset(self):
        """Remettre en brouillon."""
        self.write({'state': 'draft'})
