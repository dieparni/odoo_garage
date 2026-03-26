"""Ordre de réparation — objet opérationnel central de l'atelier."""

from odoo import api, fields, models


class GarageRepairOrder(models.Model):
    """OR garage avec workflow complet de suivi des réparations."""

    _name = 'garage.repair.order'
    _description = 'Ordre de réparation'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'create_date desc'

    name = fields.Char(
        string="Référence OR",
        default='Nouveau',
        readonly=True,
        copy=False,
    )

    # === STATUT ===
    state = fields.Selection([
        ('draft', 'Brouillon'),
        ('confirmed', 'Confirmé'),
        ('parts_waiting', 'Attente pièces'),
        ('in_progress', 'En cours'),
        ('paint_booth', 'En cabine'),
        ('reassembly', 'Remontage'),
        ('qc_pending', 'Contrôle qualité'),
        ('qc_done', 'QC validé'),
        ('ready', 'Prêt à livrer'),
        ('delivered', 'Livré'),
        ('invoiced', 'Facturé'),
        ('cancelled', 'Annulé'),
    ], default='draft', tracking=True, string="Statut",
        group_expand='_group_expand_states')

    # === LIENS ===
    vehicle_id = fields.Many2one(
        'fleet.vehicle',
        string="Véhicule",
        required=True,
        tracking=True,
    )
    customer_id = fields.Many2one(
        'res.partner',
        string="Client",
        required=True,
        tracking=True,
    )
    invoice_partner_id = fields.Many2one(
        'res.partner',
        string="Facturer à",
    )
    claim_id = fields.Many2one(
        'garage.insurance.claim',
        string="Sinistre",
    )
    quotation_id = fields.Many2one(
        'garage.quotation',
        string="Devis d'origine",
    )
    quotation_ids = fields.One2many(
        'garage.quotation',
        'repair_order_id',
        string="Devis liés",
    )

    # === LIGNES ===
    line_ids = fields.One2many(
        'garage.repair.order.line',
        'repair_order_id',
        string="Lignes",
    )

    # === OPÉRATIONS MÉTIER ===
    bodywork_operation_ids = fields.One2many(
        'garage.bodywork.operation',
        'repair_order_id',
        string="Opérations carrosserie",
    )
    paint_operation_ids = fields.One2many(
        'garage.paint.operation',
        'repair_order_id',
        string="Opérations peinture",
    )
    mechanic_operation_ids = fields.One2many(
        'garage.mechanic.operation',
        'repair_order_id',
        string="Opérations mécanique",
    )
    bodywork_count = fields.Integer(
        compute='_compute_operation_counts',
    )
    paint_count = fields.Integer(
        compute='_compute_operation_counts',
    )
    mechanic_count = fields.Integer(
        compute='_compute_operation_counts',
    )

    # === PLANNING ===
    planned_start_date = fields.Datetime(string="Début planifié")
    planned_end_date = fields.Datetime(string="Fin planifiée")
    actual_start_date = fields.Datetime(string="Début réel")
    actual_end_date = fields.Datetime(string="Fin réelle")
    estimated_days = fields.Float(string="Durée estimée (jours)")
    estimated_delivery_date = fields.Date(
        string="Date restitution estimée",
    )

    # === VÉHICULE ===
    odometer_at_entry = fields.Integer(string="Km à l'entrée")
    odometer_at_exit = fields.Integer(string="Km à la sortie")
    vehicle_location = fields.Selection([
        ('outside', 'Parking extérieur'),
        ('workshop', "Dans l'atelier"),
        ('paint_booth', 'En cabine peinture'),
        ('subcontractor', 'Chez un sous-traitant'),
        ('delivered', 'Restitué'),
    ], string="Localisation véhicule", default='outside', tracking=True)

    # === TEMPS ===
    total_allocated_hours = fields.Float(
        string="Heures allouées (total)",
        compute='_compute_hours',
        store=True,
    )
    total_worked_hours = fields.Float(
        string="Heures travaillées (total)",
        compute='_compute_hours',
        store=True,
    )
    productivity_rate = fields.Float(
        string="Taux de productivité (%)",
        compute='_compute_hours',
        store=True,
    )

    # === MONTANTS ===
    amount_untaxed = fields.Monetary(
        string="Total HT",
        compute='_compute_amounts',
        store=True,
        currency_field='currency_id',
    )
    amount_tax = fields.Monetary(
        string="TVA",
        compute='_compute_amounts',
        store=True,
        currency_field='currency_id',
    )
    amount_total = fields.Monetary(
        string="Total TTC",
        compute='_compute_amounts',
        store=True,
        currency_field='currency_id',
    )

    # === NOTES ===
    internal_notes = fields.Html(string="Notes internes")
    delivery_notes = fields.Html(string="Notes de restitution")

    # === PRIORITÉ ===
    priority = fields.Selection([
        ('0', 'Normal'),
        ('1', 'Urgent'),
        ('2', 'Très urgent'),
    ], default='0', string="Priorité")

    company_id = fields.Many2one(
        'res.company',
        default=lambda self: self.env.company,
    )
    currency_id = fields.Many2one(
        'res.currency',
        default=lambda self: self.env.company.currency_id,
    )
    user_id = fields.Many2one(
        'res.users',
        string="Responsable",
        default=lambda self: self.env.user,
    )

    # ------------------------------------------------------------------
    # Compute
    # ------------------------------------------------------------------

    @api.depends('bodywork_operation_ids', 'paint_operation_ids',
                 'mechanic_operation_ids')
    def _compute_operation_counts(self):
        for rec in self:
            rec.bodywork_count = len(rec.bodywork_operation_ids)
            rec.paint_count = len(rec.paint_operation_ids)
            rec.mechanic_count = len(rec.mechanic_operation_ids)

    @api.depends('line_ids.allocated_time', 'line_ids.actual_time')
    def _compute_hours(self):
        for rec in self:
            rec.total_allocated_hours = sum(
                rec.line_ids.mapped('allocated_time')
            )
            rec.total_worked_hours = sum(
                rec.line_ids.mapped('actual_time')
            )
            if rec.total_allocated_hours:
                rec.productivity_rate = (
                    rec.total_worked_hours / rec.total_allocated_hours * 100
                )
            else:
                rec.productivity_rate = 0.0

    @api.depends('line_ids.amount_total')
    def _compute_amounts(self):
        for rec in self:
            rec.amount_untaxed = sum(rec.line_ids.mapped('amount_total'))
            rec.amount_tax = rec.amount_untaxed * 0.21
            rec.amount_total = rec.amount_untaxed + rec.amount_tax

    @api.model
    def _group_expand_states(self, states, domain):
        """Affiche toutes les colonnes dans la vue kanban."""
        return [key for key, _val in type(self).state.selection]

    # ------------------------------------------------------------------
    # CRUD
    # ------------------------------------------------------------------

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', 'Nouveau') == 'Nouveau':
                vals['name'] = self.env['ir.sequence'].next_by_code(
                    'garage.repair.order'
                ) or 'Nouveau'
        return super().create(vals_list)

    # ------------------------------------------------------------------
    # Workflow actions
    # ------------------------------------------------------------------

    def action_confirm(self):
        """Brouillon → Confirmé."""
        self.write({'state': 'confirmed'})

    def action_start(self):
        """Confirmé/Attente pièces → En cours."""
        self.write({
            'state': 'in_progress',
            'actual_start_date': fields.Datetime.now(),
            'vehicle_location': 'workshop',
        })

    def action_enter_paint_booth(self):
        """En cours → En cabine."""
        self.write({
            'state': 'paint_booth',
            'vehicle_location': 'paint_booth',
        })

    def action_reassembly(self):
        """En cabine → Remontage."""
        self.write({
            'state': 'reassembly',
            'vehicle_location': 'workshop',
        })

    def action_request_qc(self):
        """Remontage → Contrôle qualité."""
        self.write({'state': 'qc_pending'})

    def action_validate_qc(self):
        """QC → QC validé."""
        self.write({'state': 'qc_done'})

    def action_ready(self):
        """QC validé → Prêt à livrer."""
        self.write({'state': 'ready'})

    def action_deliver(self):
        """Prêt → Livré. Restitution du véhicule."""
        self.write({
            'state': 'delivered',
            'actual_end_date': fields.Datetime.now(),
            'vehicle_location': 'delivered',
        })
        # Mettre à jour l'odomètre si saisi
        for rec in self:
            if rec.odometer_at_exit and rec.vehicle_id:
                self.env['fleet.vehicle.odometer'].create({
                    'vehicle_id': rec.vehicle_id.id,
                    'value': rec.odometer_at_exit,
                    'date': fields.Date.today(),
                })

    def action_cancel(self):
        """Annuler l'OR."""
        self.write({'state': 'cancelled'})
