"""Tests pour la sous-traitance et les véhicules de courtoisie."""

from datetime import date, timedelta

from odoo.tests.common import TransactionCase


class TestSubcontractBase(TransactionCase):
    """Setup commun pour les tests sous-traitance & courtoisie."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partner = cls.env['res.partner'].create({
            'name': 'Client Sous-traitance Test',
            'is_garage_customer': True,
        })
        cls.subcontractor = cls.env['res.partner'].create({
            'name': 'PDR Express',
            'is_garage_customer': True,
            'garage_customer_type': 'subcontractor',
        })
        cls.brand = cls.env['fleet.vehicle.model.brand'].create({
            'name': 'SubBrand',
        })
        cls.vmodel = cls.env['fleet.vehicle.model'].create({
            'name': 'SubModel',
            'brand_id': cls.brand.id,
        })
        cls.vehicle = cls.env['fleet.vehicle'].create({
            'model_id': cls.vmodel.id,
            'license_plate': 'SUB-001-XX',
            'driver_id': cls.partner.id,
        })
        cls.repair_order = cls.env['garage.repair.order'].create({
            'vehicle_id': cls.vehicle.id,
            'customer_id': cls.partner.id,
        })


class TestSubcontractOrder(TestSubcontractBase):
    """Tests bons de sous-traitance."""

    def _create_subcontract(self, **kwargs):
        vals = {
            'repair_order_id': self.repair_order.id,
            'subcontractor_id': self.subcontractor.id,
            'service_type': 'pdr',
            'estimated_cost': 250.0,
            'expected_return_date': date.today() + timedelta(days=5),
        }
        vals.update(kwargs)
        return self.env['garage.subcontract.order'].create(vals)

    def test_01_create_subcontract(self):
        """Création d'un bon de sous-traitance."""
        order = self._create_subcontract()
        self.assertEqual(order.state, 'draft')
        self.assertTrue(order.name.startswith('ST/'))

    def test_02_workflow_send(self):
        """Workflow : draft → sent."""
        order = self._create_subcontract()
        order.action_send()
        self.assertEqual(order.state, 'sent')
        self.assertEqual(order.send_date, date.today())

    def test_03_workflow_full(self):
        """Workflow complet : draft → sent → in_progress → done → invoiced."""
        order = self._create_subcontract()
        order.action_send()
        order.action_start()
        self.assertEqual(order.state, 'in_progress')
        order.action_done()
        self.assertEqual(order.state, 'done')
        self.assertEqual(order.actual_return_date, date.today())
        order.action_invoice()
        self.assertEqual(order.state, 'invoiced')

    def test_04_cancel_and_reset(self):
        """Annulation et remise en brouillon."""
        order = self._create_subcontract()
        order.action_cancel()
        self.assertEqual(order.state, 'cancelled')
        order.action_reset()
        self.assertEqual(order.state, 'draft')

    def test_05_is_late(self):
        """Détection de retard."""
        order = self._create_subcontract(
            expected_return_date=date.today() - timedelta(days=1),
        )
        order.action_send()
        order.action_start()
        order.invalidate_recordset()
        self.assertTrue(order.is_late)

    def test_06_not_late_when_done(self):
        """Pas en retard quand terminé."""
        order = self._create_subcontract(
            expected_return_date=date.today() - timedelta(days=1),
        )
        order.action_send()
        order.action_start()
        order.action_done()
        order.invalidate_recordset()
        self.assertFalse(order.is_late)

    def test_07_vehicle_related(self):
        """Le véhicule est récupéré depuis l'OR."""
        order = self._create_subcontract()
        self.assertEqual(order.vehicle_id, self.vehicle)

    def test_08_ro_subcontract_count(self):
        """Compteur sous-traitance sur l'OR."""
        self._create_subcontract()
        self.repair_order.invalidate_recordset()
        self.assertEqual(self.repair_order.subcontract_count, 1)

    def test_09_service_types(self):
        """Différents types de service."""
        for stype in ('glass', 'adas_calibration', 'towing'):
            order = self._create_subcontract(service_type=stype)
            self.assertEqual(order.service_type, stype)


