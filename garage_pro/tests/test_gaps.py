"""Tests pour les gaps spec comblés (agent 16)."""

from datetime import date

from odoo.exceptions import UserError
from odoo.tests.common import TransactionCase


class TestVehicleTotalSpent(TransactionCase):
    """Tests pour vehicle.total_spent."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partner = cls.env['res.partner'].create({
            'name': 'Client Total Spent',
            'is_garage_customer': True,
        })
        cls.brand = cls.env['fleet.vehicle.model.brand'].create({
            'name': 'SpentBrand',
        })
        cls.model = cls.env['fleet.vehicle.model'].create({
            'name': 'SpentModel',
            'brand_id': cls.brand.id,
        })
        cls.vehicle = cls.env['fleet.vehicle'].create({
            'model_id': cls.model.id,
            'license_plate': 'TS-001-XX',
            'driver_id': cls.partner.id,
        })

    def test_01_total_spent_no_orders(self):
        """Véhicule sans OR → total_spent = 0."""
        self.assertEqual(self.vehicle.total_spent, 0.0)

    def test_02_total_spent_with_confirmed_order(self):
        """Total dépensé inclut les OR confirmés."""
        ro = self.env['garage.repair.order'].create({
            'vehicle_id': self.vehicle.id,
            'customer_id': self.partner.id,
        })
        self.env['garage.repair.order.line'].create({
            'repair_order_id': ro.id,
            'name': 'Test MO',
            'line_type': 'labor_body',
            'quantity': 5.0,
            'unit_price': 55.0,
        })
        ro.action_confirm()
        self.vehicle.invalidate_recordset(['total_spent'])
        self.assertGreater(self.vehicle.total_spent, 0.0)

    def test_03_total_spent_excludes_draft(self):
        """Total dépensé exclut les OR brouillon."""
        ro = self.env['garage.repair.order'].create({
            'vehicle_id': self.vehicle.id,
            'customer_id': self.partner.id,
        })
        self.env['garage.repair.order.line'].create({
            'repair_order_id': ro.id,
            'name': 'Draft MO',
            'line_type': 'labor_body',
            'quantity': 10.0,
            'unit_price': 55.0,
        })
        self.vehicle.invalidate_recordset(['total_spent'])
        self.assertEqual(self.vehicle.total_spent, 0.0)


class TestQuotationInsuranceSplit(TransactionCase):
    """Tests pour quotation.insurance_amount / franchise_amount_computed."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partner = cls.env['res.partner'].create({
            'name': 'Client Split Test',
            'is_garage_customer': True,
        })
        ins_partner = cls.env['res.partner'].create({
            'name': 'Insurance Split SA',
            'is_company': True,
        })
        cls.brand = cls.env['fleet.vehicle.model.brand'].create({
            'name': 'SplitBrand',
        })
        cls.model_v = cls.env['fleet.vehicle.model'].create({
            'name': 'SplitModel',
            'brand_id': cls.brand.id,
        })
        cls.vehicle = cls.env['fleet.vehicle'].create({
            'model_id': cls.model_v.id,
            'license_plate': 'SP-001-XX',
            'driver_id': cls.partner.id,
        })
        cls.insurance = cls.env['garage.insurance.company'].create({
            'name': 'Split Insurance',
            'partner_id': ins_partner.id,
            'code': 'SPLIT',
            'convention_type': 'direct',
            'hourly_rate_bodywork': 55.0,
            'hourly_rate_paint': 55.0,
        })
        cls.claim = cls.env['garage.insurance.claim'].create({
            'vehicle_id': cls.vehicle.id,
            'customer_id': cls.partner.id,
            'insurance_company_id': cls.insurance.id,
            'claim_date': date(2026, 1, 15),
            'claim_type': 'collision',
            'franchise_type': 'fixed',
            'franchise_amount': 250.0,
        })

    def test_01_no_claim_no_split(self):
        """Devis sans sinistre → pas de split."""
        quotation = self.env['garage.quotation'].create({
            'vehicle_id': self.vehicle.id,
            'customer_id': self.partner.id,
        })
        self.env['garage.quotation.line'].create({
            'quotation_id': quotation.id,
            'name': 'MO Test',
            'line_type': 'labor_body',
            'quantity': 2.0,
            'unit_price': 55.0,
        })
        self.assertEqual(quotation.insurance_amount, 0.0)
        self.assertEqual(quotation.franchise_amount_computed, 0.0)

    def test_02_with_claim_split(self):
        """Devis avec sinistre → franchise déduite du total."""
        quotation = self.env['garage.quotation'].create({
            'vehicle_id': self.vehicle.id,
            'customer_id': self.partner.id,
            'claim_id': self.claim.id,
        })
        self.env['garage.quotation.line'].create({
            'quotation_id': quotation.id,
            'name': 'MO Collision',
            'line_type': 'labor_body',
            'quantity': 10.0,
            'unit_price': 55.0,
        })
        # amount_total = 550 HT + TVA
        self.assertGreater(quotation.amount_total, 0.0)
        self.assertEqual(quotation.franchise_amount_computed, 250.0)
        self.assertAlmostEqual(
            quotation.insurance_amount,
            quotation.amount_total - 250.0,
            places=2,
        )

    def test_03_franchise_capped_at_total(self):
        """Si franchise > total → franchise = total, assurance = 0."""
        self.claim.write({'franchise_amount': 99999.0})
        quotation = self.env['garage.quotation'].create({
            'vehicle_id': self.vehicle.id,
            'customer_id': self.partner.id,
            'claim_id': self.claim.id,
        })
        self.env['garage.quotation.line'].create({
            'quotation_id': quotation.id,
            'name': 'Petite MO',
            'line_type': 'labor_body',
            'quantity': 1.0,
            'unit_price': 10.0,
        })
        self.assertAlmostEqual(
            quotation.franchise_amount_computed,
            quotation.amount_total,
            places=2,
        )
        self.assertAlmostEqual(quotation.insurance_amount, 0.0, places=2)


