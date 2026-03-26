"""Tests des rapports QWeb garage."""

from odoo.tests.common import TransactionCase, tagged


@tagged('garage_pro', '-at_install', 'post_install')
class TestGarageReports(TransactionCase):
    """Vérification des rapports PDF garage."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        brand = cls.env['fleet.vehicle.model.brand'].create({
            'name': 'TestBrand Reports',
        })
        model = cls.env['fleet.vehicle.model'].create({
            'name': 'TestModel Reports',
            'brand_id': brand.id,
        })
        cls.vehicle = cls.env['fleet.vehicle'].create({
            'model_id': model.id,
            'license_plate': 'RPT-001',
            'vin_sn': 'WDBRF61J21F123456',
        })
        cls.customer = cls.env['res.partner'].create({
            'name': 'Client Test Reports',
            'is_garage_customer': True,
        })
        cls.quotation = cls.env['garage.quotation'].create({
            'vehicle_id': cls.vehicle.id,
            'customer_id': cls.customer.id,
        })
        cls.env['garage.quotation.line'].create({
            'quotation_id': cls.quotation.id,
            'name': 'Redressage capot',
            'line_type': 'labor_body',
            'allocated_time': 3.0,
            'hourly_rate': 55.0,
        })
        cls.env['garage.quotation.line'].create({
            'quotation_id': cls.quotation.id,
            'name': 'Pare-chocs avant',
            'line_type': 'parts',
            'quantity': 1,
            'unit_price': 250.0,
        })
        cls.quotation.action_send()
        cls.quotation.action_approve()
        res = cls.quotation.action_convert_to_repair_order()
        cls.repair_order = cls.env['garage.repair.order'].browse(res['res_id'])
        cls.checklist = cls.env['garage.quality.checklist'].create_from_repair_order(
            cls.repair_order,
        )

    # ------------------------------------------------------------------
    # Tests : report actions existent
    # ------------------------------------------------------------------

    def test_01_quotation_report_action_exists(self):
        """L'action de rapport devis existe."""
        action = self.env.ref('garage_pro.action_report_garage_quotation')
        self.assertTrue(action)
        self.assertEqual(action.model, 'garage.quotation')

    def test_02_repair_order_report_action_exists(self):
        """L'action de rapport OR existe."""
        action = self.env.ref('garage_pro.action_report_garage_repair_order')
        self.assertTrue(action)
        self.assertEqual(action.model, 'garage.repair.order')

    def test_03_quality_checklist_report_action_exists(self):
        """L'action de rapport checklist qualité existe."""
        action = self.env.ref('garage_pro.action_report_garage_quality_checklist')
        self.assertTrue(action)
        self.assertEqual(action.model, 'garage.quality.checklist')

    def test_04_invoice_inherit_exists(self):
        """Le template d'héritage facture garage existe."""
        tpl = self.env.ref('garage_pro.report_invoice_garage_fields')
        self.assertTrue(tpl)

    # ------------------------------------------------------------------
    # Tests : report rendering (HTML)
    # ------------------------------------------------------------------

    def test_05_quotation_report_renders_html(self):
        """Le rapport devis se génère en HTML sans erreur."""
        report = self.env['ir.actions.report']._get_report_from_name(
            'garage_pro.report_garage_quotation'
        )
        html_content = report._render_qweb_html(
            'garage_pro.report_garage_quotation',
            self.quotation.ids,
        )
        self.assertTrue(html_content)
        body = html_content[0]
        self.assertIn(self.quotation.name, body.decode('utf-8'))

    def test_06_repair_order_report_renders_html(self):
        """Le rapport OR se génère en HTML sans erreur."""
        report = self.env['ir.actions.report']._get_report_from_name(
            'garage_pro.report_garage_repair_order'
        )
        html_content = report._render_qweb_html(
            'garage_pro.report_garage_repair_order',
            self.repair_order.ids,
        )
        self.assertTrue(html_content)
        body = html_content[0]
        self.assertIn(self.repair_order.name, body.decode('utf-8'))

    def test_07_quality_checklist_report_renders_html(self):
        """Le rapport checklist QC se génère en HTML sans erreur."""
        report = self.env['ir.actions.report']._get_report_from_name(
            'garage_pro.report_garage_quality_checklist'
        )
        html_content = report._render_qweb_html(
            'garage_pro.report_garage_quality_checklist',
            self.checklist.ids,
        )
        self.assertTrue(html_content)
        body = html_content[0]
        self.assertIn('Contrôle', body.decode('utf-8'))

    # ------------------------------------------------------------------
    # Tests : contenu du rapport devis
    # ------------------------------------------------------------------

    def test_08_quotation_report_contains_vehicle_info(self):
        """Le rapport devis affiche les infos véhicule."""
        report = self.env['ir.actions.report']._get_report_from_name(
            'garage_pro.report_garage_quotation'
        )
        html = report._render_qweb_html(
            'garage_pro.report_garage_quotation',
            self.quotation.ids,
        )[0].decode('utf-8')
        self.assertIn('RPT-001', html)
        self.assertIn('Client Test Reports', html)

    def test_09_quotation_report_contains_lines(self):
        """Le rapport devis affiche les lignes."""
        report = self.env['ir.actions.report']._get_report_from_name(
            'garage_pro.report_garage_quotation'
        )
        html = report._render_qweb_html(
            'garage_pro.report_garage_quotation',
            self.quotation.ids,
        )[0].decode('utf-8')
        self.assertIn('Redressage capot', html)
        self.assertIn('Pare-chocs avant', html)

    def test_10_repair_order_report_contains_lines(self):
        """Le rapport OR affiche les lignes de travaux."""
        report = self.env['ir.actions.report']._get_report_from_name(
            'garage_pro.report_garage_repair_order'
        )
        html = report._render_qweb_html(
            'garage_pro.report_garage_repair_order',
            self.repair_order.ids,
        )[0].decode('utf-8')
        self.assertIn('Redressage capot', html)
        self.assertIn('Pare-chocs avant', html)

    def test_11_quality_report_contains_items(self):
        """Le rapport QC affiche les points de contrôle."""
        report = self.env['ir.actions.report']._get_report_from_name(
            'garage_pro.report_garage_quality_checklist'
        )
        html = report._render_qweb_html(
            'garage_pro.report_garage_quality_checklist',
            self.checklist.ids,
        )[0].decode('utf-8')
        # La checklist a des items standard + carrosserie (car labor_body dans les lignes)
        self.assertIn('Propreté extérieure', html)
        self.assertIn('Ajustement jeux de carrosserie', html)

    def test_12_quotation_report_shows_totals(self):
        """Le rapport devis affiche le total TTC."""
        report = self.env['ir.actions.report']._get_report_from_name(
            'garage_pro.report_garage_quotation'
        )
        html = report._render_qweb_html(
            'garage_pro.report_garage_quotation',
            self.quotation.ids,
        )[0].decode('utf-8')
        self.assertIn('Total TTC', html)
        self.assertIn('Total HT', html)
