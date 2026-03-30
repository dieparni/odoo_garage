"""Tests Agent 14 — TVA configurable, auto purchase order, portail client."""

from odoo.tests.common import TransactionCase, tagged


@tagged('garage_pro')
class TestConfigurableVAT(TransactionCase):
    """Tests pour le taux TVA configurable via ir.config_parameter."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        brand = cls.env['fleet.vehicle.model.brand'].create({
            'name': 'TestBrand VAT',
        })
        model = cls.env['fleet.vehicle.model'].create({
            'name': 'TestModel VAT',
            'brand_id': brand.id,
        })
        cls.vehicle = cls.env['fleet.vehicle'].create({
            'model_id': model.id,
            'license_plate': 'VAT-001',
        })
        cls.customer = cls.env['res.partner'].create({
            'name': 'Client TVA Test',
            'is_garage_customer': True,
        })

    def test_01_default_vat_21(self):
        """Le taux par défaut est 21% si pas de paramètre."""
        self.env['ir.config_parameter'].sudo().set_param(
            'garage_pro.default_vat_rate', '21.0'
        )
        quotation = self.env['garage.quotation'].create({
            'vehicle_id': self.vehicle.id,
            'customer_id': self.customer.id,
        })
        self.env['garage.quotation.line'].create({
            'quotation_id': quotation.id,
            'name': 'Test TVA',
            'line_type': 'labor_body',
            'quantity': 1,
            'unit_price': 100.0,
        })
        quotation.invalidate_recordset()
        self.assertAlmostEqual(quotation.amount_tax, 21.0, places=2)
        self.assertAlmostEqual(quotation.amount_total, 121.0, places=2)

    def test_02_custom_vat_rate(self):
        """Changer le taux TVA via ir.config_parameter."""
        self.env['ir.config_parameter'].sudo().set_param(
            'garage_pro.default_vat_rate', '17.0'
        )
        quotation = self.env['garage.quotation'].create({
            'vehicle_id': self.vehicle.id,
            'customer_id': self.customer.id,
        })
        self.env['garage.quotation.line'].create({
            'quotation_id': quotation.id,
            'name': 'Test TVA 17%',
            'line_type': 'parts',
            'quantity': 1,
            'unit_price': 200.0,
        })
        quotation.invalidate_recordset()
        self.assertAlmostEqual(quotation.amount_tax, 34.0, places=2)
        self.assertAlmostEqual(quotation.amount_total, 234.0, places=2)

    def test_03_vat_on_repair_order(self):
        """Le taux TVA configurable s'applique aussi aux OR."""
        self.env['ir.config_parameter'].sudo().set_param(
            'garage_pro.default_vat_rate', '17.0'
        )
        ro = self.env['garage.repair.order'].create({
            'vehicle_id': self.vehicle.id,
            'customer_id': self.customer.id,
        })
        self.env['garage.repair.order.line'].create({
            'repair_order_id': ro.id,
            'name': 'Test TVA OR',
            'line_type': 'labor_mech',
            'quantity': 1,
            'unit_price': 100.0,
        })
        ro.invalidate_recordset()
        self.assertAlmostEqual(ro.amount_tax, 17.0, places=2)

    def test_04_vat_zero(self):
        """TVA à 0% (exonération)."""
        self.env['ir.config_parameter'].sudo().set_param(
            'garage_pro.default_vat_rate', '0.0'
        )
        quotation = self.env['garage.quotation'].create({
            'vehicle_id': self.vehicle.id,
            'customer_id': self.customer.id,
        })
        self.env['garage.quotation.line'].create({
            'quotation_id': quotation.id,
            'name': 'Test TVA 0%',
            'line_type': 'parts',
            'quantity': 1,
            'unit_price': 100.0,
        })
        quotation.invalidate_recordset()
        self.assertAlmostEqual(quotation.amount_tax, 0.0, places=2)
        self.assertAlmostEqual(quotation.amount_total, 100.0, places=2)

    def test_05_settings_field_exists(self):
        """Le champ garage_default_vat_rate existe dans les settings."""
        settings = self.env['res.config.settings'].create({})
        self.assertTrue(hasattr(settings, 'garage_default_vat_rate'))


