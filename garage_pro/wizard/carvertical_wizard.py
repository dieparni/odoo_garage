"""Wizard de recherche CarVertical — interroge l'API et applique les résultats au véhicule."""

import json
import logging
import re

from odoo import api, fields, models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class CarVerticalLookupWizard(models.TransientModel):
    """Assistant de recherche historique véhicule via l'API CarVertical."""

    _name = 'garage.carvertical.lookup.wizard'
    _description = 'Recherche CarVertical'

    vehicle_id = fields.Many2one('fleet.vehicle', string="Véhicule")
    vin = fields.Char(string="VIN", required=True, size=17)

    state = fields.Selection([
        ('input', 'Saisie VIN'),
        ('result', 'Résultats'),
        ('error', 'Erreur'),
    ], default='input', string="État")

    # --- Résultats ---
    result_make = fields.Char(string="Marque")
    result_model = fields.Char(string="Modèle")
    result_year = fields.Integer(string="Année")
    result_body_type = fields.Char(string="Type carrosserie")
    result_engine_code = fields.Char(string="Code moteur")
    result_displacement = fields.Integer(string="Cylindrée (cm³)")
    result_power_kw = fields.Integer(string="Puissance (kW)")
    result_fuel_type = fields.Char(string="Carburant")
    result_transmission = fields.Char(string="Boîte")
    result_drivetrain = fields.Char(string="Transmission")
    result_color = fields.Char(string="Couleur")
    result_last_mileage = fields.Integer(string="Dernier km connu")
    result_mileage_tampered = fields.Boolean(string="Km falsifié détecté")
    result_damage_count = fields.Integer(string="Nombre de dommages")
    result_damage_summary = fields.Text(string="Résumé dommages")
    result_recall_count = fields.Integer(string="Rappels constructeur")
    result_recall_summary = fields.Text(string="Résumé rappels")
    result_registration_count = fields.Integer(string="Nombre d'immatriculations")
    result_report_url = fields.Char(string="URL rapport complet")

    error_message = fields.Text(string="Message d'erreur")

    # ------------------------------------------------------------------
    # Validation VIN
    # ------------------------------------------------------------------

    @api.constrains('vin')
    def _check_vin_format(self):
        """Valide le format VIN avant tout appel API."""
        for rec in self:
            if rec.vin:
                vin = rec.vin.strip().upper()
                if len(vin) != 17 or not re.match(r'^[A-HJ-NPR-Z0-9]{17}$', vin):
                    raise UserError(
                        "Le VIN doit contenir exactement 17 caractères "
                        "alphanumériques (I, O, Q interdits)."
                    )

    # ------------------------------------------------------------------
    # Actions
    # ------------------------------------------------------------------

    def action_search(self):
        """Lance la recherche CarVertical (avec cache)."""
        self.ensure_one()
        api_key = self.env['ir.config_parameter'].sudo().get_param(
            'garage_pro.carvertical_api_key')
        if not api_key:
            raise UserError(
                "Clé API CarVertical non configurée. "
                "Allez dans Configuration > Paramètres > Garage."
            )

        vin = self.vin.strip().upper()

        # Vérifier le cache
        cache = self.env['garage.carvertical.cache'].sudo().search(
            [('vin', '=', vin)], limit=1)
        if cache and not cache.is_expired:
            _logger.info("CarVertical cache hit pour VIN %s", vin)
            data = json.loads(cache.raw_response)
            self._parse_response(data)
            return self._reopen_wizard()

        # Appel API
        try:
            import requests
            response = requests.get(
                'https://api.carvertical.com/v1/reports/%s' % vin,
                headers={
                    'X-API-Key': api_key,
                    'Accept': 'application/json',
                },
                timeout=30,
            )

            if response.status_code == 404:
                self.write({
                    'state': 'error',
                    'error_message': 'VIN non trouvé dans la base CarVertical.',
                })
                return self._reopen_wizard()

            if response.status_code == 402:
                self.write({
                    'state': 'error',
                    'error_message': 'Crédit CarVertical insuffisant. Rechargez votre compte.',
                })
                return self._reopen_wizard()

            response.raise_for_status()
            data = response.json()

            # Mettre en cache
            if cache:
                cache.write({
                    'raw_response': json.dumps(data),
                    'lookup_date': fields.Datetime.now(),
                })
            else:
                self.env['garage.carvertical.cache'].sudo().create({
                    'vin': vin,
                    'raw_response': json.dumps(data),
                })

            self._parse_response(data)

        except ImportError:
            self.write({
                'state': 'error',
                'error_message': "Le module Python 'requests' n'est pas installé.",
            })
        except Exception as e:
            if 'Timeout' in type(e).__name__:
                self.write({
                    'state': 'error',
                    'error_message': 'Timeout — le service CarVertical ne répond pas.',
                })
            else:
                _logger.exception("Erreur CarVertical pour VIN %s", vin)
                self.write({
                    'state': 'error',
                    'error_message': 'Erreur de connexion : %s' % str(e),
                })

        return self._reopen_wizard()

    def _parse_response(self, data):
        """Parse la réponse JSON et écrit les résultats sur le wizard."""
        vehicle_data = data.get('vehicle', {})
        mileage_data = data.get('mileage', {})
        damages = data.get('damages', [])
        recalls = data.get('recalls', [])
        registrations = data.get('registrations', [])

        mileage_records = mileage_data.get('records', [])
        last_mileage = mileage_records[-1].get('value', 0) if mileage_records else 0

        self.write({
            'state': 'result',
            'result_make': vehicle_data.get('make', ''),
            'result_model': vehicle_data.get('model', ''),
            'result_year': vehicle_data.get('year', 0),
            'result_body_type': vehicle_data.get('bodyType', ''),
            'result_engine_code': vehicle_data.get('engine', {}).get('code', ''),
            'result_displacement': vehicle_data.get('engine', {}).get('displacement', 0),
            'result_power_kw': vehicle_data.get('engine', {}).get('power', {}).get('kw', 0),
            'result_fuel_type': vehicle_data.get('fuelType', ''),
            'result_transmission': vehicle_data.get('transmission', ''),
            'result_drivetrain': vehicle_data.get('drivetrain', ''),
            'result_color': vehicle_data.get('color', ''),
            'result_last_mileage': last_mileage,
            'result_mileage_tampered': mileage_data.get('isTampered', False),
            'result_damage_count': len(damages),
            'result_damage_summary': self._format_damages(damages),
            'result_recall_count': len(recalls),
            'result_recall_summary': self._format_recalls(recalls),
            'result_registration_count': len(registrations),
            'result_report_url': data.get('reportUrl', ''),
        })

    def action_apply_to_vehicle(self):
        """Applique les résultats CarVertical au véhicule Odoo."""
        self.ensure_one()
        if not self.vehicle_id:
            raise UserError("Aucun véhicule lié.")

        vals = {}
        if self.result_engine_code:
            vals['engine_code'] = self.result_engine_code
        if self.result_displacement:
            vals['engine_displacement'] = self.result_displacement
        if self.result_power_kw:
            vals['power_kw'] = self.result_power_kw
        if self.result_color:
            vals['paint_color_name'] = self.result_color
        if self.result_year:
            vals['model_year'] = str(self.result_year)

        # Mapping fuel_type CarVertical → Odoo
        fuel_map = {
            'petrol': 'gasoline', 'gasoline': 'gasoline',
            'diesel': 'diesel',
            'electric': 'electric',
            'hybrid': 'hybrid',
            'lpg': 'lpg', 'cng': 'cng',
        }
        if self.result_fuel_type:
            vals['fuel_type'] = fuel_map.get(
                self.result_fuel_type.lower(), 'gasoline')

        # Mapping body_type
        body_map = {
            'sedan': 'sedan', 'saloon': 'sedan',
            'estate': 'break', 'wagon': 'break',
            'suv': 'suv', 'crossover': 'suv',
            'coupe': 'coupe', 'coupé': 'coupe',
            'convertible': 'cabriolet', 'cabriolet': 'cabriolet',
            'mpv': 'monospace', 'minivan': 'monospace',
            'van': 'utilitaire', 'pickup': 'pickup',
            'hatchback': 'citadine',
        }
        if self.result_body_type:
            vals['body_type'] = body_map.get(
                self.result_body_type.lower(), 'other')

        # Mapping transmission
        trans_map = {
            'manual': 'manual', 'automatic': 'automatic',
            'semi-automatic': 'semi_auto', 'cvt': 'cvt',
        }
        if self.result_transmission:
            vals['transmission_type'] = trans_map.get(
                self.result_transmission.lower(), 'manual')

        # Mapping drivetrain
        drive_map = {
            'fwd': 'fwd', 'front-wheel': 'fwd',
            'rwd': 'rwd', 'rear-wheel': 'rwd',
            'awd': 'awd', 'all-wheel': 'awd',
            '4wd': '4wd', '4x4': '4wd',
        }
        if self.result_drivetrain:
            vals['drive_type'] = drive_map.get(
                self.result_drivetrain.lower(), False)

        # Métadonnées CarVertical
        vals['carvertical_last_check'] = fields.Datetime.now()
        vals['carvertical_report_url'] = self.result_report_url or False
        vals['carvertical_mileage_ok'] = not self.result_mileage_tampered
        vals['carvertical_damage_history'] = self.result_damage_summary or False

        self.vehicle_id.write(vals)

        # Mapping marque/modèle si pas encore renseigné
        if self.result_make and self.result_model and not self.vehicle_id.model_id:
            brand = self.env['fleet.vehicle.model.brand'].search(
                [('name', 'ilike', self.result_make)], limit=1)
            if not brand:
                brand = self.env['fleet.vehicle.model.brand'].create(
                    {'name': self.result_make})
            model = self.env['fleet.vehicle.model'].search([
                ('brand_id', '=', brand.id),
                ('name', 'ilike', self.result_model),
            ], limit=1)
            if not model:
                model = self.env['fleet.vehicle.model'].create({
                    'brand_id': brand.id,
                    'name': self.result_model,
                })
            self.vehicle_id.model_id = model.id

        return {'type': 'ir.actions.act_window_close'}

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _format_damages(self, damages):
        """Formate la liste de dommages en texte lisible."""
        if not damages:
            return "Aucun dommage enregistré."
        lines = []
        for d in damages:
            lines.append("- %s (%s) : %s" % (
                d.get('date', '?'),
                d.get('type', '?'),
                d.get('description', 'N/A'),
            ))
        return '\n'.join(lines)

    def _format_recalls(self, recalls):
        """Formate la liste de rappels constructeur en texte lisible."""
        if not recalls:
            return "Aucun rappel enregistré."
        lines = []
        for r in recalls:
            lines.append("- %s : %s" % (
                r.get('date', '?'),
                r.get('description', 'N/A'),
            ))
        return '\n'.join(lines)

    def _reopen_wizard(self):
        """Ré-ouvre le wizard après action (pour rester dans la modale)."""
        return {
            'type': 'ir.actions.act_window',
            'res_model': self._name,
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new',
        }
