"""Tests pour les champs différés : formules peinture, marge, stock, consommation."""

from odoo.tests.common import TransactionCase


class TestPaintFormulaOnVehicle(TransactionCase):
    """Tests pour paint_formula_ids sur fleet.vehicle."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.brand = cls.env['fleet.vehicle.model.brand'].create({
            'name': 'TestBrandDF',
        })
        cls.model = cls.env['fleet.vehicle.model'].create({
            'name': 'TestModelDF',
            'brand_id': cls.brand.id,
        })
        cls.vehicle = cls.env['fleet.vehicle'].create({
            'model_id': cls.model.id,
            'license_plate': 'DF-001',
            'vin_sn': 'WDBRF61J31F123456',
        })
        cls.paint_system = cls.env['garage.paint.system'].create({
            'name': 'Standox Test',
            'code': 'STX',
        })

    def test_01_formula_one2many(self):
        """Le champ paint_formula_ids existe et est vide par défaut."""
        self.assertEqual(len(self.vehicle.paint_formula_ids), 0)
        self.assertEqual(self.vehicle.paint_formula_count, 0)

    def test_02_add_formula(self):
        """On peut ajouter une formule et le count est mis à jour."""
        self.env['garage.paint.formula'].create({
            'vehicle_id': self.vehicle.id,
            'paint_system_id': self.paint_system.id,
            'paint_code': 'LY9T',
        })
        self.vehicle.invalidate_recordset()
        self.assertEqual(len(self.vehicle.paint_formula_ids), 1)
        self.assertEqual(self.vehicle.paint_formula_count, 1)

    def test_03_multiple_formulas(self):
        """Plusieurs formules sur un même véhicule."""
        for code in ('LY9T', 'LC9X', '475'):
            self.env['garage.paint.formula'].create({
                'vehicle_id': self.vehicle.id,
                'paint_system_id': self.paint_system.id,
                'paint_code': code,
            })
        self.vehicle.invalidate_recordset()
        self.assertEqual(self.vehicle.paint_formula_count, 3)


class TestRepairOrderMargin(TransactionCase):
    """Tests pour les champs margin/margin_rate sur l'OR."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.brand = cls.env['fleet.vehicle.model.brand'].create({
            'name': 'TestBrandMG',
        })
        cls.model = cls.env['fleet.vehicle.model'].create({
            'name': 'TestModelMG',
            'brand_id': cls.brand.id,
        })
        cls.partner = cls.env['res.partner'].create({
            'name': 'Client Marge Test',
        })
        cls.vehicle = cls.env['fleet.vehicle'].create({
            'model_id': cls.model.id,
            'license_plate': 'MG-001',
            'vin_sn': 'WDBRF61J31F234567',
        })
        cls.repair_order = cls.env['garage.repair.order'].create({
            'vehicle_id': cls.vehicle.id,
            'customer_id': cls.partner.id,
        })

    def test_01_margin_zero_no_lines(self):
        """Sans lignes, la marge est 0."""
        self.assertEqual(self.repair_order.margin, 0.0)
        self.assertEqual(self.repair_order.margin_rate, 0.0)
        self.assertEqual(self.repair_order.total_cost, 0.0)

    def test_02_margin_parts_line(self):
        """Marge = vente - coût sur une ligne pièces."""
        self.env['garage.repair.order.line'].create({
            'repair_order_id': self.repair_order.id,
            'name': 'Pare-chocs avant',
            'line_type': 'parts',
            'quantity': 1,
            'unit_price': 500.0,
            'cost_price': 300.0,
        })
        self.repair_order.invalidate_recordset()
        self.assertEqual(self.repair_order.amount_untaxed, 500.0)
        self.assertEqual(self.repair_order.total_cost, 300.0)
        self.assertEqual(self.repair_order.margin, 200.0)
        self.assertAlmostEqual(self.repair_order.margin_rate, 40.0, places=1)

    def test_03_margin_labor_line(self):
        """Marge sur une ligne MO = (heures × taux vente) - (heures × coût horaire)."""
        self.env['garage.repair.order.line'].create({
            'repair_order_id': self.repair_order.id,
            'name': 'MO carrosserie',
            'line_type': 'labor_body',
            'allocated_time': 5.0,
            'hourly_rate': 80.0,
            'cost_price': 35.0,
        })
        self.repair_order.invalidate_recordset()
        self.assertEqual(self.repair_order.amount_untaxed, 400.0)
        self.assertEqual(self.repair_order.total_cost, 175.0)
        self.assertEqual(self.repair_order.margin, 225.0)

    def test_04_margin_multiple_lines(self):
        """Marge agrégée sur plusieurs lignes."""
        self.env['garage.repair.order.line'].create({
            'repair_order_id': self.repair_order.id,
            'name': 'Pièce A',
            'line_type': 'parts',
            'quantity': 2,
            'unit_price': 100.0,
            'cost_price': 60.0,
        })
        self.env['garage.repair.order.line'].create({
            'repair_order_id': self.repair_order.id,
            'name': 'MO peinture',
            'line_type': 'labor_paint',
            'allocated_time': 3.0,
            'hourly_rate': 70.0,
            'cost_price': 30.0,
        })
        self.repair_order.invalidate_recordset()
        # Revenue: (2*100) + (3*70) = 200 + 210 = 410
        # Cost: (2*60) + (3*30) = 120 + 90 = 210
        self.assertEqual(self.repair_order.amount_untaxed, 410.0)
        self.assertEqual(self.repair_order.total_cost, 210.0)
        self.assertEqual(self.repair_order.margin, 200.0)

    def test_05_cost_total_line(self):
        """Le cost_total de la ligne est correctement calculé."""
        line = self.env['garage.repair.order.line'].create({
            'repair_order_id': self.repair_order.id,
            'name': 'Pièce B',
            'line_type': 'parts',
            'quantity': 3,
            'unit_price': 50.0,
            'cost_price': 25.0,
        })
        self.assertEqual(line.cost_total, 75.0)


