"""Tests pour les config defaults, ir.rules et le wizard restitution courtoisie."""

from odoo.exceptions import UserError
from odoo.tests.common import TransactionCase


class TestConfigDefaults(TransactionCase):
    """Tests des paramètres de configuration par défaut."""

    def test_01_default_hourly_rate_body(self):
        """Le taux horaire carrosserie par défaut est 55.0."""
        val = self.env['ir.config_parameter'].get_param(
            'garage_pro.default_hourly_rate_body')
        self.assertEqual(val, '55.0')

    def test_02_default_hourly_rate_paint(self):
        """Le taux horaire peinture par défaut est 55.0."""
        val = self.env['ir.config_parameter'].get_param(
            'garage_pro.default_hourly_rate_paint')
        self.assertEqual(val, '55.0')

    def test_03_default_hourly_rate_mech(self):
        """Le taux horaire mécanique par défaut est 60.0."""
        val = self.env['ir.config_parameter'].get_param(
            'garage_pro.default_hourly_rate_mech')
        self.assertEqual(val, '60.0')

    def test_04_default_vat_rate(self):
        """Le taux TVA par défaut est 21.0."""
        val = self.env['ir.config_parameter'].get_param(
            'garage_pro.default_vat_rate')
        self.assertEqual(val, '21.0')

    def test_05_quotation_validity_days(self):
        """La validité devis par défaut est 30 jours."""
        val = self.env['ir.config_parameter'].get_param(
            'garage_pro.quotation_validity_days')
        self.assertEqual(val, '30')

    def test_06_settings_hourly_fields_exist(self):
        """Les champs taux horaires existent dans res.config.settings."""
        settings = self.env['res.config.settings'].create({})
        self.assertTrue(hasattr(settings, 'garage_default_hourly_rate_body'))
        self.assertTrue(hasattr(settings, 'garage_default_hourly_rate_paint'))
        self.assertTrue(hasattr(settings, 'garage_default_hourly_rate_mech'))
        self.assertTrue(hasattr(settings, 'garage_quotation_validity_days'))


class TestIrRules(TransactionCase):
    """Tests des règles d'accès multi-société."""

    def test_07_quotation_rule_exists(self):
        """La règle multi-société pour les devis existe."""
        rule = self.env.ref('garage_pro.rule_quotation_company', raise_if_not_found=False)
        self.assertTrue(rule)
        self.assertEqual(rule.model_id.model, 'garage.quotation')

    def test_08_repair_order_rule_exists(self):
        """La règle multi-société pour les OR existe."""
        rule = self.env.ref('garage_pro.rule_repair_order_company', raise_if_not_found=False)
        self.assertTrue(rule)
        self.assertEqual(rule.model_id.model, 'garage.repair.order')

    def test_09_subcontract_rule_exists(self):
        """La règle multi-société pour la sous-traitance existe."""
        rule = self.env.ref('garage_pro.rule_subcontract_company', raise_if_not_found=False)
        self.assertTrue(rule)
        self.assertEqual(rule.model_id.model, 'garage.subcontract.order')


class TestCourtesyReturnWizard(TransactionCase):
    """Tests du wizard de restitution courtoisie."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partner = cls.env['res.partner'].create({
            'name': 'Client Wizard Test',
            'is_garage_customer': True,
        })
        brand = cls.env['fleet.vehicle.model.brand'].create({
            'name': 'WizBrand',
        })
        vmodel = cls.env['fleet.vehicle.model'].create({
            'name': 'WizModel',
            'brand_id': brand.id,
        })
        cls.fleet_vehicle = cls.env['fleet.vehicle'].create({
            'model_id': vmodel.id,
            'license_plate': 'WIZ-001-XX',
        })
        cls.courtesy_vehicle = cls.env['garage.courtesy.vehicle'].create({
            'vehicle_id': cls.fleet_vehicle.id,
            'name': 'Courtoisie Wizard',
            'daily_charge_rate': 25.0,
            'max_free_days': 3,
        })

    def _create_active_loan(self):
        """Crée et active un prêt."""
        loan = self.env['garage.courtesy.loan'].create({
            'courtesy_vehicle_id': self.courtesy_vehicle.id,
            'customer_id': self.partner.id,
        })
        loan.action_activate()
        return loan

    def test_10_wizard_creates_from_active_loan(self):
        """Le wizard s'initialise correctement depuis un prêt actif."""
        loan = self._create_active_loan()
        wizard = self.env['garage.courtesy.return.wizard'].with_context(
            active_id=loan.id,
        ).create({
            'loan_id': loan.id,
            'km_end': 55000,
            'fuel_level_end': '3_4',
        })
        self.assertEqual(wizard.loan_id, loan)
        self.assertEqual(wizard.courtesy_vehicle_id, self.courtesy_vehicle)

    def test_11_wizard_confirm_return_no_damage(self):
        """La confirmation sans dommage passe le prêt en 'returned'."""
        loan = self._create_active_loan()
        wizard = self.env['garage.courtesy.return.wizard'].with_context(
            active_id=loan.id,
        ).create({
            'loan_id': loan.id,
            'km_end': 55000,
            'fuel_level_end': 'full',
            'has_damage': False,
        })
        wizard.action_confirm_return()
        self.assertEqual(loan.state, 'returned')
        self.assertEqual(loan.km_end, 55000)
        self.assertEqual(loan.fuel_level_end, 'full')
        self.assertEqual(self.courtesy_vehicle.state, 'available')

    def test_12_wizard_confirm_return_with_damage(self):
        """La confirmation avec dommage passe le prêt en 'damaged'."""
        loan = self._create_active_loan()
        wizard = self.env['garage.courtesy.return.wizard'].with_context(
            active_id=loan.id,
        ).create({
            'loan_id': loan.id,
            'km_end': 55000,
            'fuel_level_end': '1_2',
            'has_damage': True,
            'damage_description': 'Rayure portière droite',
        })
        wizard.action_confirm_return()
        self.assertEqual(loan.state, 'damaged')
        self.assertTrue(loan.has_damage)
        self.assertEqual(loan.damage_description, 'Rayure portière droite')

    def test_13_wizard_rejects_non_active_loan(self):
        """Le wizard refuse de confirmer un prêt qui n'est pas actif."""
        loan = self.env['garage.courtesy.loan'].create({
            'courtesy_vehicle_id': self.courtesy_vehicle.id,
            'customer_id': self.partner.id,
        })
        # Loan is in 'reserved' state
        wizard = self.env['garage.courtesy.return.wizard'].create({
            'loan_id': loan.id,
            'km_end': 55000,
            'fuel_level_end': 'full',
        })
        with self.assertRaises(UserError):
            wizard.action_confirm_return()

    def test_14_wizard_sets_condition_end(self):
        """Le wizard enregistre l'état des lieux retour."""
        loan = self._create_active_loan()
        wizard = self.env['garage.courtesy.return.wizard'].with_context(
            active_id=loan.id,
        ).create({
            'loan_id': loan.id,
            'km_end': 56000,
            'fuel_level_end': '3_4',
            'condition_end': '<p>RAS</p>',
        })
        wizard.action_confirm_return()
        self.assertIn('RAS', loan.condition_end)

    def test_15_wizard_acl_exists(self):
        """Les droits d'accès du wizard existent."""
        acl = self.env['ir.model.access'].search([
            ('model_id.model', '=', 'garage.courtesy.return.wizard'),
        ])
        self.assertTrue(len(acl) >= 2)
