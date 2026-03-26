"""Tests pour devis et ordres de réparation."""

from odoo.exceptions import UserError
from odoo.tests.common import TransactionCase


class TestGarageQuotation(TransactionCase):
    """Tests unitaires pour devis et conversion en OR."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partner = cls.env['res.partner'].create({
            'name': 'Client Devis Test',
            'is_garage_customer': True,
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
            'license_plate': 'DEV-001-XX',
            'driver_id': cls.partner.id,
        })

    def _create_quotation(self, lines=None):
        """Crée un devis avec des lignes optionnelles."""
        quotation = self.env['garage.quotation'].create({
            'vehicle_id': self.vehicle.id,
            'customer_id': self.partner.id,
        })
        if lines:
            for line_vals in lines:
                line_vals['quotation_id'] = quotation.id
                self.env['garage.quotation.line'].create(line_vals)
        return quotation

    def test_quotation_sequence(self):
        """La référence devis est générée automatiquement."""
        quotation = self._create_quotation()
        self.assertTrue(quotation.name.startswith('DEV/'))

    def test_quotation_initial_state(self):
        """Un devis commence en brouillon."""
        quotation = self._create_quotation()
        self.assertEqual(quotation.state, 'draft')

    def test_workflow_send(self):
        """Brouillon → Envoyé."""
        quotation = self._create_quotation()
        quotation.action_send()
        self.assertEqual(quotation.state, 'sent')
        self.assertTrue(quotation.date_sent)

    def test_workflow_approve(self):
        """Envoyé → Accepté."""
        quotation = self._create_quotation()
        quotation.action_send()
        quotation.action_approve()
        self.assertEqual(quotation.state, 'approved')
        self.assertTrue(quotation.date_approved)

    def test_workflow_refuse(self):
        """Envoyé → Refusé."""
        quotation = self._create_quotation()
        quotation.action_send()
        quotation.action_refuse()
        self.assertEqual(quotation.state, 'refused')

    def test_compute_amounts_labor(self):
        """Calcul des montants MO."""
        quotation = self._create_quotation([{
            'name': 'Carrosserie capot',
            'line_type': 'labor_body',
            'allocated_time': 3.0,
            'hourly_rate': 55.0,
            'quantity': 1,
            'unit_price': 0,
        }])
        self.assertEqual(quotation.amount_labor, 165.0)
        self.assertEqual(quotation.amount_untaxed, 165.0)

    def test_compute_amounts_parts(self):
        """Calcul des montants pièces."""
        quotation = self._create_quotation([{
            'name': 'Pare-chocs avant',
            'line_type': 'parts',
            'quantity': 1,
            'unit_price': 350.0,
        }])
        self.assertEqual(quotation.amount_parts, 350.0)

    def test_compute_amounts_discount(self):
        """Calcul avec remise globale."""
        quotation = self._create_quotation([{
            'name': 'Carrosserie',
            'line_type': 'labor_body',
            'allocated_time': 10.0,
            'hourly_rate': 55.0,
            'quantity': 1,
            'unit_price': 0,
        }])
        quotation.write({'global_discount_rate': 10.0})
        self.assertAlmostEqual(quotation.amount_untaxed, 495.0, places=2)

    def test_line_compute_total_labor(self):
        """Ligne MO : total = temps * taux horaire."""
        quotation = self._create_quotation()
        line = self.env['garage.quotation.line'].create({
            'quotation_id': quotation.id,
            'name': 'Peinture aile',
            'line_type': 'labor_paint',
            'allocated_time': 2.5,
            'hourly_rate': 55.0,
            'quantity': 1,
            'unit_price': 0,
        })
        self.assertEqual(line.amount_total, 137.5)

    def test_line_compute_total_parts(self):
        """Ligne pièces : total = qté * PU * (1 - remise)."""
        quotation = self._create_quotation()
        line = self.env['garage.quotation.line'].create({
            'quotation_id': quotation.id,
            'name': 'Filtre à huile',
            'line_type': 'parts',
            'quantity': 2,
            'unit_price': 15.0,
            'discount': 10.0,
        })
        self.assertEqual(line.amount_total, 27.0)

    def test_convert_to_repair_order(self):
        """Conversion devis → OR."""
        quotation = self._create_quotation([{
            'name': 'Redressage aile',
            'line_type': 'labor_body',
            'allocated_time': 4.0,
            'hourly_rate': 55.0,
            'quantity': 1,
            'unit_price': 0,
        }])
        quotation.action_send()
        quotation.action_approve()
        result = quotation.action_convert_to_repair_order()
        self.assertEqual(quotation.state, 'converted')
        self.assertTrue(quotation.repair_order_id)
        ro = quotation.repair_order_id
        self.assertEqual(ro.vehicle_id, self.vehicle)
        self.assertEqual(ro.customer_id, self.partner)
        self.assertEqual(len(ro.line_ids), 1)
        self.assertTrue(ro.name.startswith('OR/'))

    def test_convert_blocked_customer(self):
        """Conversion refuse si client bloqué."""
        self.partner.write({
            'is_blocked_garage': True,
            'blocked_reason': 'Impayé',
        })
        quotation = self._create_quotation()
        quotation.action_send()
        quotation.action_approve()
        with self.assertRaises(UserError):
            quotation.action_convert_to_repair_order()
        # Cleanup
        self.partner.write({
            'is_blocked_garage': False,
            'blocked_reason': False,
        })

    def test_convert_requires_approved(self):
        """Conversion refuse si pas accepté."""
        quotation = self._create_quotation()
        with self.assertRaises(UserError):
            quotation.action_convert_to_repair_order()

    def test_supplement(self):
        """Créer un avenant."""
        quotation = self._create_quotation()
        quotation.action_send()
        quotation.action_approve()
        result = quotation.action_create_supplement()
        supplement_id = result['res_id']
        supplement = self.env['garage.quotation'].browse(supplement_id)
        self.assertTrue(supplement.is_supplement)
        self.assertEqual(supplement.parent_quotation_id, quotation)


class TestGarageRepairOrder(TransactionCase):
    """Tests unitaires pour le workflow OR."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partner = cls.env['res.partner'].create({
            'name': 'Client OR Test',
            'is_garage_customer': True,
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
            'license_plate': 'OR-001-XX',
            'driver_id': cls.partner.id,
        })
        cls.ro = cls.env['garage.repair.order'].create({
            'vehicle_id': cls.vehicle.id,
            'customer_id': cls.partner.id,
        })

    def test_ro_sequence(self):
        """La référence OR est générée automatiquement."""
        self.assertTrue(self.ro.name.startswith('OR/'))

    def test_ro_workflow_full(self):
        """Workflow complet de l'OR."""
        self.ro.action_confirm()
        self.assertEqual(self.ro.state, 'confirmed')

        self.ro.action_start()
        self.assertEqual(self.ro.state, 'in_progress')
        self.assertTrue(self.ro.actual_start_date)
        self.assertEqual(self.ro.vehicle_location, 'workshop')

        self.ro.action_enter_paint_booth()
        self.assertEqual(self.ro.state, 'paint_booth')
        self.assertEqual(self.ro.vehicle_location, 'paint_booth')

        self.ro.action_reassembly()
        self.assertEqual(self.ro.state, 'reassembly')

        self.ro.action_request_qc()
        self.assertEqual(self.ro.state, 'qc_pending')

        self.ro.action_validate_qc()
        self.assertEqual(self.ro.state, 'qc_done')

        self.ro.action_ready()
        self.assertEqual(self.ro.state, 'ready')

        self.ro.action_deliver()
        self.assertEqual(self.ro.state, 'delivered')
        self.assertTrue(self.ro.actual_end_date)
        self.assertEqual(self.ro.vehicle_location, 'delivered')

    def test_ro_compute_hours(self):
        """Calcul des heures et productivité."""
        self.env['garage.repair.order.line'].create({
            'repair_order_id': self.ro.id,
            'name': 'Carrosserie',
            'line_type': 'labor_body',
            'allocated_time': 10.0,
            'hourly_rate': 55.0,
            'actual_time': 8.0,
            'quantity': 1,
            'unit_price': 0,
        })
        self.assertEqual(self.ro.total_allocated_hours, 10.0)
        self.assertEqual(self.ro.total_worked_hours, 8.0)
        self.assertEqual(self.ro.productivity_rate, 80.0)

    def test_ro_compute_amounts(self):
        """Calcul des montants OR."""
        self.env['garage.repair.order.line'].create({
            'repair_order_id': self.ro.id,
            'name': 'Peinture',
            'line_type': 'labor_paint',
            'allocated_time': 5.0,
            'hourly_rate': 55.0,
            'quantity': 1,
            'unit_price': 0,
        })
        self.assertEqual(self.ro.amount_untaxed, 275.0)
        self.assertAlmostEqual(self.ro.amount_tax, 57.75, places=2)
