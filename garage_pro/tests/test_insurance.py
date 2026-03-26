"""Tests pour les modèles assurance et sinistre."""

from datetime import date

from odoo.exceptions import UserError
from odoo.tests.common import TransactionCase


class TestGarageInsurance(TransactionCase):
    """Tests unitaires pour les assurances et sinistres."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partner = cls.env['res.partner'].create({
            'name': 'Client Sinistre Test',
            'is_garage_customer': True,
        })
        cls.insurance_partner = cls.env['res.partner'].create({
            'name': 'AXA Belgium SA',
            'is_company': True,
        })
        cls.brand = cls.env['fleet.vehicle.model.brand'].create({
            'name': 'TestBrand',
        })
        cls.model = cls.env['fleet.vehicle.model'].create({
            'name': 'TestModel',
            'brand_id': cls.brand.id,
        })
        cls.vehicle = cls.env['fleet.vehicle'].create({
            'model_id': cls.model.id,
            'license_plate': 'INS-001-XX',
            'driver_id': cls.partner.id,
        })
        cls.insurance = cls.env['garage.insurance.company'].create({
            'name': 'AXA Belgium',
            'partner_id': cls.insurance_partner.id,
            'code': 'AXA',
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
        })

    def test_claim_sequence(self):
        """La référence sinistre est générée automatiquement."""
        self.assertTrue(self.claim.name.startswith('SIN/'))

    def test_claim_initial_state(self):
        """Un sinistre commence en brouillon."""
        self.assertEqual(self.claim.state, 'draft')

    def test_workflow_declare(self):
        """Brouillon → Déclaré."""
        self.claim.action_declare()
        self.assertEqual(self.claim.state, 'declared')
        self.assertTrue(self.claim.declaration_date)

    def test_workflow_request_expertise(self):
        """Déclaré → En attente expertise."""
        self.claim.action_declare()
        self.claim.action_request_expertise()
        self.assertEqual(self.claim.state, 'expertise_pending')

    def test_workflow_expertise_done(self):
        """En attente → Expertise réalisée."""
        self.claim.action_declare()
        self.claim.action_request_expertise()
        self.claim.action_expertise_done()
        self.assertEqual(self.claim.state, 'expertise_done')
        self.assertTrue(self.claim.expertise_done_date)

    def test_workflow_approve_requires_amount(self):
        """Approuver sans montant lève une erreur."""
        self.claim.action_declare()
        self.claim.action_request_expertise()
        self.claim.action_expertise_done()
        with self.assertRaises(UserError):
            self.claim.action_approve()

    def test_workflow_approve_with_amount(self):
        """Approuver avec montant fonctionne."""
        self.claim.action_declare()
        self.claim.action_request_expertise()
        self.claim.action_expertise_done()
        self.claim.write({'approved_amount': 2500.0})
        self.claim.action_approve()
        self.assertEqual(self.claim.state, 'approved')

    def test_workflow_vei(self):
        """Passage en VEI."""
        self.claim.action_declare()
        self.claim.action_mark_vei()
        self.assertEqual(self.claim.state, 'vei')
        self.assertTrue(self.claim.is_vei)
        self.assertEqual(self.claim.vei_customer_decision, 'pending')

    def test_workflow_cancel(self):
        """Annulation du sinistre."""
        self.claim.action_cancel()
        self.assertEqual(self.claim.state, 'cancelled')

    def test_compute_franchise_fixed(self):
        """Franchise fixe."""
        self.claim.write({
            'franchise_type': 'fixed',
            'franchise_amount': 500.0,
        })
        self.assertEqual(self.claim.franchise_computed, 500.0)

    def test_compute_franchise_percentage(self):
        """Franchise en pourcentage."""
        self.claim.write({
            'franchise_type': 'percentage',
            'franchise_percentage': 10.0,
            'estimated_amount': 3000.0,
        })
        self.assertEqual(self.claim.franchise_computed, 300.0)

    def test_compute_total_approved(self):
        """Total approuvé = montant + supplément approuvé."""
        self.claim.write({'approved_amount': 2000.0})
        supplement = self.env['garage.insurance.supplement'].create({
            'claim_id': self.claim.id,
            'name': 'Supplément test',
            'amount': 600.0,
            'approved_amount': 500.0,
            'state': 'approved',
        })
        self.claim.invalidate_recordset()
        self.assertEqual(self.claim.supplement_amount, 500.0)
        self.assertEqual(self.claim.total_approved, 2500.0)

    def test_insurance_company_claim_count(self):
        """Le compteur sinistres est correct."""
        self.insurance._compute_claim_count()
        self.assertEqual(self.insurance.claim_count, 1)

    def test_vehicle_claim_count(self):
        """Le compteur sinistres véhicule est correct."""
        self.vehicle._compute_claim_count()
        self.assertEqual(self.vehicle.claim_count, 1)

    def test_supplement(self):
        """Création et workflow supplément."""
        supplement = self.env['garage.insurance.supplement'].create({
            'claim_id': self.claim.id,
            'name': 'Pièce cachée endommagée',
            'amount': 350.0,
        })
        self.assertEqual(supplement.state, 'draft')
        supplement.action_send()
        self.assertEqual(supplement.state, 'sent')
        supplement.action_approve()
        self.assertEqual(supplement.state, 'approved')
        self.assertTrue(supplement.expert_response_date)

    def test_expert(self):
        """Création d'un expert lié à la compagnie."""
        expert = self.env['garage.insurance.expert'].create({
            'name': 'Jean Expert',
            'company_id': self.insurance.id,
            'phone': '+32 2 123 45 67',
            'expertise_type': 'on_site',
        })
        self.assertIn(expert, self.insurance.expert_contact_ids)
