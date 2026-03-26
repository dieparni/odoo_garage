"""Extension de account.move pour la facturation garage multi-payeur."""

from odoo import api, fields, models


class AccountMove(models.Model):
    """Extension facture Odoo avec champs spécifiques garage."""

    _inherit = 'account.move'

    # === LIENS GARAGE ===
    garage_repair_order_id = fields.Many2one(
        'garage.repair.order',
        string="OR garage",
        tracking=True,
    )
    garage_claim_id = fields.Many2one(
        'garage.insurance.claim',
        string="Sinistre",
        tracking=True,
    )

    # === TYPE FACTURE GARAGE ===
    is_garage_invoice = fields.Boolean(
        string="Facture garage",
        compute='_compute_is_garage',
        store=True,
    )
    garage_invoice_type = fields.Selection([
        ('client_full', 'Client (intégralité)'),
        ('insurance', 'Assurance'),
        ('franchise', 'Franchise client'),
        ('deposit', 'Acompte'),
        ('subcontract', 'Sous-traitance (achat)'),
        ('courtesy_charge', 'Facturation véhicule courtoisie'),
        ('warranty', 'Reprise garantie'),
    ], string="Type facture garage", tracking=True)

    # === INFOS AFFICHAGE ===
    garage_vehicle_id = fields.Many2one(
        'fleet.vehicle',
        string="Véhicule",
        related='garage_repair_order_id.vehicle_id',
        store=True,
    )
    garage_license_plate = fields.Char(
        string="Immatriculation",
        related='garage_vehicle_id.license_plate',
    )

    # ------------------------------------------------------------------
    # Compute
    # ------------------------------------------------------------------

    @api.depends('garage_repair_order_id')
    def _compute_is_garage(self):
        for rec in self:
            rec.is_garage_invoice = bool(rec.garage_repair_order_id)

    # ------------------------------------------------------------------
    # Overrides
    # ------------------------------------------------------------------

    def write(self, vals):
        res = super().write(vals)
        if 'payment_state' in vals:
            self._check_claim_paid()
        return res

    def _check_claim_paid(self):
        """Auto-transition claim to 'paid' when all invoices are paid."""
        for move in self:
            claim = move.garage_claim_id
            if not claim or claim.state != 'invoiced':
                continue
            ro = move.garage_repair_order_id
            if not ro:
                continue
            invoices = ro.invoice_ids.filtered(
                lambda m: m.state == 'posted'
                and m.move_type == 'out_invoice'
            )
            if invoices and all(
                inv.payment_state in ('paid', 'in_payment')
                for inv in invoices
            ):
                claim.action_mark_paid()