class TestCourtesyVehicle(TestSubcontractBase):
    """Tests véhicules de courtoisie."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.courtesy_vehicle_fleet = cls.env['fleet.vehicle'].create({
            'model_id': cls.vmodel.id,
            'license_plate': 'CRT-001-XX',
        })
        cls.courtesy_vehicle = cls.env['garage.courtesy.vehicle'].create({
            'vehicle_id': cls.courtesy_vehicle_fleet.id,
            'daily_cost': 15.0,
            'daily_charge_rate': 25.0,
            'max_free_days': 3,
        })

    def test_01_create_courtesy(self):
        """Création d'un véhicule de courtoisie."""
        self.assertEqual(self.courtesy_vehicle.state, 'available')
        self.assertEqual(self.courtesy_vehicle.name, 'CRT-001-XX')

    def test_02_loan_count(self):
        """Compteur de prêts."""
        self.assertEqual(self.courtesy_vehicle.loan_count, 0)


class TestCourtesyLoan(TestSubcontractBase):
    """Tests prêts de courtoisie."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.courtesy_fleet = cls.env['fleet.vehicle'].create({
            'model_id': cls.vmodel.id,
            'license_plate': 'CRT-002-XX',
        })
        cls.courtesy_vehicle = cls.env['garage.courtesy.vehicle'].create({
            'vehicle_id': cls.courtesy_fleet.id,
            'daily_cost': 15.0,
            'daily_charge_rate': 25.0,
            'max_free_days': 3,
        })

    def _create_loan(self, **kwargs):
        vals = {
            'courtesy_vehicle_id': self.courtesy_vehicle.id,
            'customer_id': self.partner.id,
            'repair_order_id': self.repair_order.id,
        }
        vals.update(kwargs)
        return self.env['garage.courtesy.loan'].create(vals)

    def test_01_create_loan(self):
        """Création d'un prêt de courtoisie."""
        loan = self._create_loan()
        self.assertEqual(loan.state, 'reserved')

    def test_02_activate_loan(self):
        """Activation du prêt change le statut véhicule."""
        loan = self._create_loan()
        loan.action_activate()
        self.assertEqual(loan.state, 'active')
        self.assertTrue(loan.loan_start)
        self.assertEqual(self.courtesy_vehicle.state, 'loaned')
        self.assertEqual(self.courtesy_vehicle.current_loan_id, loan)

    def test_03_return_loan(self):
        """Restitution du véhicule."""
        loan = self._create_loan()
        loan.action_activate()
        loan.action_return()
        self.assertEqual(loan.state, 'returned')
        self.assertTrue(loan.loan_end)
        self.assertEqual(self.courtesy_vehicle.state, 'available')
        self.assertFalse(self.courtesy_vehicle.current_loan_id)

    def test_04_return_with_damage(self):
        """Restitution avec dommage."""
        loan = self._create_loan()
        loan.action_activate()
        loan.write({
            'has_damage': True,
            'damage_description': 'Rayure portière conducteur',
        })
        loan.action_return()
        self.assertEqual(loan.state, 'damaged')

    def test_05_billable_days(self):
        """Calcul des jours facturables."""
        loan = self._create_loan()
        loan.action_activate()
        # Simuler 5 jours
        loan.write({
            'loan_start': '2026-03-20 08:00:00',
            'loan_end': '2026-03-25 08:00:00',
        })
        loan.invalidate_recordset()
        self.assertEqual(loan.loan_days, 5)
        self.assertEqual(loan.billable_days, 2)  # 5 - 3 free days
        self.assertEqual(loan.billable_amount, 50.0)  # 2 * 25

    def test_06_no_billable_within_free(self):
        """Pas de facturation dans la période gratuite."""
        loan = self._create_loan()
        loan.action_activate()
        loan.write({
            'loan_start': '2026-03-20 08:00:00',
            'loan_end': '2026-03-22 08:00:00',
        })
        loan.invalidate_recordset()
        self.assertEqual(loan.loan_days, 2)
        self.assertEqual(loan.billable_days, 0)
        self.assertEqual(loan.billable_amount, 0.0)

    def test_07_ro_courtesy_flag(self):
        """Flag courtoisie sur l'OR."""
        loan = self._create_loan()
        self.repair_order.write({'courtesy_loan_id': loan.id})
        self.repair_order.invalidate_recordset()
        self.assertTrue(self.repair_order.has_courtesy_vehicle)
