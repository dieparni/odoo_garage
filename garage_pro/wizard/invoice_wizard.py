"""Wizard de génération de factures multi-payeur depuis un OR."""

from odoo import api, fields, models
from odoo.exceptions import UserError


class GarageInvoiceWizard(models.TransientModel):
    """Assistant de facturation garage — gère les scénarios multi-payeur."""

    _name = 'garage.invoice.wizard'
    _description = 'Assistant facturation garage'

    repair_order_id = fields.Many2one(
        'garage.repair.order',
        string="Ordre de réparation",
        required=True,
    )
    invoice_scenario = fields.Selection([
        ('client_full', 'Client intégral (pas d\'assurance)'),
        ('insurance_split', 'Assurance + Franchise client'),
        ('insurance_only', 'Assurance seule (pas de franchise)'),
        ('deposit', 'Acompte client'),
        ('partial', 'Facture partielle (lignes terminées)'),
        ('courtesy_charge', 'Facturation courtoisie (dépassement)'),
    ], string="Scénario de facturation", required=True,
        default='client_full')

    # === Champs contextuels ===
    customer_id = fields.Many2one(
        related='repair_order_id.customer_id',
    )
    claim_id = fields.Many2one(
        related='repair_order_id.claim_id',
    )
    insurance_company_partner_id = fields.Many2one(
        'res.partner',
        string="Partenaire assurance",
        compute='_compute_insurance_partner',
    )
    franchise_amount = fields.Monetary(
        string="Montant franchise",
        compute='_compute_franchise',
        currency_field='currency_id',
    )
    amount_untaxed = fields.Monetary(
        related='repair_order_id.amount_untaxed',
    )
    currency_id = fields.Many2one(
        related='repair_order_id.currency_id',
    )

    # === Acompte ===
    deposit_amount = fields.Monetary(
        string="Montant acompte",
        currency_field='currency_id',
    )

    # === Courtoisie ===
    courtesy_loan_id = fields.Many2one(
        related='repair_order_id.courtesy_loan_id',
    )

    # ------------------------------------------------------------------
    # Compute
    # ------------------------------------------------------------------

    @api.depends('claim_id')
    def _compute_insurance_partner(self):
        for rec in self:
            if rec.claim_id and rec.claim_id.insurance_company_id:
                rec.insurance_company_partner_id = (
                    rec.claim_id.insurance_company_id.partner_id
                )
            else:
                rec.insurance_company_partner_id = False

    @api.depends('claim_id')
    def _compute_franchise(self):
        for rec in self:
            rec.franchise_amount = (
                rec.claim_id.franchise_computed if rec.claim_id else 0.0
            )

    # ------------------------------------------------------------------
    # Actions
    # ------------------------------------------------------------------

    def action_create_invoices(self):
        """Crée les factures selon le scénario choisi."""
        self.ensure_one()
        ro = self.repair_order_id

        if ro.state not in ('delivered', 'ready', 'qc_done', 'in_progress',
                            'paint_booth', 'reassembly'):
            raise UserError(
                "L'OR doit être au minimum en cours pour être facturé."
            )

        invoices = self.env['account.move']

        if self.invoice_scenario == 'client_full':
            invoices = self._create_client_full_invoice(ro)
        elif self.invoice_scenario == 'insurance_split':
            invoices = self._create_insurance_split_invoices(ro)
        elif self.invoice_scenario == 'insurance_only':
            invoices = self._create_insurance_only_invoice(ro)
        elif self.invoice_scenario == 'deposit':
            invoices = self._create_deposit_invoice(ro)
        elif self.invoice_scenario == 'partial':
            invoices = self._create_partial_invoice(ro)
        elif self.invoice_scenario == 'courtesy_charge':
            invoices = self._create_courtesy_invoice(ro)

        if not invoices:
            raise UserError("Aucune facture n'a pu être créée.")

        # Marquer l'OR comme facturé si facture complète
        if self.invoice_scenario in ('client_full', 'insurance_split',
                                     'insurance_only'):
            ro.write({'state': 'invoiced'})
            # Auto-transition du sinistre vers 'invoiced'
            if (ro.claim_id
                    and ro.claim_id.state == 'work_in_progress'):
                ro.claim_id.action_invoice()

        # Retourner la vue des factures créées
        action = {
            'type': 'ir.actions.act_window',
            'name': 'Factures créées',
            'res_model': 'account.move',
            'view_mode': 'tree,form',
            'domain': [('id', 'in', invoices.ids)],
        }
        if len(invoices) == 1:
            action.update({
                'view_mode': 'form',
                'res_id': invoices.id,
            })
        return action

    # ------------------------------------------------------------------
    # Méthodes privées de création
    # ------------------------------------------------------------------

    def _prepare_invoice_lines(self, ro, line_filter=None):
        """Prépare les lignes de facture depuis les lignes d'OR."""
        lines = ro.line_ids
        if line_filter:
            lines = lines.filtered(line_filter)

        invoice_lines = []
        for line in lines:
            vals = {
                'name': line.name,
                'quantity': line.quantity,
                'price_unit': line.unit_price,
                'discount': line.discount,
            }
            # Pour les lignes MO, utiliser allocated_time * hourly_rate
            if (line.line_type in ('labor_body', 'labor_paint', 'labor_mech')
                    and line.allocated_time and line.hourly_rate):
                vals['quantity'] = line.allocated_time
                vals['price_unit'] = line.hourly_rate
            if line.product_id:
                vals['product_id'] = line.product_id.id
            invoice_lines.append((0, 0, vals))
        return invoice_lines

    def _base_invoice_vals(self, ro, partner, garage_type):
        """Valeurs de base communes à toutes les factures garage."""
        return {
            'move_type': 'out_invoice',
            'partner_id': partner.id,
            'garage_repair_order_id': ro.id,
            'garage_claim_id': ro.claim_id.id if ro.claim_id else False,
            'garage_invoice_type': garage_type,
            'invoice_origin': ro.name,
            'ref': ro.name,
        }

    def _create_client_full_invoice(self, ro):
        """Scénario 1 : facture client intégrale."""
        vals = self._base_invoice_vals(ro, ro.customer_id, 'client_full')
        vals['invoice_line_ids'] = self._prepare_invoice_lines(ro)
        return self.env['account.move'].create(vals)

    def _create_insurance_split_invoices(self, ro):
        """Scénario 3 : facture assurance + facture franchise client."""
        if not ro.claim_id:
            raise UserError(
                "L'OR doit être lié à un sinistre pour la facturation "
                "assurance."
            )
        claim = ro.claim_id
        if not claim.insurance_company_id.partner_id:
            raise UserError(
                "La compagnie d'assurance doit avoir un partenaire associé."
            )

        franchise = claim.franchise_computed
        total_ht = ro.amount_untaxed
        insurance_amount = total_ht - franchise

        invoices = self.env['account.move']

        # Facture assurance (total - franchise)
        insurance_vals = self._base_invoice_vals(
            ro, claim.insurance_company_id.partner_id, 'insurance'
        )
        insurance_vals['invoice_line_ids'] = self._prepare_invoice_lines(ro)
        # Ajouter une ligne négative pour la franchise
        if franchise > 0:
            insurance_vals['invoice_line_ids'].append((0, 0, {
                'name': "Déduction franchise client",
                'quantity': 1,
                'price_unit': -franchise,
            }))
        invoices |= self.env['account.move'].create(insurance_vals)

        # Facture franchise client
        if franchise > 0:
            franchise_vals = self._base_invoice_vals(
                ro, ro.customer_id, 'franchise'
            )
            franchise_vals['invoice_line_ids'] = [(0, 0, {
                'name': "Franchise sinistre %s" % claim.name,
                'quantity': 1,
                'price_unit': franchise,
            })]
            invoices |= self.env['account.move'].create(franchise_vals)

        return invoices

    def _create_insurance_only_invoice(self, ro):
        """Scénario 4 : facture assurance seule (pas de franchise)."""
        if not ro.claim_id:
            raise UserError(
                "L'OR doit être lié à un sinistre pour la facturation "
                "assurance."
            )
        claim = ro.claim_id
        if not claim.insurance_company_id.partner_id:
            raise UserError(
                "La compagnie d'assurance doit avoir un partenaire associé."
            )

        vals = self._base_invoice_vals(
            ro, claim.insurance_company_id.partner_id, 'insurance'
        )
        vals['invoice_line_ids'] = self._prepare_invoice_lines(ro)
        return self.env['account.move'].create(vals)

    def _create_deposit_invoice(self, ro):
        """Scénario 5 : facture d'acompte."""
        if not self.deposit_amount or self.deposit_amount <= 0:
            raise UserError("Veuillez saisir un montant d'acompte positif.")

        vals = self._base_invoice_vals(ro, ro.customer_id, 'deposit')
        vals['invoice_line_ids'] = [(0, 0, {
            'name': "Acompte sur travaux — OR %s" % ro.name,
            'quantity': 1,
            'price_unit': self.deposit_amount,
        })]
        return self.env['account.move'].create(vals)

    def _create_partial_invoice(self, ro):
        """Scénario 7 : facture partielle (lignes terminées)."""
        done_lines = ro.line_ids.filtered(lambda l: l.is_done)
        if not done_lines:
            raise UserError(
                "Aucune ligne n'est marquée comme terminée."
            )

        vals = self._base_invoice_vals(ro, ro.customer_id, 'client_full')
        vals['invoice_line_ids'] = self._prepare_invoice_lines(
            ro, line_filter=lambda l: l.is_done
        )
        return self.env['account.move'].create(vals)

    def _create_courtesy_invoice(self, ro):
        """Scénario 8 : facturation dépassement véhicule courtoisie."""
        loan = ro.courtesy_loan_id
        if not loan:
            raise UserError(
                "Aucun prêt de courtoisie lié à cet OR."
            )
        if not loan.billable_days or loan.billable_days <= 0:
            raise UserError(
                "Aucun jour facturable sur le prêt de courtoisie."
            )

        rate = loan.courtesy_vehicle_id.daily_charge_rate or 0.0
        vals = self._base_invoice_vals(ro, ro.customer_id, 'courtesy_charge')
        vals['invoice_line_ids'] = [(0, 0, {
            'name': "Dépassement véhicule de courtoisie — %s jours × %.2f €" % (
                loan.billable_days, rate
            ),
            'quantity': loan.billable_days,
            'price_unit': rate,
        })]
        return self.env['account.move'].create(vals)
