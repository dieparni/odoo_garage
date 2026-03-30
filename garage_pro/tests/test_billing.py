"""Tests pour la facturation multi-payeur garage."""

from datetime import date

from odoo.exceptions import UserError
from odoo.tests.common import TransactionCase


class TestGarageBilling(TransactionCase):
    """Tests unitaires pour la facturation garage multi-payeur."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Journal de vente (requis pour créer des account.move de type sale en Odoo 19)
        cls.journal_sale = cls.env['account.journal'].create({
            'name': 'Test Sale Journal',
            'type': 'sale',
            'code': 'TSLG',
            'company_id': cls.env.company.id,
        })
        # Client
        cls.partner = cls.env['res.partner'].create({
            'name': 'Client Facturation Test',
            'is_garage_customer': True,
        })
        # Assurance
        cls.insurance_partner = cls.env['res.partner'].create({
            'name': 'AXA Belgium SA',
            'is_company': True,
        })
        cls.insurance = cls.env['garage.insurance.company'].create({
            'name': 'AXA Belgium',
            'partner_id': cls.insurance_partner.id,
            'code': 'AXA',
            'convention_type': 'direct',
            'hourly_rate_bodywork': 55.0,
            'hourly_rate_paint': 55.0,
        })
        # Véhicule
        cls.brand = cls.env['fleet.vehicle.model.brand'].create({
            'name': 'TestBrandBill',
        })
        cls.model = cls.env['fleet.vehicle.model'].create({
            'name': 'TestModelBill',
            'brand_id': cls.brand.id,
        })
        cls.vehicle = cls.env['fleet.vehicle'].create({
            'model_id': cls.model.id,
            'license_plate': 'BILL-001',
            'driver_id': cls.partner.id,
        })

    def _create_repair_order(self, with_claim=False, franchise=0.0):
        """Crée un OR avec des lignes, optionnellement lié à un sinistre."""
        vals = {
            'vehicle_id': self.vehicle.id,
            'customer_id': self.partner.id,
        }
        if with_claim:
            claim = self.env['garage.insurance.claim'].create({
                'vehicle_id': self.vehicle.id,
                'customer_id': self.partner.id,
                'insurance_company_id': self.insurance.id,
                'claim_date': date(2026, 1, 15),
                'claim_type': 'collision',
                'franchise_type': 'fixed' if franchise else 'none',
                'franchise_amount': franchise,
            })
            vals['claim_id'] = claim.id

        ro = self.env['garage.repair.order'].create(vals)
        # Ajouter des lignes
        self.env['garage.repair.order.line'].create({
            'repair_order_id': ro.id,
            'name': 'Carrosserie pare-chocs',
            'line_type': 'labor_body',
            'allocated_time': 3.0,
            'hourly_rate': 55.0,
            'quantity': 1,
            'unit_price': 165.0,
        })
        self.env['garage.repair.order.line'].create({
            'repair_order_id': ro.id,
            'name': 'Pare-chocs neuf',
            'line_type': 'parts',
            'quantity': 1,
            'unit_price': 350.0,
        })
        return ro

    def _advance_ro_to_delivered(self, ro):
        """Avance un OR jusqu'à livré."""
        ro.action_confirm()
        ro.action_start()
        ro.action_request_qc()
        ro.action_validate_qc()
        ro.action_ready()
        ro.action_deliver()

    # ------------------------------------------------------------------
    # Tests account.move extension
    # ------------------------------------------------------------------

    def test_account_move_garage_fields(self):
        """Les champs garage sont présents sur account.move."""
        move = self.env['account.move'].create({
            'move_type': 'out_invoice',
            'partner_id': self.partner.id,
        })
        self.assertFalse(move.is_garage_invoice)
        self.assertFalse(move.garage_repair_order_id)

    def test_is_garage_invoice_computed(self):
        """is_garage_invoice est True si lié à un OR."""
        ro = self._create_repair_order()
        move = self.env['account.move'].create({
            'move_type': 'out_invoice',
            'partner_id': self.partner.id,
            'garage_repair_order_id': ro.id,
        })
        self.assertTrue(move.is_garage_invoice)

    # ------------------------------------------------------------------
    # Tests repair_order invoice fields
    # ------------------------------------------------------------------

    def test_ro_invoice_count_initial(self):
        """Un OR sans facture a invoice_count = 0."""
        ro = self._create_repair_order()
        self.assertEqual(ro.invoice_count, 0)
        self.assertEqual(ro.invoice_status, 'no')

    def test_ro_invoice_status_to_invoice(self):
        """Un OR livré sans facture est 'à facturer'."""
        ro = self._create_repair_order()
        self._advance_ro_to_delivered(ro)
        self.assertEqual(ro.invoice_status, 'to_invoice')

    # ------------------------------------------------------------------
    # Tests wizard — scénario client intégral
    # ------------------------------------------------------------------

    def test_wizard_client_full(self):
        """Facturation client intégrale depuis le wizard."""
        ro = self._create_repair_order()
        self._advance_ro_to_delivered(ro)

        wizard = self.env['garage.invoice.wizard'].create({
            'repair_order_id': ro.id,
            'invoice_scenario': 'client_full',
        })
        result = wizard.action_create_invoices()

        self.assertEqual(ro.state, 'invoiced')
        self.assertEqual(ro.invoice_count, 1)
        invoice = ro.invoice_ids[0]
        self.assertEqual(invoice.partner_id, self.partner)
        self.assertEqual(invoice.garage_invoice_type, 'client_full')
        self.assertTrue(invoice.is_garage_invoice)
        # 2 lignes : MO + pièce
        self.assertEqual(len(invoice.invoice_line_ids), 2)

    def test_wizard_client_full_amounts(self):
        """Les montants de la facture client correspondent à l'OR."""
        ro = self._create_repair_order()
        self._advance_ro_to_delivered(ro)

        wizard = self.env['garage.invoice.wizard'].create({
            'repair_order_id': ro.id,
            'invoice_scenario': 'client_full',
        })
        wizard.action_create_invoices()

        invoice = ro.invoice_ids[0]
        # MO : 3h × 55€ = 165€, Pièce : 350€ → Total HT = 515€
        line_total = sum(invoice.invoice_line_ids.mapped('price_subtotal'))
        self.assertAlmostEqual(line_total, 515.0, places=2)

    # ------------------------------------------------------------------
    # Tests wizard — scénario assurance + franchise
    # ------------------------------------------------------------------

    def test_wizard_insurance_split(self):
        """Facturation assurance + franchise crée 2 factures."""
        ro = self._create_repair_order(with_claim=True, franchise=250.0)
        self._advance_ro_to_delivered(ro)

        wizard = self.env['garage.invoice.wizard'].create({
            'repair_order_id': ro.id,
            'invoice_scenario': 'insurance_split',
        })
        wizard.action_create_invoices()

        self.assertEqual(ro.state, 'invoiced')
        self.assertEqual(ro.invoice_count, 2)

        insurance_inv = ro.invoice_ids.filtered(
            lambda i: i.garage_invoice_type == 'insurance'
        )
        franchise_inv = ro.invoice_ids.filtered(
            lambda i: i.garage_invoice_type == 'franchise'
        )
        self.assertEqual(len(insurance_inv), 1)
        self.assertEqual(len(franchise_inv), 1)
        self.assertEqual(insurance_inv.partner_id, self.insurance_partner)
        self.assertEqual(franchise_inv.partner_id, self.partner)

    def test_wizard_insurance_split_franchise_amount(self):
        """La facture franchise contient le bon montant."""
        ro = self._create_repair_order(with_claim=True, franchise=250.0)
        self._advance_ro_to_delivered(ro)

        wizard = self.env['garage.invoice.wizard'].create({
            'repair_order_id': ro.id,
            'invoice_scenario': 'insurance_split',
        })
        wizard.action_create_invoices()

        franchise_inv = ro.invoice_ids.filtered(
            lambda i: i.garage_invoice_type == 'franchise'
        )
        line = franchise_inv.invoice_line_ids[0]
        self.assertAlmostEqual(line.price_unit, 250.0, places=2)

    def test_wizard_insurance_split_no_claim_error(self):
        """Erreur si facturation assurance sans sinistre."""
        ro = self._create_repair_order(with_claim=False)
        self._advance_ro_to_delivered(ro)

        wizard = self.env['garage.invoice.wizard'].create({
            'repair_order_id': ro.id,
            'invoice_scenario': 'insurance_split',
        })
        with self.assertRaises(UserError):
            wizard.action_create_invoices()

    # ------------------------------------------------------------------
    # Tests wizard — assurance seule
    # ------------------------------------------------------------------

    def test_wizard_insurance_only(self):
        """Facturation assurance seule (pas de franchise)."""
        ro = self._create_repair_order(with_claim=True, franchise=0.0)
        self._advance_ro_to_delivered(ro)

        wizard = self.env['garage.invoice.wizard'].create({
            'repair_order_id': ro.id,
            'invoice_scenario': 'insurance_only',
        })
        wizard.action_create_invoices()

        self.assertEqual(ro.state, 'invoiced')
        self.assertEqual(ro.invoice_count, 1)
        invoice = ro.invoice_ids[0]
        self.assertEqual(invoice.partner_id, self.insurance_partner)
        self.assertEqual(invoice.garage_invoice_type, 'insurance')

    # ------------------------------------------------------------------
    # Tests wizard — acompte
    # ------------------------------------------------------------------

    def test_wizard_deposit(self):
        """Création d'une facture d'acompte."""
        ro = self._create_repair_order()
        self._advance_ro_to_delivered(ro)

        wizard = self.env['garage.invoice.wizard'].create({
            'repair_order_id': ro.id,
            'invoice_scenario': 'deposit',
            'deposit_amount': 200.0,
        })
        wizard.action_create_invoices()

        # L'acompte ne passe pas l'OR en 'invoiced'
        self.assertNotEqual(ro.state, 'invoiced')
        deposit_inv = ro.invoice_ids.filtered(
            lambda i: i.garage_invoice_type == 'deposit'
        )
        self.assertEqual(len(deposit_inv), 1)
        self.assertAlmostEqual(
            deposit_inv.invoice_line_ids[0].price_unit, 200.0, places=2
        )

    def test_wizard_deposit_zero_error(self):
        """Erreur si acompte avec montant 0."""
        ro = self._create_repair_order()
        self._advance_ro_to_delivered(ro)

        wizard = self.env['garage.invoice.wizard'].create({
            'repair_order_id': ro.id,
            'invoice_scenario': 'deposit',
            'deposit_amount': 0.0,
        })
        with self.assertRaises(UserError):
            wizard.action_create_invoices()

    # ------------------------------------------------------------------
    # Tests wizard — facture partielle
    # ------------------------------------------------------------------

    def test_wizard_partial(self):
        """Facture partielle ne prend que les lignes terminées."""
        ro = self._create_repair_order()
        self._advance_ro_to_delivered(ro)

        # Marquer la première ligne comme terminée
        ro.line_ids[0].write({'is_done': True})

        wizard = self.env['garage.invoice.wizard'].create({
            'repair_order_id': ro.id,
            'invoice_scenario': 'partial',
        })
        wizard.action_create_invoices()

        # L'OR ne passe pas en 'invoiced' (partiel)
        self.assertNotEqual(ro.state, 'invoiced')
        invoice = ro.invoice_ids[0]
        # Seule 1 ligne doit être facturée
        self.assertEqual(len(invoice.invoice_line_ids), 1)

    def test_wizard_partial_no_done_lines_error(self):
        """Erreur si facture partielle sans lignes terminées."""
        ro = self._create_repair_order()
        self._advance_ro_to_delivered(ro)

        wizard = self.env['garage.invoice.wizard'].create({
            'repair_order_id': ro.id,
            'invoice_scenario': 'partial',
        })
        with self.assertRaises(UserError):
            wizard.action_create_invoices()

    # ------------------------------------------------------------------
    # Tests wizard — état OR invalide
    # ------------------------------------------------------------------

    def test_wizard_draft_or_error(self):
        """Erreur si on tente de facturer un OR en brouillon."""
        ro = self._create_repair_order()
        wizard = self.env['garage.invoice.wizard'].create({
            'repair_order_id': ro.id,
            'invoice_scenario': 'client_full',
        })
        with self.assertRaises(UserError):
            wizard.action_create_invoices()

    # ------------------------------------------------------------------
    # Tests action OR
    # ------------------------------------------------------------------

    def test_ro_action_view_invoices(self):
        """L'action d'affichage des factures retourne le bon domain."""
        ro = self._create_repair_order()
        self._advance_ro_to_delivered(ro)

        wizard = self.env['garage.invoice.wizard'].create({
            'repair_order_id': ro.id,
            'invoice_scenario': 'client_full',
        })
        wizard.action_create_invoices()

        action = ro.action_view_invoices()
        self.assertEqual(action['res_model'], 'account.move')
        self.assertIn(ro.invoice_ids[0].id, action['domain'][0][2])

    def test_ro_action_credit_note(self):
        """Création d'un avoir depuis l'OR."""
        ro = self._create_repair_order()
        self._advance_ro_to_delivered(ro)

        action = ro.action_create_credit_note()
        self.assertEqual(action['res_model'], 'account.move')
        credit = self.env['account.move'].browse(action['res_id'])
        self.assertEqual(credit.move_type, 'out_refund')
        self.assertEqual(credit.garage_repair_order_id, ro)

    # ------------------------------------------------------------------
    # Tests customer invoice stats
    # ------------------------------------------------------------------

    def test_customer_invoice_stats_initial(self):
        """Stats facturation garage sont à 0 initialement."""
        self.assertEqual(self.partner.total_invoiced_garage, 0.0)
        self.assertEqual(self.partner.outstanding_garage_balance, 0.0)
        self.assertEqual(self.partner.garage_invoice_count, 0)

    def test_customer_last_visit_date(self):
        """La date de dernière visite est calculée correctement."""
        ro = self._create_repair_order()
        self._advance_ro_to_delivered(ro)
        self.assertEqual(self.partner.last_visit_date, date.today())

    # ------------------------------------------------------------------
    # Tests wizard — ouvrir depuis l'OR
    # ------------------------------------------------------------------

    def test_open_invoice_wizard(self):
        """L'action d'ouverture du wizard retourne les bonnes valeurs."""
        ro = self._create_repair_order()
        action = ro.action_open_invoice_wizard()
        self.assertEqual(action['res_model'], 'garage.invoice.wizard')
        self.assertEqual(action['target'], 'new')
        self.assertEqual(
            action['context']['default_repair_order_id'], ro.id
        )

    # ------------------------------------------------------------------
    # Tests fiscal position on invoice
    # ------------------------------------------------------------------

    def test_wizard_applies_fiscal_position(self):
        """Le wizard applique la position fiscale du partenaire."""
        fp = self.env['account.fiscal.position'].create({
            'name': 'Intracom LU Test',
            'auto_apply': True,
            'vat_required': True,
        })
        lu_partner = self.env['res.partner'].create({
            'name': 'Client LU',
            'is_garage_customer': True,
            'property_account_position_id': fp.id,
        })
        ro = self._create_repair_order()
        ro.write({'customer_id': lu_partner.id})
        self._advance_ro_to_delivered(ro)

        wizard = self.env['garage.invoice.wizard'].create({
            'repair_order_id': ro.id,
            'invoice_scenario': 'client_full',
        })
        action = wizard.action_create_invoices()
        invoice = self.env['account.move'].browse(action['res_id'])
        self.assertEqual(invoice.fiscal_position_id, fp)

    # ------------------------------------------------------------------
    # Tests shortfall invoice scenario
    # ------------------------------------------------------------------

    def test_wizard_shortfall_no_claim_error(self):
        """Erreur si scénario shortfall sans sinistre."""
        ro = self._create_repair_order(with_claim=False)
        self._advance_ro_to_delivered(ro)

        wizard = self.env['garage.invoice.wizard'].create({
            'repair_order_id': ro.id,
            'invoice_scenario': 'shortfall_client',
        })
        with self.assertRaises(UserError):
            wizard.action_create_invoices()

    def test_insurance_shortfall_fields(self):
        """Les champs shortfall sont présents sur le sinistre."""
        claim = self.env['garage.insurance.claim'].create({
            'vehicle_id': self.vehicle.id,
            'customer_id': self.partner.id,
            'insurance_company_id': self.insurance.id,
            'claim_date': date(2026, 1, 20),
            'claim_type': 'collision',
        })
        self.assertEqual(claim.insurance_shortfall, 0.0)
        self.assertEqual(claim.shortfall_action, 'none')
