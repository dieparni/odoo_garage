"""Tests pour les opérations métier (carrosserie, peinture, mécanique)."""

from datetime import date, timedelta

from odoo.tests.common import TransactionCase


class TestTradesBase(TransactionCase):
    """Setup commun pour les tests métier."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partner = cls.env['res.partner'].create({
            'name': 'Client Trades Test',
            'is_garage_customer': True,
        })
        cls.brand = cls.env['fleet.vehicle.model.brand'].create({
            'name': 'TradesBrand',
        })
        cls.vmodel = cls.env['fleet.vehicle.model'].create({
            'name': 'TradesModel',
            'brand_id': cls.brand.id,
        })
        cls.vehicle = cls.env['fleet.vehicle'].create({
            'model_id': cls.vmodel.id,
            'license_plate': 'TRD-001-XX',
            'driver_id': cls.partner.id,
        })
        cls.repair_order = cls.env['garage.repair.order'].create({
            'vehicle_id': cls.vehicle.id,
            'customer_id': cls.partner.id,
        })


class TestBodyworkOperation(TestTradesBase):
    """Tests opérations de carrosserie."""

    def _create_bodywork(self, **kwargs):
        vals = {
            'repair_order_id': self.repair_order.id,
            'name': 'Remplacement aile AVG',
            'operation_type': 'replace',
            'damage_zone': 'fender_fl',
            'damage_level': 'replace',
        }
        vals.update(kwargs)
        return self.env['garage.bodywork.operation'].create(vals)

    def test_01_create_bodywork(self):
        """Création d'une opération carrosserie."""
        op = self._create_bodywork()
        self.assertEqual(op.state, 'todo')
        self.assertTrue(op.requires_painting)

    def test_02_workflow_start(self):
        """Workflow : todo → in_progress."""
        op = self._create_bodywork()
        op.action_start()
        self.assertEqual(op.state, 'in_progress')

    def test_03_workflow_done_creates_paint(self):
        """Terminer une op carrosserie crée une op peinture liée."""
        op = self._create_bodywork()
        op.action_start()
        op.action_done()
        self.assertEqual(op.state, 'done')
        self.assertTrue(op.paint_operation_id)
        paint_op = op.paint_operation_id
        self.assertEqual(paint_op.repair_order_id, self.repair_order)
        self.assertEqual(paint_op.bodywork_operation_id, op)
        self.assertEqual(paint_op.zone, 'fender_fl')
        self.assertEqual(paint_op.state, 'waiting')

    def test_04_done_no_paint_if_not_required(self):
        """Pas d'op peinture si requires_painting=False."""
        op = self._create_bodywork(requires_painting=False)
        op.action_start()
        op.action_done()
        self.assertFalse(op.paint_operation_id)

    def test_05_done_no_duplicate_paint(self):
        """Pas de doublon si paint_operation_id déjà renseigné."""
        op = self._create_bodywork()
        paint_op = self.env['garage.paint.operation'].create({
            'repair_order_id': self.repair_order.id,
            'name': 'Peinture aile',
            'operation_type': 'full_panel',
        })
        op.paint_operation_id = paint_op
        op.action_start()
        op.action_done()
        self.assertEqual(op.paint_operation_id, paint_op)

    def test_06_block_unblock(self):
        """Workflow blocage/déblocage."""
        op = self._create_bodywork()
        op.action_start()
        op.action_block()
        self.assertEqual(op.state, 'blocked')
        op.action_unblock()
        self.assertEqual(op.state, 'in_progress')

    def test_07_on_repair_order(self):
        """Les opérations apparaissent sur l'OR."""
        op = self._create_bodywork()
        self.assertIn(op, self.repair_order.bodywork_operation_ids)
        self.assertEqual(self.repair_order.bodywork_count, 1)


class TestPaintOperation(TestTradesBase):
    """Tests opérations de peinture."""

    def _create_paint(self, **kwargs):
        vals = {
            'repair_order_id': self.repair_order.id,
            'name': 'Peinture capot',
            'operation_type': 'full_panel',
            'zone': 'hood',
        }
        vals.update(kwargs)
        return self.env['garage.paint.operation'].create(vals)

    def test_01_create_paint(self):
        """Création d'une opération peinture."""
        op = self._create_paint()
        self.assertEqual(op.state, 'waiting')

    def test_02_full_workflow(self):
        """Workflow complet peinture."""
        op = self._create_paint()
        op.action_start_prep()
        self.assertEqual(op.state, 'prep')
        op.action_enter_booth()
        self.assertEqual(op.state, 'booth')
        op.action_drying()
        self.assertEqual(op.state, 'drying')
        op.action_polish()
        self.assertEqual(op.state, 'polish')
        op.action_done()
        self.assertEqual(op.state, 'done')

    def test_03_rework_cycle(self):
        """Cycle reprise qualité peinture."""
        op = self._create_paint()
        op.action_start_prep()
        op.action_enter_booth()
        op.action_drying()
        op.action_polish()
        op.action_rework()
        self.assertEqual(op.state, 'rework')
        op.action_restart()
        self.assertEqual(op.state, 'prep')

    def test_04_product_consumption_cost(self):
        """Calcul coût total consommation produits."""
        op = self._create_paint()
        # Utiliser un produit existant pour éviter les contraintes des modules tiers
        product = self.env['product.product'].search([], limit=1)
        if not product:
            return
        self.env['garage.paint.consumption'].create({
            'paint_operation_id': op.id,
            'product_id': product.id,
            'product_type': 'base',
            'quantity': 2.5,
            'unit_cost': 40.0,
        })
        self.env['garage.paint.consumption'].create({
            'paint_operation_id': op.id,
            'product_id': product.id,
            'product_type': 'clear',
            'quantity': 1.0,
            'unit_cost': 25.0,
        })
        self.assertAlmostEqual(op.total_product_cost, 125.0)

    def test_05_on_repair_order(self):
        """Les opérations peinture apparaissent sur l'OR."""
        op = self._create_paint()
        self.assertIn(op, self.repair_order.paint_operation_ids)
        self.assertEqual(self.repair_order.paint_count, 1)


