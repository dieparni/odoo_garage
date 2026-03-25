# Intégration CarVertical — Phase 2

## Vue d'ensemble

[CarVertical](https://www.carvertical.com/) fournit un rapport d'historique véhicule à partir du VIN : kilométrage vérifié, historique de dommages, rappels constructeur, historique d'immatriculation, etc.

L'intégration permet de **préremplir automatiquement** la fiche véhicule dans Odoo et de détecter les anomalies (km falsifié, dommages cachés).

---

## API CarVertical

### Authentification
- API REST, authentification par clé API (`X-API-Key` header)
- Clé à stocker dans `ir.config_parameter` : `garage_pro.carvertical_api_key`
- Endpoint base : `https://api.carvertical.com/v1`

### Endpoint principal
```
GET /reports/{vin}
Headers:
  X-API-Key: <api_key>
  Accept: application/json
```

### Données retournées (à mapper vers le véhicule Odoo)

| Champ CarVertical | Champ Odoo cible | Notes |
|-------------------|------------------|-------|
| `vehicle.make` | `model_id.brand_id` | Mapping vers fleet.vehicle.model.brand |
| `vehicle.model` | `model_id` | Mapping vers fleet.vehicle.model |
| `vehicle.year` | `model_year` | |
| `vehicle.bodyType` | `body_type` | Mapping string → selection |
| `vehicle.engine.displacement` | `engine_displacement` | En cm³ |
| `vehicle.engine.power.kw` | `power_kw` | |
| `vehicle.engine.code` | `engine_code` | |
| `vehicle.fuelType` | `fuel_type` | Mapping string → selection |
| `vehicle.transmission` | `transmission_type` | |
| `vehicle.drivetrain` | `drive_type` | |
| `vehicle.color` | `paint_color_name` | Nom de couleur |
| `mileage.records[-1].value` | Km actuel (info) | Dernier relevé connu |
| `mileage.isTampered` | `carvertical_mileage_ok` | Inverse (ok = not tampered) |
| `damages` | `carvertical_damage_history` | JSON → Text résumé |
| `recalls` | Info à afficher | |
| `registrations` | Info à afficher | |

---

## Configuration Odoo

### Paramètres système

```python
class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    carvertical_api_key = fields.Char(
        string="Clé API CarVertical",
        config_parameter='garage_pro.carvertical_api_key',
    )
    carvertical_auto_lookup = fields.Boolean(
        string="Recherche auto à la création véhicule",
        config_parameter='garage_pro.carvertical_auto_lookup',
        help="Si activé, une recherche CarVertical est lancée automatiquement quand un VIN est saisi",
    )
    carvertical_cache_days = fields.Integer(
        string="Durée cache (jours)",
        config_parameter='garage_pro.carvertical_cache_days',
        default=30,
        help="Nombre de jours pendant lesquels un résultat CarVertical est considéré comme frais",
    )
```

---

## Wizard de recherche

### Modèle : `garage.carvertical.lookup.wizard`

```python
class CarVerticalLookupWizard(models.TransientModel):
    _name = 'garage.carvertical.lookup.wizard'
    _description = 'Recherche CarVertical'

    vehicle_id = fields.Many2one('fleet.vehicle', string="Véhicule")
    vin = fields.Char(string="VIN", required=True, size=17)

    # Résultats
    state = fields.Selection([
        ('input', 'Saisie VIN'),
        ('loading', 'Recherche en cours'),
        ('result', 'Résultats'),
        ('error', 'Erreur'),
    ], default='input')

    # Données retournées
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

    def action_search(self):
        """Lance la recherche CarVertical"""
        self.ensure_one()
        api_key = self.env['ir.config_parameter'].sudo().get_param('garage_pro.carvertical_api_key')
        if not api_key:
            raise UserError("Clé API CarVertical non configurée. Allez dans Configuration > Garage.")

        try:
            import requests
            response = requests.get(
                f'https://api.carvertical.com/v1/reports/{self.vin}',
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

            # Parser les résultats
            vehicle_data = data.get('vehicle', {})
            mileage_data = data.get('mileage', {})
            damages = data.get('damages', [])
            recalls = data.get('recalls', [])
            registrations = data.get('registrations', [])

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
                'result_last_mileage': mileage_data.get('records', [{}])[-1].get('value', 0) if mileage_data.get('records') else 0,
                'result_mileage_tampered': mileage_data.get('isTampered', False),
                'result_damage_count': len(damages),
                'result_damage_summary': self._format_damages(damages),
                'result_recall_count': len(recalls),
                'result_recall_summary': self._format_recalls(recalls),
                'result_registration_count': len(registrations),
                'result_report_url': data.get('reportUrl', ''),
            })

        except requests.exceptions.Timeout:
            self.write({'state': 'error', 'error_message': 'Timeout — le service CarVertical ne répond pas.'})
        except requests.exceptions.RequestException as e:
            self.write({'state': 'error', 'error_message': 'Erreur de connexion : %s' % str(e)})

        return self._reopen_wizard()

    def action_apply_to_vehicle(self):
        """Applique les résultats au véhicule Odoo"""
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

        # Mapping fuel_type
        fuel_map = {
            'petrol': 'gasoline', 'gasoline': 'gasoline',
            'diesel': 'diesel',
            'electric': 'electric',
            'hybrid': 'hybrid',
            'lpg': 'lpg', 'cng': 'cng',
        }
        if self.result_fuel_type:
            vals['fuel_type'] = fuel_map.get(self.result_fuel_type.lower(), 'gasoline')

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
            vals['body_type'] = body_map.get(self.result_body_type.lower(), 'other')

        # Mapping transmission
        trans_map = {
            'manual': 'manual', 'automatic': 'automatic',
            'semi-automatic': 'semi_auto', 'cvt': 'cvt',
        }
        if self.result_transmission:
            vals['transmission_type'] = trans_map.get(self.result_transmission.lower(), 'manual')

        # CarVertical metadata
        vals['carvertical_last_check'] = fields.Datetime.now()
        vals['carvertical_report_url'] = self.result_report_url
        vals['carvertical_mileage_ok'] = not self.result_mileage_tampered
        vals['carvertical_damage_history'] = self.result_damage_summary

        self.vehicle_id.write(vals)

        # Mapping marque/modèle (si pas encore renseigné)
        if self.result_make and self.result_model and not self.vehicle_id.model_id:
            brand = self.env['fleet.vehicle.model.brand'].search(
                [('name', 'ilike', self.result_make)], limit=1
            )
            if not brand:
                brand = self.env['fleet.vehicle.model.brand'].create({'name': self.result_make})
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

    def _format_damages(self, damages):
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
        if not recalls:
            return "Aucun rappel enregistré."
        lines = []
        for r in recalls:
            lines.append("- %s : %s" % (r.get('date', '?'), r.get('description', 'N/A')))
        return '\n'.join(lines)

    def _reopen_wizard(self):
        return {
            'type': 'ir.actions.act_window',
            'res_model': self._name,
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new',
        }
```

### Vue wizard

```xml
<record id="garage_carvertical_wizard_form" model="ir.ui.view">
    <field name="name">CarVertical Lookup</field>
    <field name="model">garage.carvertical.lookup.wizard</field>
    <field name="arch" type="xml">
        <form>
            <group attrs="{'invisible': [('state', '!=', 'input')]}">
                <field name="vin"/>
                <field name="vehicle_id" invisible="1"/>
            </group>
            <group attrs="{'invisible': [('state', '!=', 'result')]}">
                <group string="Identification">
                    <field name="result_make"/>
                    <field name="result_model"/>
                    <field name="result_year"/>
                    <field name="result_body_type"/>
                    <field name="result_color"/>
                </group>
                <group string="Moteur">
                    <field name="result_engine_code"/>
                    <field name="result_displacement"/>
                    <field name="result_power_kw"/>
                    <field name="result_fuel_type"/>
                    <field name="result_transmission"/>
                    <field name="result_drivetrain"/>
                </group>
                <group string="Historique">
                    <field name="result_last_mileage"/>
                    <field name="result_mileage_tampered"
                        decoration-danger="result_mileage_tampered"/>
                    <field name="result_damage_count"/>
                    <field name="result_recall_count"/>
                    <field name="result_registration_count"/>
                </group>
                <group string="Détails">
                    <field name="result_damage_summary"/>
                    <field name="result_recall_summary"/>
                    <field name="result_report_url" widget="url"/>
                </group>
            </group>
            <group attrs="{'invisible': [('state', '!=', 'error')]}">
                <field name="error_message" readonly="1"/>
            </group>
            <field name="state" invisible="1"/>
            <footer>
                <button string="Rechercher" name="action_search" type="object"
                    class="btn-primary"
                    attrs="{'invisible': [('state', '!=', 'input')]}"/>
                <button string="Appliquer au véhicule" name="action_apply_to_vehicle"
                    type="object" class="btn-primary"
                    attrs="{'invisible': [('state', '!=', 'result')]}"/>
                <button string="Nouvelle recherche" name="action_search" type="object"
                    attrs="{'invisible': [('state', 'not in', ['result', 'error'])]}"/>
                <button string="Fermer" class="btn-secondary" special="cancel"/>
            </footer>
        </form>
    </field>
</record>
```

---

## Cache des résultats

Pour éviter de consommer des crédits inutilement, stocker les résultats bruts :

```python
class CarVerticalCache(models.Model):
    _name = 'garage.carvertical.cache'
    _description = 'Cache résultats CarVertical'

    vin = fields.Char(string="VIN", required=True, index=True)
    lookup_date = fields.Datetime(string="Date recherche", default=fields.Datetime.now)
    raw_response = fields.Text(string="Réponse brute (JSON)")
    is_expired = fields.Boolean(compute='_compute_expired')

    _sql_constraints = [
        ('vin_unique', 'UNIQUE(vin)', 'Un seul cache par VIN'),
    ]

    def _compute_expired(self):
        cache_days = int(self.env['ir.config_parameter'].sudo().get_param(
            'garage_pro.carvertical_cache_days', 30))
        for rec in self:
            if rec.lookup_date:
                rec.is_expired = (fields.Datetime.now() - rec.lookup_date).days > cache_days
            else:
                rec.is_expired = True
```

---

## Points d'attention

1. **API CarVertical** : vérifier la documentation exacte de l'API au moment de l'implémentation — les endpoints et formats peuvent avoir évolué
2. **Coût** : chaque appel API consomme un crédit CarVertical (payant). D'où le cache et l'option auto/manuel
3. **VIN invalide** : si le VIN ne passe pas la validation format, ne pas appeler l'API
4. **Rate limiting** : respecter les limites de l'API, implémenter un retry avec backoff si nécessaire
5. **Fallback** : si CarVertical est indisponible, le workflow de création véhicule ne doit pas être bloqué
