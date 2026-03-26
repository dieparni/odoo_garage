"""Sinistres assurance — modèle transactionnel central."""

from datetime import timedelta

from odoo import api, fields, models
from odoo.exceptions import UserError


class GarageInsuranceClaim(models.Model):
    """Sinistre assurance lié à un véhicule et un client."""

    _name = 'garage.insurance.claim'
    _description = 'Sinistre assurance'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'create_date desc'

    name = fields.Char(
        string="Référence sinistre",
        default='Nouveau',
        readonly=True,
        copy=False,
    )

    # === STATUT ===
    state = fields.Selection([
        ('draft', 'Brouillon'),
        ('declared', 'Déclaré'),
        ('expertise_pending', "En attente d'expertise"),
        ('expertise_done', 'Expertise réalisée'),
        ('approved', 'Accord reçu'),
        ('supplement_pending', 'Supplément en attente'),
        ('supplement_approved', 'Supplément approuvé'),
        ('work_in_progress', 'Travaux en cours'),
        ('invoiced', 'Facturé'),
        ('paid', 'Payé'),
        ('vei', 'VEI (Perte totale)'),
        ('disputed', 'Litige'),
        ('cancelled', 'Annulé'),
    ], string="Statut", default='draft', tracking=True,
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
        string="Client (assuré)",
        required=True,
        tracking=True,
    )
    insurance_company_id = fields.Many2one(
        'garage.insurance.company',
        string="Compagnie d'assurance",
        required=True,
        tracking=True,
    )
    expert_id = fields.Many2one(
        'garage.insurance.expert',
        string="Expert assigné",
        domain="[('company_id', '=', insurance_company_id)]",
    )
    quotation_id = fields.Many2one(
        'garage.quotation',
        string="Devis principal",
    )
    repair_order_id = fields.Many2one(
        'garage.repair.order',
        string="Ordre de réparation",
    )

    # === SINISTRE ===
    claim_date = fields.Date(
        string="Date du sinistre",
        required=True,
        tracking=True,
    )
    declaration_date = fields.Date(string="Date de déclaration")
    claim_type = fields.Selection([
        ('collision', 'Collision'),
        ('theft', 'Vol'),
        ('vandalism', 'Vandalisme'),
        ('hail', 'Grêle'),
        ('glass', 'Bris de glace'),
        ('natural', 'Catastrophe naturelle'),
        ('fire', 'Incendie'),
        ('parking', 'Dommage parking'),
        ('animal', 'Collision animale'),
        ('other', 'Autre'),
    ], string="Type de sinistre", required=True, tracking=True)
    claim_description = fields.Html(string="Circonstances du sinistre")
    has_third_party = fields.Boolean(string="Tiers impliqué")
    third_party_info = fields.Text(
        string="Informations tiers",
        help="Nom, assurance, immatriculation du tiers",
    )
    police_report = fields.Boolean(string="PV de police établi")
    police_report_number = fields.Char(string="Numéro PV")

    # === ASSURANCE CLIENT ===
    policy_number = fields.Char(string="N° de police")
    insurance_claim_number = fields.Char(
        string="N° sinistre assurance",
        help="Numéro attribué par la compagnie d'assurance",
        tracking=True,
    )

    # === FRANCHISE ===
    franchise_type = fields.Selection([
        ('none', 'Pas de franchise'),
        ('fixed', 'Montant fixe'),
        ('percentage', 'Pourcentage'),
        ('variable', 'Variable (selon contrat)'),
    ], string="Type de franchise", default='fixed')
    franchise_amount = fields.Monetary(
        string="Montant franchise (€)",
        currency_field='currency_id',
        tracking=True,
    )
    franchise_percentage = fields.Float(
        string="Franchise (%)",
        help="Pourcentage du montant total des réparations",
    )
    franchise_computed = fields.Monetary(
        string="Franchise calculée",
        compute='_compute_franchise',
        currency_field='currency_id',
        store=True,
    )

    # === EXPERTISE ===
    expertise_date = fields.Datetime(string="Date expertise prévue")
    expertise_done_date = fields.Datetime(string="Date expertise réalisée")
    expertise_type = fields.Selection([
        ('on_site', 'Sur place'),
        ('remote', 'À distance (photos)'),
        ('waived', "Dispensé d'expertise"),
    ], string="Type d'expertise")
    expertise_report = fields.Binary(string="Rapport d'expertise")
    expertise_report_filename = fields.Char(string="Nom fichier expertise")

    # === MONTANTS ===
    estimated_amount = fields.Monetary(
        string="Montant estimé (devis)",
        currency_field='currency_id',
    )
    approved_amount = fields.Monetary(
        string="Montant approuvé (expert)",
        currency_field='currency_id',
        tracking=True,
    )
    supplement_amount = fields.Monetary(
        string="Montant supplément",
        compute='_compute_supplement_amount',
        currency_field='currency_id',
        store=True,
    )
    total_approved = fields.Monetary(
        string="Total approuvé",
        compute='_compute_total_approved',
        currency_field='currency_id',
        store=True,
    )

    # === VEI ===
    is_vei = fields.Boolean(string="Véhicule Économiquement Irréparable")
    vei_vehicle_value = fields.Monetary(
        string="Valeur vénale véhicule",
        currency_field='currency_id',
    )
    vei_repair_cost = fields.Monetary(
        string="Coût réparation estimé",
        currency_field='currency_id',
    )
    vei_customer_decision = fields.Selection([
        ('pending', 'En attente de décision'),
        ('accept_loss', 'Accepte la perte totale'),
        ('repair_own_cost', 'Répare à ses frais'),
        ('contest', 'Conteste la décision'),
    ], string="Décision client VEI")

    # === SUPPLÉMENT ===
    supplement_ids = fields.One2many(
        'garage.insurance.supplement',
        'claim_id',
        string="Suppléments",
    )
    supplement_count = fields.Integer(compute='_compute_supplement_count')

    # === DOCUMENTS ===
    accident_report = fields.Binary(string="Constat amiable")
    accident_report_filename = fields.Char()
    document_ids = fields.One2many(
        'garage.documentation',
        'claim_id',
        string="Documents / Photos",
    )
    document_count = fields.Integer(
        compute='_compute_document_count',
    )

    currency_id = fields.Many2one(
        'res.currency',
        default=lambda self: self.env.company.currency_id,
    )

    # ------------------------------------------------------------------
    # Compute
    # ------------------------------------------------------------------

    @api.depends('franchise_type', 'franchise_amount', 'franchise_percentage',
                 'estimated_amount')
    def _compute_franchise(self):
        for rec in self:
            if rec.franchise_type == 'fixed':
                rec.franchise_computed = rec.franchise_amount
            elif rec.franchise_type == 'percentage' and rec.estimated_amount:
                rec.franchise_computed = (
                    rec.estimated_amount * rec.franchise_percentage / 100.0
                )
            else:
                rec.franchise_computed = 0.0

    @api.depends('supplement_ids.approved_amount', 'supplement_ids.state')
    def _compute_supplement_amount(self):
        for rec in self:
            rec.supplement_amount = sum(
                s.approved_amount for s in rec.supplement_ids
                if s.state == 'approved'
            )

    @api.depends('approved_amount', 'supplement_amount')
    def _compute_total_approved(self):
        for rec in self:
            rec.total_approved = rec.approved_amount + rec.supplement_amount

    @api.depends('supplement_ids')
    def _compute_supplement_count(self):
        for rec in self:
            rec.supplement_count = len(rec.supplement_ids)

    @api.depends('document_ids')
    def _compute_document_count(self):
        for rec in self:
            rec.document_count = len(rec.document_ids)

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
                    'garage.insurance.claim'
                ) or 'Nouveau'
        return super().create(vals_list)

    # ------------------------------------------------------------------
    # Workflow actions
    # ------------------------------------------------------------------

    def action_declare(self):
        """Brouillon → Déclaré."""
        self.write({
            'state': 'declared',
            'declaration_date': fields.Date.today(),
        })

    def action_request_expertise(self):
        """Déclaré → En attente d'expertise."""
        self.write({'state': 'expertise_pending'})
        for rec in self:
            rec.activity_schedule(
                'mail.mail_activity_data_todo',
                date_deadline=fields.Date.today() + timedelta(days=5),
                summary="Relancer expert pour sinistre %s" % rec.name,
            )

    def action_expertise_done(self):
        """En attente → Expertise réalisée."""
        self.write({
            'state': 'expertise_done',
            'expertise_done_date': fields.Datetime.now(),
        })

    def action_approve(self):
        """Expertise réalisée → Approuvé."""
        for rec in self:
            if not rec.approved_amount:
                raise UserError(
                    "Veuillez saisir le montant approuvé par l'expert "
                    "avant de valider."
                )
        self.write({'state': 'approved'})

    def action_request_supplement(self):
        """Ouvre le wizard de demande de supplément."""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Demande de supplément',
            'res_model': 'garage.insurance.supplement.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_claim_id': self.id},
        }

    def action_start_work(self):
        """Approuvé → Travaux en cours (vérifie que l'OR existe)."""
        for rec in self:
            if not rec.repair_order_id:
                raise UserError(
                    "Aucun ordre de réparation n'est lié à ce sinistre."
                )
        self.write({'state': 'work_in_progress'})

    def action_mark_vei(self):
        """Marquer comme VEI (perte totale)."""
        self.write({
            'state': 'vei',
            'is_vei': True,
            'vei_customer_decision': 'pending',
        })

    def action_dispute(self):
        """Passer en litige."""
        self.write({'state': 'disputed'})

    def action_cancel(self):
        """Annuler le sinistre."""
        self.write({'state': 'cancelled'})

    def action_view_documents(self):
        """Ouvre les documents / photos liés à ce sinistre."""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Documents / Photos',
            'res_model': 'garage.documentation',
            'view_mode': 'tree,form',
            'domain': [('claim_id', '=', self.id)],
            'context': {'default_claim_id': self.id},
        }

    # ------------------------------------------------------------------
    # Crons
    # ------------------------------------------------------------------

    @api.model
    def cron_reminder_expertise(self):
        """Relance : sinistres en attente d'expertise > 5 jours."""
        cutoff = fields.Datetime.now() - timedelta(days=5)
        claims = self.search([
            ('state', '=', 'expertise_pending'),
            ('write_date', '<=', cutoff),
        ])
        for claim in claims:
            claim.activity_schedule(
                'mail.mail_activity_data_todo',
                date_deadline=fields.Date.today(),
                summary="Relance expertise sinistre %s" % claim.name,
            )