class TestRepairOrderLineStock(TransactionCase):
    """Tests pour stock_move_ids et parts_received sur les lignes d'OR."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.brand = cls.env['fleet.vehicle.model.brand'].create({
            'name': 'TestBrandST',
        })
        cls.model = cls.env['fleet.vehicle.model'].create({
            'name': 'TestModelST',
            'brand_id': cls.brand.id,
        })
        cls.partner = cls.env['res.partner'].create({
            'name': 'Client Stock Test',
        })
        cls.vehicle = cls.env['fleet.vehicle'].create({
            'model_id': cls.model.id,
            'license_plate': 'ST-001',
            'vin_sn': 'WDBRF61J31F345678',
        })
        cls.ro = cls.env['garage.repair.order'].create({
            'vehicle_id': cls.vehicle.id,
            'customer_id': cls.partner.id,
        })

    def test_01_stock_move_fields_exist(self):
        """Les champs stock existent sur la ligne d'OR."""
        fields_list = self.env['garage.repair.order.line']._fields
        self.assertIn('stock_move_ids', fields_list)
        self.assertIn('parts_received', fields_list)

    def test_02_parts_received_default_true(self):
        """Sans mouvement stock, parts_received est True (pas en attente)."""
        line = self.env['garage.repair.order.line'].create({
            'repair_order_id': self.ro.id,
            'name': 'Pièce test',
            'line_type': 'parts',
            'quantity': 1,
            'unit_price': 100,
        })
        self.assertTrue(line.parts_received)

    def test_03_stock_move_on_stock_model(self):
        """Le champ garage_ro_line_id existe sur stock.move."""
        fields_list = self.env['stock.move']._fields
        self.assertIn('garage_ro_line_id', fields_list)
        self.assertIn('garage_paint_consumption_id', fields_list)

    def test_04_parts_received_with_pending_move(self):
        """Avec un mouvement non terminé, parts_received est False."""
        line = self.env['garage.repair.order.line'].create({
            'repair_order_id': self.ro.id,
            'name': 'Pièce en attente',
            'line_type': 'parts',
            'quantity': 1,
            'unit_price': 100,
        })
        product = self.env['product.product'].create({
            'name': 'Produit Test Stock',
            'type': 'consu',
        })
        warehouse = self.env['stock.warehouse'].search([], limit=1)
        self.env['stock.move'].create({
            'name': 'Test move',
            'product_id': product.id,
            'product_uom': product.uom_id.id,
            'product_uom_qty': 1,
            'location_id': warehouse.lot_stock_id.id,
            'location_dest_id': warehouse.lot_stock_id.id,
            'garage_ro_line_id': line.id,
        })
        line.invalidate_recordset()
        self.assertFalse(line.parts_received)


