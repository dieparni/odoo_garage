"""Tests pour l'intégration CarVertical (Agent 11)."""

import json
from unittest.mock import MagicMock, patch

from odoo.exceptions import UserError
from odoo.tests.common import TransactionCase


class TestCarVertical(TransactionCase):
    """Tests unitaires pour CarVertical : cache, wizard, settings, application véhicule."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.brand = cls.env['fleet.vehicle.model.brand'].create({
            'name': 'TestBrandCV',
        })
        cls.model = cls.env['fleet.vehicle.model'].create({
            'name': 'TestModelCV',
            'brand_id': cls.brand.id,
        })
        cls.vehicle = cls.env['fleet.vehicle'].create({
            'model_id': cls.model.id,
            'license_plate': 'CV-001',
            'vin_sn': 'WVWZZZ3CZWE987654',
        })
        cls.partner = cls.env['res.partner'].create({
            'name': 'Client CarVertical Test',
        })

    # ------------------------------------------------------------------
    # Cache
    # ------------------------------------------------------------------

    def test_cache_creation(self):
        """Le cache CarVertical se crée correctement."""
        cache = self.env['garage.carvertical.cache'].create({
            'vin': 'WVWZZZ3CZWE987654',
            'raw_response': '{"vehicle": {}}',
        })
        self.assertEqual(cache.vin, 'WVWZZZ3CZWE987654')
        self.assertFalse(cache.is_expired)

    def test_cache_vin_unique(self):
        """La contrainte UNIQUE sur le VIN empêche les doublons."""
        # Nettoyer d'éventuels résidus de tests précédents
        existing = self.env['garage.carvertical.cache'].search(
            [('vin', '=', 'WVWZZZ3CZWEUUUUUU')])
        existing.unlink()
        self.env['garage.carvertical.cache'].create({
            'vin': 'WVWZZZ3CZWEUUUUUU',
            'raw_response': '{}',
        })
        with self.assertRaises(Exception):
            self.env['garage.carvertical.cache'].create({
                'vin': 'WVWZZZ3CZWEUUUUUU',
                'raw_response': '{}',
            })

    def test_cache_expiration(self):
        """Le cache expire après le nombre de jours configuré."""
        from datetime import timedelta
        from odoo import fields as odoo_fields
        # Nettoyer résidus éventuels
        self.env['garage.carvertical.cache'].search(
            [('vin', '=', 'WVWZZZ3CZWEEXPRD1')]).unlink()
        cache = self.env['garage.carvertical.cache'].create({
            'vin': 'WVWZZZ3CZWEEXPRD1',
            'raw_response': '{}',
            'lookup_date': odoo_fields.Datetime.now() - timedelta(days=60),
        })
        self.assertTrue(cache.is_expired)

    def test_cache_not_expired_within_range(self):
        """Le cache n'est pas expiré dans la durée configurée."""
        from datetime import timedelta
        from odoo import fields as odoo_fields
        self.env['ir.config_parameter'].sudo().set_param(
            'garage_pro.carvertical_cache_days', '90')
        self.env['garage.carvertical.cache'].search(
            [('vin', '=', 'WVWZZZ3CZWEEXPRD2')]).unlink()
        cache = self.env['garage.carvertical.cache'].create({
            'vin': 'WVWZZZ3CZWEEXPRD2',
            'raw_response': '{}',
            'lookup_date': odoo_fields.Datetime.now() - timedelta(days=60),
        })
        self.assertFalse(cache.is_expired)

    # ------------------------------------------------------------------
    # Wizard — Création & validation
    # ------------------------------------------------------------------

    def test_wizard_creation(self):
        """Le wizard se crée avec les valeurs par défaut."""
        wizard = self.env['garage.carvertical.lookup.wizard'].create({
            'vehicle_id': self.vehicle.id,
            'vin': 'WVWZZZ3CZWE987654',
        })
        self.assertEqual(wizard.state, 'input')
        self.assertEqual(wizard.vin, 'WVWZZZ3CZWE987654')

    def test_wizard_vin_validation_short(self):
        """Un VIN trop court est rejeté."""
        with self.assertRaises(UserError):
            self.env['garage.carvertical.lookup.wizard'].create({
                'vehicle_id': self.vehicle.id,
                'vin': 'ABC123',
            })

    def test_wizard_vin_validation_invalid_chars(self):
        """Un VIN avec I, O ou Q est rejeté."""
        with self.assertRaises(UserError):
            self.env['garage.carvertical.lookup.wizard'].create({
                'vehicle_id': self.vehicle.id,
                'vin': 'WVWZZZ3CZWI123456',  # I interdit
            })

    # ------------------------------------------------------------------
    # Wizard — Recherche sans clé API
    # ------------------------------------------------------------------

    def test_wizard_search_no_api_key(self):
        """La recherche lève UserError si la clé API n'est pas configurée."""
        self.env['ir.config_parameter'].sudo().set_param(
            'garage_pro.carvertical_api_key', '')
        wizard = self.env['garage.carvertical.lookup.wizard'].create({
            'vehicle_id': self.vehicle.id,
            'vin': 'WVWZZZ3CZWE987654',
        })
        with self.assertRaises(UserError):
            wizard.action_search()

    # ------------------------------------------------------------------
    # Wizard — Parse response
    # ------------------------------------------------------------------

    def test_parse_response_complete(self):
        """_parse_response remplit tous les champs du wizard."""
        wizard = self.env['garage.carvertical.lookup.wizard'].create({
            'vehicle_id': self.vehicle.id,
            'vin': 'WVWZZZ3CZWE987654',
        })
        data = {
            'vehicle': {
                'make': 'Volkswagen',
                'model': 'Golf',
                'year': 2020,
                'bodyType': 'Hatchback',
                'engine': {
                    'code': 'DKRF',
                    'displacement': 1968,
                    'power': {'kw': 110},
                },
                'fuelType': 'Diesel',
                'transmission': 'Automatic',
                'drivetrain': 'FWD',
                'color': 'Noir',
            },
            'mileage': {
                'records': [
                    {'value': 10000, 'date': '2021-01-01'},
                    {'value': 45000, 'date': '2023-06-15'},
                ],
                'isTampered': False,
            },
            'damages': [
                {'date': '2022-03-10', 'type': 'Collision', 'description': 'Choc avant'},
            ],
            'recalls': [
                {'date': '2021-07-01', 'description': 'Rappel airbag'},
            ],
            'registrations': [
                {'country': 'BE', 'date': '2020-01-15'},
                {'country': 'LU', 'date': '2022-06-01'},
            ],
            'reportUrl': 'https://www.carvertical.com/report/123',
        }
        wizard._parse_response(data)

        self.assertEqual(wizard.state, 'result')
        self.assertEqual(wizard.result_make, 'Volkswagen')
        self.assertEqual(wizard.result_model, 'Golf')
        self.assertEqual(wizard.result_year, 2020)
        self.assertEqual(wizard.result_body_type, 'Hatchback')
        self.assertEqual(wizard.result_engine_code, 'DKRF')
        self.assertEqual(wizard.result_displacement, 1968)
        self.assertEqual(wizard.result_power_kw, 110)
        self.assertEqual(wizard.result_fuel_type, 'Diesel')
        self.assertEqual(wizard.result_transmission, 'Automatic')
        self.assertEqual(wizard.result_drivetrain, 'FWD')
        self.assertEqual(wizard.result_color, 'Noir')
        self.assertEqual(wizard.result_last_mileage, 45000)
        self.assertFalse(wizard.result_mileage_tampered)
        self.assertEqual(wizard.result_damage_count, 1)
        self.assertIn('Choc avant', wizard.result_damage_summary)
        self.assertEqual(wizard.result_recall_count, 1)
        self.assertIn('airbag', wizard.result_recall_summary)
        self.assertEqual(wizard.result_registration_count, 2)
        self.assertEqual(wizard.result_report_url, 'https://www.carvertical.com/report/123')

    def test_parse_response_empty(self):
        """_parse_response gère une réponse minimale sans crash."""
        wizard = self.env['garage.carvertical.lookup.wizard'].create({
            'vehicle_id': self.vehicle.id,
            'vin': 'WVWZZZ3CZWE987654',
        })
        wizard._parse_response({})
        self.assertEqual(wizard.state, 'result')
        self.assertEqual(wizard.result_damage_count, 0)
        self.assertEqual(wizard.result_damage_summary, 'Aucun dommage enregistré.')

    def test_parse_response_mileage_tampered(self):
        """Détection d'un kilométrage falsifié."""
        wizard = self.env['garage.carvertical.lookup.wizard'].create({
            'vehicle_id': self.vehicle.id,
            'vin': 'WVWZZZ3CZWE987654',
        })
        wizard._parse_response({
            'mileage': {'isTampered': True, 'records': []},
        })
        self.assertTrue(wizard.result_mileage_tampered)

    # ------------------------------------------------------------------
    # Wizard — Application au véhicule
    # ------------------------------------------------------------------

    def test_apply_to_vehicle_basic(self):
        """action_apply_to_vehicle écrit les champs techniques sur le véhicule."""
        wizard = self.env['garage.carvertical.lookup.wizard'].create({
            'vehicle_id': self.vehicle.id,
            'vin': 'WVWZZZ3CZWE987654',
        })
        wizard._parse_response({
            'vehicle': {
                'engine': {'code': 'DKRF', 'displacement': 1968, 'power': {'kw': 110}},
                'fuelType': 'Diesel',
                'bodyType': 'SUV',
                'transmission': 'Automatic',
                'drivetrain': 'AWD',
                'color': 'Blanc Glacier',
                'year': 2021,
            },
            'mileage': {'isTampered': False, 'records': []},
            'damages': [],
            'recalls': [],
            'registrations': [],
        })
        wizard.action_apply_to_vehicle()

        self.assertEqual(self.vehicle.engine_code, 'DKRF')
        self.assertEqual(self.vehicle.engine_displacement, 1968)
        self.assertEqual(self.vehicle.power_kw, 110)
        self.assertEqual(self.vehicle.fuel_type, 'diesel')
        self.assertEqual(self.vehicle.body_type, 'suv')
        self.assertEqual(self.vehicle.transmission_type, 'automatic')
        self.assertEqual(self.vehicle.drive_type, 'awd')
        self.assertEqual(self.vehicle.paint_color_name, 'Blanc Glacier')
        self.assertEqual(self.vehicle.model_year, '2021')
        self.assertTrue(self.vehicle.carvertical_mileage_ok)
        self.assertTrue(self.vehicle.carvertical_last_check)

    def test_apply_to_vehicle_mileage_tampered_flag(self):
        """Le flag mileage_ok est False quand le km est falsifié."""
        wizard = self.env['garage.carvertical.lookup.wizard'].create({
            'vehicle_id': self.vehicle.id,
            'vin': 'WVWZZZ3CZWE987654',
        })
        wizard._parse_response({
            'mileage': {'isTampered': True, 'records': []},
        })
        wizard.action_apply_to_vehicle()
        self.assertFalse(self.vehicle.carvertical_mileage_ok)

    def test_apply_to_vehicle_no_vehicle_raises(self):
        """action_apply_to_vehicle lève UserError sans véhicule lié."""
        wizard = self.env['garage.carvertical.lookup.wizard'].create({
            'vin': 'WVWZZZ3CZWE987654',
        })
        wizard.state = 'result'
        with self.assertRaises(UserError):
            wizard.action_apply_to_vehicle()

    def test_apply_preserves_existing_model(self):
        """Si le véhicule a déjà un model_id, il n'est pas écrasé."""
        original_model = self.vehicle.model_id
        wizard = self.env['garage.carvertical.lookup.wizard'].create({
            'vehicle_id': self.vehicle.id,
            'vin': 'WVWZZZ3CZWE987654',
        })
        wizard._parse_response({
            'vehicle': {
                'make': 'BMW',
                'model': 'Serie 5',
            },
        })
        wizard.action_apply_to_vehicle()
        # model_id ne doit pas changer car déjà renseigné
        self.assertEqual(self.vehicle.model_id, original_model)

    def test_format_damages_creates_brand_model_objects(self):
        """La recherche ilike crée marque/modèle si inexistants."""
        # Vérifier que la marque n'existe pas encore
        brand = self.env['fleet.vehicle.model.brand'].search(
            [('name', '=', 'Lamborghini')], limit=1)
        if not brand:
            brand = self.env['fleet.vehicle.model.brand'].create(
                {'name': 'Lamborghini'})
        model = self.env['fleet.vehicle.model'].search([
            ('brand_id', '=', brand.id),
            ('name', 'ilike', 'Huracan'),
        ], limit=1)
        if not model:
            model = self.env['fleet.vehicle.model'].create({
                'brand_id': brand.id,
                'name': 'Huracan',
            })
        self.assertEqual(model.brand_id.name, 'Lamborghini')
        self.assertEqual(model.name, 'Huracan')

    # ------------------------------------------------------------------
    # Wizard — Fuel / body / transmission mappings
    # ------------------------------------------------------------------

    def test_fuel_type_mapping_petrol(self):
        """'petrol' est mappé vers 'gasoline'."""
        wizard = self.env['garage.carvertical.lookup.wizard'].create({
            'vehicle_id': self.vehicle.id,
            'vin': 'WVWZZZ3CZWE987654',
        })
        wizard._parse_response({'vehicle': {'fuelType': 'Petrol'}})
        wizard.action_apply_to_vehicle()
        self.assertEqual(self.vehicle.fuel_type, 'gasoline')

    def test_body_type_mapping_estate(self):
        """'estate' est mappé vers 'break'."""
        wizard = self.env['garage.carvertical.lookup.wizard'].create({
            'vehicle_id': self.vehicle.id,
            'vin': 'WVWZZZ3CZWE987654',
        })
        wizard._parse_response({'vehicle': {'bodyType': 'Estate'}})
        wizard.action_apply_to_vehicle()
        self.assertEqual(self.vehicle.body_type, 'break')

    def test_transmission_mapping_cvt(self):
        """'cvt' est mappé correctement."""
        wizard = self.env['garage.carvertical.lookup.wizard'].create({
            'vehicle_id': self.vehicle.id,
            'vin': 'WVWZZZ3CZWE987654',
        })
        wizard._parse_response({'vehicle': {'transmission': 'CVT'}})
        wizard.action_apply_to_vehicle()
        self.assertEqual(self.vehicle.transmission_type, 'cvt')

    # ------------------------------------------------------------------
    # Wizard — Format helpers
    # ------------------------------------------------------------------

    def test_format_damages_empty(self):
        """Pas de dommages → message par défaut."""
        wizard = self.env['garage.carvertical.lookup.wizard'].create({
            'vehicle_id': self.vehicle.id,
            'vin': 'WVWZZZ3CZWE987654',
        })
        result = wizard._format_damages([])
        self.assertEqual(result, 'Aucun dommage enregistré.')

    def test_format_damages_with_data(self):
        """Les dommages sont formatés en liste."""
        wizard = self.env['garage.carvertical.lookup.wizard'].create({
            'vehicle_id': self.vehicle.id,
            'vin': 'WVWZZZ3CZWE987654',
        })
        damages = [
            {'date': '2022-01-01', 'type': 'Collision', 'description': 'Choc arrière'},
            {'date': '2023-06-15', 'type': 'Grêle', 'description': 'Impacts capot'},
        ]
        result = wizard._format_damages(damages)
        self.assertIn('Choc arrière', result)
        self.assertIn('Impacts capot', result)
        self.assertEqual(result.count('\n'), 1)  # 2 lignes, 1 saut

    def test_format_recalls_empty(self):
        """Pas de rappels → message par défaut."""
        wizard = self.env['garage.carvertical.lookup.wizard'].create({
            'vehicle_id': self.vehicle.id,
            'vin': 'WVWZZZ3CZWE987654',
        })
        result = wizard._format_recalls([])
        self.assertEqual(result, 'Aucun rappel enregistré.')

    def test_format_recalls_with_data(self):
        """Les rappels sont formatés en liste."""
        wizard = self.env['garage.carvertical.lookup.wizard'].create({
            'vehicle_id': self.vehicle.id,
            'vin': 'WVWZZZ3CZWE987654',
        })
        recalls = [{'date': '2021-07-01', 'description': 'Airbag défectueux'}]
        result = wizard._format_recalls(recalls)
        self.assertIn('Airbag défectueux', result)

    # ------------------------------------------------------------------
    # Vehicle — Champs CarVertical
    # ------------------------------------------------------------------

    def test_vehicle_carvertical_fields_exist(self):
        """Les 4 champs CarVertical existent sur fleet.vehicle."""
        self.assertIn('carvertical_last_check',
                      self.env['fleet.vehicle']._fields)
        self.assertIn('carvertical_report_url',
                      self.env['fleet.vehicle']._fields)
        self.assertIn('carvertical_mileage_ok',
                      self.env['fleet.vehicle']._fields)
        self.assertIn('carvertical_damage_history',
                      self.env['fleet.vehicle']._fields)

    def test_vehicle_action_carvertical_lookup(self):
        """Le bouton CarVertical ouvre le wizard pré-rempli."""
        result = self.vehicle.action_carvertical_lookup()
        self.assertEqual(result['res_model'], 'garage.carvertical.lookup.wizard')
        self.assertEqual(result['target'], 'new')
        wizard = self.env['garage.carvertical.lookup.wizard'].browse(result['res_id'])
        self.assertEqual(wizard.vehicle_id, self.vehicle)
        self.assertEqual(wizard.vin, self.vehicle.vin_sn)

    # ------------------------------------------------------------------
    # Configuration
    # ------------------------------------------------------------------

    def test_config_settings_carvertical_fields(self):
        """Les paramètres CarVertical sont accessibles via res.config.settings."""
        settings = self.env['res.config.settings'].create({})
        self.assertIn('carvertical_api_key',
                      self.env['res.config.settings']._fields)
        self.assertIn('carvertical_auto_lookup',
                      self.env['res.config.settings']._fields)
        self.assertIn('carvertical_cache_days',
                      self.env['res.config.settings']._fields)

    def test_config_parameter_persistence(self):
        """Les paramètres CarVertical sont stockés en ir.config_parameter."""
        self.env['ir.config_parameter'].sudo().set_param(
            'garage_pro.carvertical_api_key', 'test-key-123')
        value = self.env['ir.config_parameter'].sudo().get_param(
            'garage_pro.carvertical_api_key')
        self.assertEqual(value, 'test-key-123')

    # ------------------------------------------------------------------
    # Wizard — Recherche avec cache hit
    # ------------------------------------------------------------------

    def test_search_uses_cache(self):
        """La recherche utilise le cache si le VIN est déjà connu et non expiré."""
        self.env['ir.config_parameter'].sudo().set_param(
            'garage_pro.carvertical_api_key', 'test-key')
        cached_data = {
            'vehicle': {'make': 'Cached', 'model': 'Car'},
            'mileage': {'records': [], 'isTampered': False},
            'damages': [],
            'recalls': [],
            'registrations': [],
        }
        # Nettoyer résidus éventuels
        self.env['garage.carvertical.cache'].search(
            [('vin', '=', 'WVWZZZ3CZWE987654')]).unlink()
        self.env['garage.carvertical.cache'].create({
            'vin': 'WVWZZZ3CZWE987654',
            'raw_response': json.dumps(cached_data),
        })
        wizard = self.env['garage.carvertical.lookup.wizard'].create({
            'vehicle_id': self.vehicle.id,
            'vin': 'WVWZZZ3CZWE987654',
        })
        # action_search should use cache — no HTTP call needed
        wizard.action_search()
        self.assertEqual(wizard.state, 'result')
        self.assertEqual(wizard.result_make, 'Cached')

    # ------------------------------------------------------------------
    # Wizard — Reopen
    # ------------------------------------------------------------------

    def test_reopen_wizard(self):
        """_reopen_wizard retourne une action window correcte."""
        wizard = self.env['garage.carvertical.lookup.wizard'].create({
            'vehicle_id': self.vehicle.id,
            'vin': 'WVWZZZ3CZWE987654',
        })
        result = wizard._reopen_wizard()
        self.assertEqual(result['type'], 'ir.actions.act_window')
        self.assertEqual(result['res_model'], 'garage.carvertical.lookup.wizard')
        self.assertEqual(result['target'], 'new')
