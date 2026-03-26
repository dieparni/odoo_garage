"""Tests pour le modèle fleet.vehicle (extension garage)."""

from odoo.exceptions import ValidationError
from odoo.tests.common import TransactionCase


class TestGarageVehicle(TransactionCase):
    """Tests unitaires pour les champs et méthodes garage sur fleet.vehicle."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.brand = cls.env['fleet.vehicle.model.brand'].create({
            'name': 'Test Brand',
        })
        cls.model = cls.env['fleet.vehicle.model'].create({
            'name': 'Test Model',
            'brand_id': cls.brand.id,
        })
        cls.partner = cls.env['res.partner'].create({
            'name': 'Client Test',
            'is_garage_customer': True,
        })
        cls.vehicle = cls.env['fleet.vehicle'].create({
            'model_id': cls.model.id,
            'license_plate': 'AB-123-CD',
            'driver_id': cls.partner.id,
            'vin_sn': 'WVWZZZ3CZWE123456',
        })

    def test_garage_ref_sequence(self):
        """La référence garage est générée automatiquement."""
        self.assertTrue(self.vehicle.garage_ref)
        self.assertNotEqual(self.vehicle.garage_ref, 'Nouveau')

    def test_vin_validation_length(self):
        """Un VIN de longueur incorrecte lève une erreur."""
        with self.assertRaises(ValidationError):
            self.vehicle.write({'vin_sn': 'TOOCOURT'})

    def test_vin_validation_invalid_chars(self):
        """Un VIN avec I, O ou Q est rejeté."""
        with self.assertRaises(ValidationError):
            self.vehicle.write({'vin_sn': 'WVWZZZ3CZWI123456'})

    def test_vin_unique(self):
        """Deux véhicules ne peuvent pas avoir le même VIN."""
        with self.assertRaises(Exception):
            self.env['fleet.vehicle'].create({
                'model_id': self.model.id,
                'license_plate': 'EF-456-GH',
                'vin_sn': 'WVWZZZ3CZWE123456',
            })

    def test_compute_power_cv(self):
        """La conversion kW → CV est correcte."""
        self.vehicle.write({'power_kw': 100})
        self.assertEqual(self.vehicle.power_cv, 136)

    def test_compute_power_cv_zero(self):
        """Pas de kW → pas de CV."""
        self.vehicle.write({'power_kw': 0})
        self.assertEqual(self.vehicle.power_cv, 0)

    def test_compute_is_electric(self):
        """Le flag électrique est calculé selon le type de carburant."""
        self.vehicle.write({'fuel_type': 'electric'})
        self.assertTrue(self.vehicle.is_electric)
        self.vehicle.write({'fuel_type': 'diesel'})
        self.assertFalse(self.vehicle.is_electric)

    def test_compute_ct_next(self):
        """Le prochain CT est 1 an après le dernier."""
        from datetime import date
        self.vehicle.write({'ct_last_date': date(2024, 6, 15)})
        self.assertEqual(self.vehicle.ct_next_date, date(2025, 6, 15))

    def test_compute_warranty(self):
        """Le flag garantie est basé sur la date de fin."""
        from datetime import date, timedelta
        future = date.today() + timedelta(days=365)
        self.vehicle.write({'warranty_end_date': future})
        self.assertTrue(self.vehicle.is_under_warranty)

        past = date.today() - timedelta(days=1)
        self.vehicle.write({'warranty_end_date': past})
        self.assertFalse(self.vehicle.is_under_warranty)

    def test_paint_system(self):
        """On peut lier un système peinture au véhicule."""
        ps = self.env['garage.paint.system'].create({
            'name': 'Standox',
            'code': 'STX',
        })
        self.vehicle.write({'paint_system_id': ps.id})
        self.assertEqual(self.vehicle.paint_system_id.name, 'Standox')