@tagged('garage_pro')
class TestAutoPurchaseOrder(TransactionCase):
    """Tests pour la création automatique de commandes fournisseur."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        brand = cls.env['fleet.vehicle.model.brand'].create({
            'name': 'TestBrand PO',
        })
        model = cls.env['fleet.vehicle.model'].create({
            'name': 'TestModel PO',
            'brand_id': brand.id,
        })
        cls.vehicle = cls.env['fleet.vehicle'].create({
            'model_id': model.id,
            'license_plate': 'PO-001',
            'vin_sn': 'WDBRF61J31FAUT0P0',
        })
        cls.customer = cls.env['res.partner'].create({
            'name': 'Client PO Test',
            'is_garage_customer': True,
        })
        cls.supplier = cls.env['res.partner'].create({
            'name': 'Fournisseur Pièces Test',
            'supplier_rank': 1,
        })
        # S'assurer qu'un entrepôt existe
        cls.warehouse = cls.env['stock.warehouse'].search(
            [('company_id', '=', cls.env.company.id)], limit=1)
        if not cls.warehouse:
            cls.warehouse = cls.env['stock.warehouse'].create({
                'name': 'Test Warehouse PO',
                'code': 'TWPO',
                'company_id': cls.env.company.id,
            })
        cls.product = cls.env['product.product'].create({
            'name': 'Pièce test auto-PO',
            'type': 'consu',
            'is_storable': True,
            'list_price': 50.0,
            'standard_price': 30.0,
            'seller_ids': [(0, 0, {
                'partner_id': cls.supplier.id,
                'price': 25.0,
            })],
        })

    def test_01_confirm_with_stock_available(self):
        """OR confirmé normalement si stock suffisant."""
        # S'assurer qu'il y a du stock
        self._add_stock(self.product, 10)

        ro = self.env['garage.repair.order'].create({
            'vehicle_id': self.vehicle.id,
            'customer_id': self.customer.id,
        })
        self.env['garage.repair.order.line'].create({
            'repair_order_id': ro.id,
            'name': 'Pièce en stock',
            'line_type': 'parts',
            'product_id': self.product.id,
            'quantity': 2,
            'unit_price': 50.0,
        })
        ro.action_confirm()
        self.assertEqual(ro.state, 'confirmed')

    def test_02_confirm_with_stock_shortage(self):
        """OR passe en attente pièces si stock insuffisant."""
        product_no_stock = self.env['product.product'].create({
            'name': 'Pièce sans stock',
            'type': 'consu',
            'is_storable': True,
            'list_price': 80.0,
            'seller_ids': [(0, 0, {
                'partner_id': self.supplier.id,
                'price': 40.0,
            })],
        })

        ro = self.env['garage.repair.order'].create({
            'vehicle_id': self.vehicle.id,
            'customer_id': self.customer.id,
        })
        self.env['garage.repair.order.line'].create({
            'repair_order_id': ro.id,
            'name': 'Pièce manquante',
            'line_type': 'parts',
            'product_id': product_no_stock.id,
            'quantity': 5,
            'unit_price': 80.0,
        })
        ro.action_confirm()
        self.assertEqual(ro.state, 'parts_waiting')

    def test_03_auto_po_message_posted(self):
        """Un PO brouillon est créé quand il y a des pièces manquantes avec fournisseur."""
        product_no_stock = self.env['product.product'].create({
            'name': 'Pièce auto-PO',
            'type': 'consu',
            'is_storable': True,
            'list_price': 60.0,
            'seller_ids': [(0, 0, {
                'partner_id': self.supplier.id,
                'price': 35.0,
            })],
        })

        po_count_before = self.env['purchase.order'].search_count([])

        ro = self.env['garage.repair.order'].create({
            'vehicle_id': self.vehicle.id,
            'customer_id': self.customer.id,
        })
        self.env['garage.repair.order.line'].create({
            'repair_order_id': ro.id,
            'name': 'Pièce auto',
            'line_type': 'parts',
            'product_id': product_no_stock.id,
            'quantity': 3,
            'unit_price': 60.0,
        })
        ro.action_confirm()
        self.assertEqual(ro.state, 'parts_waiting')

        # Un PO a été créé
        po_count_after = self.env['purchase.order'].search_count([])
        self.assertEqual(po_count_after, po_count_before + 1,
                         "Un bon de commande fournisseur doit être créé")
        po = self.env['purchase.order'].search(
            [('origin', '=', ro.name)], limit=1)
        self.assertTrue(po, "Le PO doit avoir l'OR comme origine")
        self.assertEqual(po.partner_id, self.supplier)
        self.assertEqual(po.state, 'draft')

        # Un message a été posté
        messages = ro.message_ids.filtered(
            lambda m: 'ommande' in (m.body or '').lower()
        )
        self.assertTrue(messages)

    def test_04_no_po_for_labor(self):
        """Pas de PO pour les lignes main d'œuvre."""
        po_count_before = self.env['purchase.order'].search_count([])

        ro = self.env['garage.repair.order'].create({
            'vehicle_id': self.vehicle.id,
            'customer_id': self.customer.id,
        })
        self.env['garage.repair.order.line'].create({
            'repair_order_id': ro.id,
            'name': 'MO carrosserie',
            'line_type': 'labor_body',
            'quantity': 1,
            'unit_price': 100.0,
            'allocated_time': 2.0,
            'hourly_rate': 50.0,
        })
        ro.action_confirm()

        po_count_after = self.env['purchase.order'].search_count([])
        self.assertEqual(po_count_after, po_count_before)
        self.assertEqual(ro.state, 'confirmed')

    def test_05_no_supplier_notification(self):
        """Si pas de fournisseur, message de notification posté."""
        product_no_supplier = self.env['product.product'].create({
            'name': 'Pièce sans fournisseur',
            'type': 'consu',
            'is_storable': True,
            'list_price': 40.0,
        })

        ro = self.env['garage.repair.order'].create({
            'vehicle_id': self.vehicle.id,
            'customer_id': self.customer.id,
        })
        self.env['garage.repair.order.line'].create({
            'repair_order_id': ro.id,
            'name': 'Pièce no supplier',
            'line_type': 'parts',
            'product_id': product_no_supplier.id,
            'quantity': 2,
            'unit_price': 40.0,
        })
        ro.action_confirm()

        # L'OR passe en attente pièces
        self.assertEqual(ro.state, 'parts_waiting')
        # Un message a été posté
        messages = ro.message_ids.filtered(
            lambda m: 'fournisseur' in (m.body or '').lower()
        )
        self.assertTrue(messages)

    def test_06_activity_scheduled(self):
        """Une activité est planifiée quand il y a des pièces manquantes."""
        product_no_stock = self.env['product.product'].create({
            'name': 'Pièce activité test',
            'type': 'consu',
            'is_storable': True,
            'list_price': 50.0,
        })

        ro = self.env['garage.repair.order'].create({
            'vehicle_id': self.vehicle.id,
            'customer_id': self.customer.id,
        })
        self.env['garage.repair.order.line'].create({
            'repair_order_id': ro.id,
            'name': 'Pièce activité',
            'line_type': 'parts',
            'product_id': product_no_stock.id,
            'quantity': 1,
            'unit_price': 50.0,
        })
        ro.action_confirm()

        activities = self.env['mail.activity'].search([
            ('res_model', '=', 'garage.repair.order'),
            ('res_id', '=', ro.id),
        ])
        self.assertTrue(activities)

    def _add_stock(self, product, qty):
        """Helper pour ajouter du stock."""
        self.env['stock.quant'].with_context(inventory_mode=True).create({
            'product_id': product.id,
            'inventory_quantity': qty,
            'location_id': self.warehouse.lot_stock_id.id,
        }).action_apply_inventory()