class TestClaimWorkflowGaps(TransactionCase):
    """Tests pour action_start_work et action_request_supplement."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partner = cls.env['res.partner'].create({
            'name': 'Client Workflow Gaps',
            'is_garage_customer': True,
        })
        ins_partner = cls.env['res.partner'].create({
            'name': 'Insurance WF SA',
            'is_company': True,
        })
        cls.brand = cls.env['fleet.vehicle.model.brand'].create({
            'name': 'WFBrand',
        })
        cls.model_v = cls.env['fleet.vehicle.model'].create({
            'name': 'WFModel',
            'brand_id': cls.brand.id,
        })
        cls.vehicle = cls.env['fleet.vehicle'].create({
            'model_id': cls.model_v.id,
            'license_plate': 'WF-001-XX',
            'driver_id': cls.partner.id,
        })
        cls.insurance = cls.env['garage.insurance.company'].create({
            'name': 'WF Insurance',
            'partner_id': ins_partner.id,
            'code': 'WF',
            'convention_type': 'direct',
            'hourly_rate_bodywork': 55.0,
            'hourly_rate_paint': 55.0,
        })
        cls.claim = cls.env['garage.insurance.claim'].create({
            'vehicle_id': cls.vehicle.id,
            'customer_id': cls.partner.id,
            'insurance_company_id': cls.insurance.id,
            'claim_date': date(2026, 2, 1),
            'claim_type': 'collision',
            'franchise_type': 'fixed',
            'franchise_amount': 300.0,
        })

    def test_01_start_work_no_ro_raises(self):
        """action_start_work sans OR → erreur."""
        self.claim.action_declare()
        self.claim.action_request_expertise()
        self.claim.action_expertise_done()
        self.claim.write({'approved_amount': 2000.0})
        self.claim.action_approve()
        with self.assertRaises(UserError):
            self.claim.action_start_work()

    def test_02_start_work_with_ro(self):
        """action_start_work avec OR → passe en work_in_progress."""
        self.claim.action_declare()
        self.claim.action_request_expertise()
        self.claim.action_expertise_done()
        self.claim.write({'approved_amount': 2000.0})
        self.claim.action_approve()
        ro = self.env['garage.repair.order'].create({
            'vehicle_id': self.vehicle.id,
            'customer_id': self.partner.id,
            'claim_id': self.claim.id,
        })
        self.claim.write({'repair_order_id': ro.id})
        self.claim.action_start_work()
        self.assertEqual(self.claim.state, 'work_in_progress')

    def test_03_request_supplement_returns_wizard(self):
        """action_request_supplement retourne une action wizard."""
        self.claim.write({'state': 'approved'})
        result = self.claim.action_request_supplement()
        self.assertEqual(result['res_model'], 'garage.insurance.supplement.wizard')
        self.assertEqual(result['target'], 'new')

    def test_04_supplement_wizard_creates_supplement(self):
        """Le wizard crée un supplément et passe le sinistre en supplement_pending."""
        self.claim.write({'state': 'approved'})
        wizard = self.env['garage.insurance.supplement.wizard'].create({
            'claim_id': self.claim.id,
            'name': 'Travaux cachés',
            'amount': 500.0,
        })
        wizard.action_confirm()
        self.assertEqual(self.claim.state, 'supplement_pending')
        self.assertEqual(len(self.claim.supplement_ids), 1)
        self.assertEqual(self.claim.supplement_ids.state, 'sent')

    def test_05_supplement_wizard_zero_amount_raises(self):
        """Wizard avec montant 0 → erreur."""
        self.claim.write({'state': 'approved'})
        wizard = self.env['garage.insurance.supplement.wizard'].create({
            'claim_id': self.claim.id,
            'name': 'Zero amount',
            'amount': 0.0,
        })
        with self.assertRaises(UserError):
            wizard.action_confirm()