class TestPaintConsumptionStock(TransactionCase):
    """Tests pour la décrémentation stock sur consommation peinture."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.brand = cls.env['fleet.vehicle.model.brand'].create({
            'name': 'TestBrandPC',
        })
        cls.fleet_model = cls.env['fleet.vehicle.model'].create({
            'name': 'TestModelPC',
            'brand_id': cls.brand.id,
        })
        cls.partner = cls.env['res.partner'].create({
            'name': 'Client Paint Test',
        })
        cls.vehicle = cls.env['fleet.vehicle'].create({
            'model_id': cls.fleet_model.id,
            'license_plate': 'PC-001',
            'vin_sn': 'WDBRF61J31F456789',
        })
        cls.ro = cls.env['garage.repair.order'].create({
            'vehicle_id': cls.vehicle.id,
            'customer_id': cls.partner.id,
        })
        cls.paint_op = cls.env['garage.paint.operation'].create({
            'repair_order_id': cls.ro.id,
            'name': 'Peinture test',
            'zone': 'hood',
            'operation_type': 'base_coat',
        })
        # Utiliser l'UoM litre pour le produit peinture
        uom_litre = cls.env.ref('uom.product_uom_litre', raise_if_not_found=False)
        cls.product = cls.env['product.product'].create({
            'name': 'Base colorée Standox',
            'type': 'consu',
            'list_price': 45.0,
            'standard_price': 30.0,
            'uom_id': uom_litre.id if uom_litre else False,
        })

    def test_01_stock_move_created(self):
        """La création d'une consommation crée un mouvement stock."""
        consumption = self.env['garage.paint.consumption'].create({
            'paint_operation_id': self.paint_op.id,
            'product_id': self.product.id,
            'product_type': 'base',
            'quantity': 0.5,
            'unit_cost': 30.0,
        })
        self.assertTrue(consumption.stock_move_id)
        self.assertEqual(consumption.stock_move_id.product_id, self.product)
        self.assertEqual(consumption.stock_move_id.state, 'done')

    def test_02_stock_move_field_on_consumption(self):
        """Le champ stock_move_id existe sur paint.consumption."""
        self.assertIn('stock_move_id',
                      self.env['garage.paint.consumption']._fields)

    def test_03_no_stock_move_zero_qty(self):
        """Pas de mouvement stock si la quantité est 0."""
        consumption = self.env['garage.paint.consumption'].create({
            'paint_operation_id': self.paint_op.id,
            'product_id': self.product.id,
            'product_type': 'base',
            'quantity': 0,
            'unit_cost': 30.0,
        })
        self.assertFalse(consumption.stock_move_id)

    def test_04_stock_move_backlink(self):
        """Le mouvement stock a le lien retour vers la consommation."""
        consumption = self.env['garage.paint.consumption'].create({
            'paint_operation_id': self.paint_op.id,
            'product_id': self.product.id,
            'product_type': 'clear',
            'quantity': 0.3,
            'unit_cost': 25.0,
        })
        self.assertEqual(
            consumption.stock_move_id.garage_paint_consumption_id,
            consumption,
        )