class TestPaintFormula(TestTradesBase):
    """Tests formules peinture."""

    def test_01_create_formula(self):
        """Création d'une formule peinture."""
        system = self.env['garage.paint.system'].create({
            'name': 'Standox Test',
        })
        formula = self.env['garage.paint.formula'].create({
            'paint_code': 'LY3D',
            'paint_system_id': system.id,
            'formula_reference': 'STX-LY3D-001',
            'variant_name': '2K nacré',
            'vehicle_id': self.vehicle.id,
        })
        self.assertTrue(formula.active)
        self.assertEqual(formula.paint_code, 'LY3D')


class TestMechanicOperation(TestTradesBase):
    """Tests opérations mécanique."""

    def _create_mechanic(self, **kwargs):
        vals = {
            'repair_order_id': self.repair_order.id,
            'name': 'Vidange moteur',
            'operation_category': 'maintenance',
            'operation_type': 'oil_change',
        }
        vals.update(kwargs)
        return self.env['garage.mechanic.operation'].create(vals)

    def test_01_create_mechanic(self):
        """Création d'une opération mécanique."""
        op = self._create_mechanic()
        self.assertEqual(op.state, 'todo')

    def test_02_workflow_start_done(self):
        """Workflow : todo → in_progress → done."""
        op = self._create_mechanic()
        op.action_start()
        self.assertEqual(op.state, 'in_progress')
        op.action_done()
        self.assertEqual(op.state, 'done')

    def test_03_waiting_parts(self):
        """Workflow : in_progress → waiting_parts → done."""
        op = self._create_mechanic()
        op.action_start()
        op.action_wait_parts()
        self.assertEqual(op.state, 'waiting_parts')
        op.action_done()
        self.assertEqual(op.state, 'done')

    def test_04_diagnostic(self):
        """Opération diagnostic avec codes OBD."""
        op = self._create_mechanic(
            operation_category='diagnostic',
            operation_type='obd_scan',
            obd_codes='P0300, P0171',
        )
        self.assertEqual(op.obd_codes, 'P0300, P0171')
        self.assertFalse(op.obd_codes_cleared)

    def test_05_tires(self):
        """Opération pneumatiques avec détails pneu."""
        op = self._create_mechanic(
            operation_category='tires',
            operation_type='tire_change',
            tire_brand='Michelin',
            tire_size='205/55 R16',
            tire_dot='2024',
            tire_tread_depth=7.5,
            tire_position='fl',
        )
        self.assertEqual(op.tire_brand, 'Michelin')
        self.assertEqual(op.tire_position, 'fl')

    def test_06_on_repair_order(self):
        """Les opérations méca apparaissent sur l'OR."""
        op = self._create_mechanic()
        self.assertIn(op, self.repair_order.mechanic_operation_ids)
        self.assertEqual(self.repair_order.mechanic_count, 1)


class TestMaintenancePlan(TestTradesBase):
    """Tests plan d'entretien."""

    def test_01_create_plan(self):
        """Création d'un plan d'entretien."""
        plan = self.env['garage.maintenance.plan'].create({
            'vehicle_id': self.vehicle.id,
        })
        self.assertIn('Plan entretien', plan.name)

    def test_02_plan_item_compute_next(self):
        """Calcul prochain entretien (km et date)."""
        plan = self.env['garage.maintenance.plan'].create({
            'vehicle_id': self.vehicle.id,
        })
        item = self.env['garage.maintenance.plan.item'].create({
            'plan_id': plan.id,
            'name': 'Vidange moteur',
            'interval_km': 15000,
            'interval_months': 12,
            'last_done_km': 45000,
            'last_done_date': date(2025, 3, 15),
        })
        self.assertEqual(item.next_due_km, 60000)
        self.assertEqual(item.next_due_date, date(2026, 3, 15))

    def test_03_plan_item_overdue(self):
        """Détection entretien en retard."""
        plan = self.env['garage.maintenance.plan'].create({
            'vehicle_id': self.vehicle.id,
        })
        item = self.env['garage.maintenance.plan.item'].create({
            'plan_id': plan.id,
            'name': 'Remplacement filtres',
            'interval_months': 6,
            'last_done_date': date(2024, 1, 1),
        })
        self.assertTrue(item.is_overdue)

    def test_04_plan_item_not_overdue(self):
        """Entretien pas encore dû."""
        plan = self.env['garage.maintenance.plan'].create({
            'vehicle_id': self.vehicle.id,
        })
        item = self.env['garage.maintenance.plan.item'].create({
            'plan_id': plan.id,
            'name': 'Courroie distribution',
            'interval_months': 60,
            'last_done_date': date.today(),
        })
        self.assertFalse(item.is_overdue)

    def test_05_plan_item_no_last_done(self):
        """next_due_km calculé même sans last_done_km (nouveau véhicule)."""
        plan = self.env['garage.maintenance.plan'].create({
            'vehicle_id': self.vehicle.id,
        })
        item = self.env['garage.maintenance.plan.item'].create({
            'plan_id': plan.id,
            'name': 'Première vidange',
            'interval_km': 15000,
            'interval_months': 12,
        })
        self.assertEqual(item.next_due_km, 15000)
        self.assertTrue(item.next_due_date)
