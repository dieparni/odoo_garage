"""Tests pour l'extension res.partner (clients garage)."""

from odoo.exceptions import ValidationError
from odoo.tests.common import TransactionCase


class TestGarageCustomer(TransactionCase):
    """Tests unitaires pour les champs et méthodes garage sur res.partner."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.customer = cls.env['res.partner'].create({
            'name': 'Client Garage Test',
            'is_garage_customer': True,
            'garage_customer_type': 'private',
        })

    def test_is_garage_customer(self):
        """Le flag client garage est correctement positionné."""
        self.assertTrue(self.customer.is_garage_customer)

    def test_compute_is_leasing(self):
        """Le flag leasing est calculé à partir du type client."""
        self.customer.write({'garage_customer_type': 'leasing_company'})
        self.assertTrue(self.customer.is_leasing_company)
        self.customer.write({'garage_customer_type': 'private'})
        self.assertFalse(self.customer.is_leasing_company)

    def test_compute_is_insurance(self):
        """Le flag assurance est calculé à partir du type client."""
        self.customer.write({'garage_customer_type': 'insurance_company'})
        self.assertTrue(self.customer.is_insurance_company)

    def test_compute_is_subcontractor(self):
        """Le flag sous-traitant est calculé à partir du type client."""
        self.customer.write({'garage_customer_type': 'subcontractor'})
        self.assertTrue(self.customer.is_subcontractor)

    def test_blocked_requires_reason(self):
        """Bloquer un client sans raison lève une erreur."""
        with self.assertRaises(ValidationError):
            self.customer.write({
                'is_blocked_garage': True,
                'blocked_reason': False,
            })

    def test_blocked_with_reason_ok(self):
        """Bloquer un client avec raison fonctionne."""
        self.customer.write({
            'is_blocked_garage': True,
            'blocked_reason': 'Impayé',
        })
        self.assertTrue(self.customer.is_blocked_garage)

    def test_vehicle_count(self):
        """Le compteur de véhicules est correct."""
        brand = self.env['fleet.vehicle.model.brand'].create({
            'name': 'Test Brand',
        })
        model = self.env['fleet.vehicle.model'].create({
            'name': 'Test Model',
            'brand_id': brand.id,
        })
        self.env['fleet.vehicle'].create({
            'model_id': model.id,
            'license_plate': 'ZZ-999-ZZ',
            'driver_id': self.customer.id,
        })
        self.customer._compute_vehicle_count()
        self.assertEqual(self.customer.vehicle_count, 1)

    def test_action_view_vehicles(self):
        """L'action ouvre la liste des véhicules du client."""
        result = self.customer.action_view_vehicles()
        self.assertEqual(result['res_model'], 'fleet.vehicle')
        self.assertEqual(result['type'], 'ir.actions.act_window')