@tagged('garage_pro')
class TestPortalController(TransactionCase):
    """Tests basiques pour le portail client — vérification des méthodes."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        brand = cls.env['fleet.vehicle.model.brand'].create({
            'name': 'TestBrand Portal',
        })
        model = cls.env['fleet.vehicle.model'].create({
            'name': 'TestModel Portal',
            'brand_id': brand.id,
        })
        cls.vehicle = cls.env['fleet.vehicle'].create({
            'model_id': model.id,
            'license_plate': 'PORTAL-01',
        })
        cls.customer = cls.env['res.partner'].create({
            'name': 'Client Portail Test',
            'is_garage_customer': True,
        })

    def test_01_portal_templates_loaded(self):
        """Les templates portail sont chargés en DB."""
        tmpl = self.env.ref(
            'garage_pro.portal_my_repair_orders', raise_if_not_found=False
        )
        self.assertTrue(tmpl)

    def test_02_portal_quotation_template_loaded(self):
        """Le template liste devis portail est chargé."""
        tmpl = self.env.ref(
            'garage_pro.portal_my_quotations', raise_if_not_found=False
        )
        self.assertTrue(tmpl)

    def test_03_portal_home_counter_template_loaded(self):
        """Le template compteurs accueil portail est chargé."""
        tmpl = self.env.ref(
            'garage_pro.portal_my_home_garage', raise_if_not_found=False
        )
        self.assertTrue(tmpl)

    def test_04_portal_detail_templates_loaded(self):
        """Les templates détail portail sont chargés."""
        tmpl_or = self.env.ref(
            'garage_pro.portal_repair_order_detail',
            raise_if_not_found=False,
        )
        tmpl_quot = self.env.ref(
            'garage_pro.portal_quotation_detail',
            raise_if_not_found=False,
        )
        self.assertTrue(tmpl_or)
        self.assertTrue(tmpl_quot)

    def test_05_documentation_portal_visibility(self):
        """Le champ is_visible_portal existe et est True par défaut."""
        doc = self.env['garage.documentation'].create({
            'name': 'Photo test portail',
            'doc_type': 'photo_before',
            'file': 'dGVzdA==',  # "test" en base64
        })
        self.assertTrue(doc.is_visible_portal)
