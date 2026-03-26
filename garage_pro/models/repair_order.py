"""Ordre de réparation — objet opérationnel central de l'atelier."""

from datetime import timedelta

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
    workshop_chief_id = fields.Many2one(
        'hr.employee',
        string="Chef d'atelier",
        domain="[('is_garage_technician', '=', True)]",
        tracking=True,
    )
    technician_ids = fields.Many2many(
        'hr.employee',
        'garage_ro_technician_rel',
        'repair_order_id',
        'employee_id',
        string="Techniciens affectés",
        domain="[('is_garage_technician', '=', True)]",
    )
    planning_slot_ids = fields.One2many(
        'garage.planning.slot',
        'repair_order_id',
        string="Créneaux planning",
    )
    planning_slot_count = fields.Integer(
        compute='_compute_planning_slot_count',
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

    # === SOUS-TRAITANCE ===
    subcontract_order_ids = fields.One2many(
        'garage.subcontract.order',
        'repair_order_id',
        string="Bons de sous-traitance",
    )
    subcontract_count = fields.Integer(
        compute='_compute_subcontract_count',
    )

    # === COURTOISIE ===
    courtesy_loan_id = fields.Many2one(
        'garage.courtesy.loan',
        string="Prêt de courtoisie",
    )
    has_courtesy_vehicle = fields.Boolean(
        string="Véhicule de courtoisie",
        compute='_compute_has_courtesy',
        store=True,
    )

    # === FACTURATION ===
    invoice_ids = fields.One2many(
        'account.move',
        'garage_repair_order_id',
        string="Factures",
        domain=[('move_type', 'in', ('out_invoice', 'out_refund'))],
    )
    invoice_count = fields.Integer(
        compute='_compute_invoice_count',
    )
    invoice_status = fields.Selection([
        ('no', 'Rien à facturer'),
        ('to_invoice', 'À facturer'),
        ('partial', 'Partiellement facturé'),
        ('invoiced', 'Entièrement facturé'),
    ], string="Statut facturation",
        compute='_compute_invoice_status',
        store=True,
    )

    # === QUALITÉ ===
    quality_checklist_ids = fields.One2many(
        'garage.quality.checklist',
        'repair_order_id',
        string="Checklists qualité",
    )
    quality_checklist_count = fields.Integer(
        compute='_compute_quality_checklist_count',
    )

    # === DOCUMENTATION ===
    documentation_ids = fields.One2many(
        'garage.documentation',
        'repair_order_id',
        string="Documents / Photos",
    )
    photo_count = fields.Integer(
        compute='_compute_photo_count',
    )

    # === MARGE ===
    total_cost = fields.Monetary(
        string="Coût total",
        compute='_compute_margin',
        store=True,
        currency_field='currency_id',
    )
    margin = fields.Monetary(
        string="Marge",
        compute='_compute_margin',
        store=True,
        currency_field='currency_id',
    )
    margin_rate = fields.Float(
        string="Taux marge (%)",
        compute='_compute_margin',
        store=True,
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

    @api.depends('planning_slot_ids')
    def _compute_planning_slot_count(self):
        for rec in self:
            rec.planning_slot_count = len(rec.planning_slot_ids)

    @api.depends('subcontract_order_ids')
    def _compute_subcontract_count(self):
        for rec in self:
            rec.subcontract_count = len(rec.subcontract_order_ids)

    @api.depends('courtesy_loan_id')
    def _compute_has_courtesy(self):
        for rec in self:
            rec.has_courtesy_vehicle = bool(rec.courtesy_loan_id)

    @api.depends('quality_checklist_ids')
    def _compute_quality_checklist_count(self):
        for rec in self:
            rec.quality_checklist_count = len(rec.quality_checklist_ids)

    @api.depends('documentation_ids')
    def _compute_photo_count(self):
        for rec in self:
            rec.photo_count = len(rec.documentation_ids)

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

    @api.depends('invoice_ids')
    def _compute_invoice_count(self):
        for rec in self:
            rec.invoice_count = len(rec.invoice_ids)

    @api.depends('invoice_ids', 'invoice_ids.payment_state', 'state')
    def _compute_invoice_status(self):
        for rec in self:
            if not rec.invoice_ids:
                if rec.state in ('delivered', 'ready', 'qc_done'):
                    rec.invoice_status = 'to_invoice'
                else:
                    rec.invoice_status = 'no'
            elif rec.state == 'invoiced':
                rec.invoice_status = 'invoiced'
            else:
                rec.invoice_status = 'partial'

    @api.depends('line_ids.cost_total', 'amount_untaxed')
    def _compute_margin(self):
        for rec in self:
            rec.total_cost = sum(rec.line_ids.mapped('cost_total'))
            rec.margin = rec.amount_untaxed - rec.total_cost
            if rec.amount_untaxed:
                rec.margin_rate = (rec.margin / rec.amount_untaxed) * 100
            else:
                rec.margin_rate = 0.0

    @api.depends('line_ids.amount_total')
    def _compute_amounts(self):
        vat_rate = float(
            self.env['ir.config_parameter'].sudo().get_param(
                'garage_pro.default_vat_rate', '21.0'
            )
        ) / 100.0
        for rec in self:
            rec.amount_untaxed = sum(rec.line_ids.mapped('amount_total'))
            rec.amount_tax = rec.amount_untaxed * vat_rate
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
        """Brouillon → Confirmé. Vérifie la disponibilité des pièces."""
        self.write({'state': 'confirmed'})
        for rec in self:
            missing_lines = rec.line_ids.filtered(
                lambda l: (l.line_type == 'parts'
                           and l.product_id
                           and l.product_id.qty_available < l.quantity)
            )
            if missing_lines:
                rec.write({'state': 'parts_waiting'})
                rec._create_auto_purchase_orders(missing_lines)
                rec.activity_schedule(
                    'mail.mail_activity_data_todo',
                    summary="Pièces manquantes — %s" % rec.name,
                    note="Pièces à commander : %s" % ', '.join(
                        missing_lines.mapped('name')
                    ),
                )

    def _create_auto_purchase_orders(self, missing_lines):
        """Crée des bons de commande fournisseur brouillon pour les pièces manquantes."""
        self.ensure_one()
        # Grouper par fournisseur (seller_id sur le product.template)
        supplier_lines = {}
        for line in missing_lines:
            seller = line.product_id.seller_ids[:1]
            partner = seller.partner_id if seller else False
            if partner:
                supplier_lines.setdefault(partner.id, {
                    'partner': partner,
                    'lines': self.env['garage.repair.order.line'],
                })
                supplier_lines[partner.id]['lines'] |= line
            else:
                # Pas de fournisseur défini — juste une notification
                self.message_post(
                    body="Aucun fournisseur défini pour la pièce « %s ». "
                         "Commande manuelle requise." % line.name,
                    message_type='notification',
                )

        PurchaseOrder = self.env['purchase.order'].with_company(
            self.company_id
        )
        # Picking type pour les réceptions (incoming)
        picking_type = self.env['stock.picking.type'].search([
            ('code', '=', 'incoming'),
            ('warehouse_id.company_id', '=', self.company_id.id),
        ], limit=1)
        if not picking_type:
            picking_type = self.env['stock.picking.type'].search([
                ('code', '=', 'incoming'),
            ], limit=1)
        for data in supplier_lines.values():
            po_lines = []
            for line in data['lines']:
                qty_needed = line.quantity - line.product_id.qty_available
                if qty_needed <= 0:
                    continue
                po_lines.append((0, 0, {
                    'product_id': line.product_id.id,
                    'name': line.name,
                    'product_qty': qty_needed,
                    'product_uom': (
                        line.product_id.uom_po_id.id
                        or line.product_id.uom_id.id
                    ),
                    'price_unit': (
                        line.product_id.seller_ids[:1].price
                        if line.product_id.seller_ids
                        else line.cost_price
                    ),
                }))
            if po_lines:
                po_vals = {
                    'partner_id': data['partner'].id,
                    'origin': self.name,
                    'order_line': po_lines,
                }
                if picking_type:
                    po_vals['picking_type_id'] = picking_type.id
                po = PurchaseOrder.create(po_vals)
                self.message_post(
                    body="Commande fournisseur <a href='#' "
                         "data-oe-model='purchase.order' "
                         "data-oe-id='%d'>%s</a> créée automatiquement."
                         % (po.id, po.name),
                    message_type='notification',
                )

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

    def action_open_invoice_wizard(self):
        """Ouvre l'assistant de facturation multi-payeur."""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Facturer',
            'res_model': 'garage.invoice.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_repair_order_id': self.id,
            },
        }

    def action_view_invoices(self):
        """Ouvre la liste des factures liées à cet OR."""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Factures',
            'res_model': 'account.move',
            'view_mode': 'tree,form',
            'domain': [('id', 'in', self.invoice_ids.ids)],
        }

    def action_create_credit_note(self):
        """Crée un avoir lié à cet OR."""
        self.ensure_one()
        vals = {
            'move_type': 'out_refund',
            'partner_id': self.customer_id.id,
            'garage_repair_order_id': self.id,
            'garage_claim_id': self.claim_id.id if self.claim_id else False,
            'invoice_origin': self.name,
            'ref': "Avoir — %s" % self.name,
        }
        credit_note = self.env['account.move'].create(vals)
        return {
            'type': 'ir.actions.act_window',
            'name': 'Avoir',
            'res_model': 'account.move',
            'view_mode': 'form',
            'res_id': credit_note.id,
        }

    def action_create_quality_checklist(self):
        """Crée une checklist QC pré-livraison pour cet OR."""
        self.ensure_one()
        checklist = self.env['garage.quality.checklist'].create_from_repair_order(self)
        return {
            'type': 'ir.actions.act_window',
            'name': 'Checklist qualité',
            'res_model': 'garage.quality.checklist',
            'view_mode': 'form',
            'res_id': checklist.id,
        }

    def action_view_quality_checklists(self):
        """Ouvre les checklists qualité liées à cet OR."""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Checklists qualité',
            'res_model': 'garage.quality.checklist',
            'view_mode': 'tree,form',
            'domain': [('repair_order_id', '=', self.id)],
        }

    def action_view_documentation(self):
        """Ouvre les documents / photos liés à cet OR."""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Documents / Photos',
            'res_model': 'garage.documentation',
            'view_mode': 'tree,form',
            'domain': [('repair_order_id', '=', self.id)],
            'context': {'default_repair_order_id': self.id},
        }

    # ------------------------------------------------------------------
    # Crons
    # ------------------------------------------------------------------

    @api.model
    def cron_vehicle_not_picked_up(self):
        """Alerte : véhicule non récupéré > 7 jours après état 'ready'."""
        cutoff = fields.Datetime.now() - timedelta(days=7)
        orders = self.search([
            ('state', '=', 'ready'),
            ('write_date', '<=', cutoff),
        ])
        for order in orders:
            order.activity_schedule(
                'mail.mail_activity_data_todo',
                date_deadline=fields.Date.today(),
                summary="Véhicule non récupéré depuis > 7 jours — %s" % order.name,
            )
