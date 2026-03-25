# Module 12 — Facturation multi-payeur

## Principe

La facturation garage est complexe car un même OR peut générer plusieurs factures vers des destinataires différents. On étend `account.move` d'Odoo, on ne recrée RIEN.

## Extension `account.move`

```python
class AccountMove(models.Model):
    _inherit = 'account.move'

    garage_repair_order_id = fields.Many2one('garage.repair.order', string="OR garage")
    garage_claim_id = fields.Many2one('garage.insurance.claim', string="Sinistre")
    is_garage_invoice = fields.Boolean(compute='_compute_is_garage', store=True)
    garage_invoice_type = fields.Selection([
        ('client_full', 'Client (intégralité)'),
        ('insurance', 'Assurance'),
        ('franchise', 'Franchise client'),
        ('deposit', 'Acompte'),
        ('subcontract', 'Sous-traitance (achat)'),
        ('courtesy_charge', 'Facturation véhicule courtoisie'),
        ('warranty', 'Reprise garantie'),
    ], string="Type facture garage")
```

## Scénarios de facturation

### 1. Client simple (pas d'assurance)
- 1 facture `out_invoice` → `partner_id = customer_id`
- Toutes les lignes de l'OR (MO + pièces + sous-traitance)
- TVA 21% standard (Belgique)

### 2. Client professionnel luxembourgeois
- 1 facture `out_invoice` → `partner_id = customer_id`
- `fiscal_position_id` = position fiscale intracommunautaire
- TVA autoliquidée (0% sur facture, mention "Autoliquidation art. 44 CTVA")
- **Utiliser le mécanisme natif Odoo** : `account.fiscal.position` avec mapping de taxes

### 3. Sinistre avec assurance (cas standard)
- **Facture assurance** : `partner_id` = compagnie d'assurance, montant = total OR - franchise
- **Facture franchise** : `partner_id` = client, montant = franchise
- Les deux factures référencent le même OR

### 4. Sinistre sans franchise
- 1 seule facture assurance, pas de facture client
- Convention directe : l'assurance paie tout

### 5. Acompte
- Le client paie un acompte avant les travaux (courant pour les travaux sans assurance)
- Créer une facture d'acompte (`garage_invoice_type = 'deposit'`)
- Au moment de la facture finale : déduire l'acompte (ligne négative ou mécanisme natif Odoo)

### 6. Avoir / Note de crédit
- Si malfaçon ou trop-facturé → `move_type = 'out_refund'`
- Lié à l'OR via `garage_repair_order_id`
- Peut concerner la facture client ou la facture assurance

### 7. Facture partielle
- L'OR n'est pas terminé mais le client veut une facture intermédiaire
- Facturer uniquement les lignes marquées `is_done = True`
- Flag `invoice_status = 'partial'` sur l'OR

### 8. Dépassement véhicule courtoisie
- Si le client dépasse les jours gratuits → facture supplémentaire
- `garage_invoice_type = 'courtesy_charge'`
- Montant = `billable_days × daily_charge_rate`

### 9. Différence assurance
- L'assurance paie moins que le montant approuvé → le delta est au choix :
  - Absorbé par le garage (perte)
  - Refacturé au client (avec accord)
  - Contesté (relance assurance)

## TVA — Configuration requise

```xml
<!-- Position fiscale intracommunautaire (Belgique → Luxembourg pro) -->
<record id="fiscal_position_intracom_lu" model="account.fiscal.position">
    <field name="name">Intracommunautaire - Luxembourg</field>
    <field name="auto_apply">True</field>
    <field name="country_id" ref="base.lu"/>
    <field name="vat_required">True</field>
</record>
<!-- Mapping de taxes dans cette position fiscale -->
```

## Rapport facture personnalisé

Étendre le template de facture Odoo (`account.report_invoice_document`) pour afficher :
- N° d'OR
- Immatriculation véhicule
- N° de sinistre et nom de l'assurance (si applicable)
- Détail par catégorie (MO carrosserie, MO peinture, MO mécanique, Pièces, Sous-traitance)
- Mention franchise si applicable

---

# Module 13 — Communication

## Templates email

```xml
<!-- Email envoi devis -->
<record id="email_template_quotation_sent" model="mail.template">
    <field name="name">Garage - Devis envoyé</field>
    <field name="model_id" ref="garage_pro.model_garage_quotation"/>
    <field name="email_from">{{ object.company_id.email }}</field>
    <field name="email_to">{{ object.customer_id.email }}</field>
    <field name="subject">Votre devis {{ object.name }} - {{ object.vehicle_id.license_plate }}</field>
    <field name="body_html"><![CDATA[
        <p>Bonjour {{ object.customer_id.name }},</p>
        <p>Veuillez trouver ci-joint votre devis <strong>{{ object.name }}</strong>
        pour votre véhicule <strong>{{ object.vehicle_id.license_plate }}</strong>.</p>
        <p>Montant total : <strong>{{ object.amount_total }} €</strong></p>
        <p>Ce devis est valable jusqu'au {{ object.date_validity }}.</p>
        <p>Cordialement,<br/>{{ object.company_id.name }}</p>
    ]]></field>
</record>

<!-- Email OR en cours -->
<record id="email_template_or_in_progress" model="mail.template">
    <field name="name">Garage - Travaux en cours</field>
    <field name="model_id" ref="garage_pro.model_garage_repair_order"/>
    <field name="subject">Travaux en cours - {{ object.vehicle_id.license_plate }}</field>
    <field name="body_html"><![CDATA[
        <p>Bonjour {{ object.customer_id.name }},</p>
        <p>Nous vous informons que les travaux sur votre véhicule
        <strong>{{ object.vehicle_id.license_plate }}</strong> (OR {{ object.name }})
        ont débuté.</p>
        <p>Date de restitution estimée : <strong>{{ object.estimated_delivery_date }}</strong></p>
    ]]></field>
</record>

<!-- Email véhicule prêt -->
<record id="email_template_or_ready" model="mail.template">
    <field name="name">Garage - Véhicule prêt</field>
    <field name="model_id" ref="garage_pro.model_garage_repair_order"/>
    <field name="subject">Votre véhicule est prêt ! - {{ object.vehicle_id.license_plate }}</field>
    <field name="body_html"><![CDATA[
        <p>Bonjour {{ object.customer_id.name }},</p>
        <p>Bonne nouvelle ! Votre véhicule <strong>{{ object.vehicle_id.license_plate }}</strong>
        est prêt à être récupéré.</p>
        <p>Merci de prendre rendez-vous pour la restitution.</p>
    ]]></field>
</record>
```

## Cron — Relances et alertes

```xml
<!-- Relance assurance : expertise en attente > 5 jours -->
<record id="cron_claim_expertise_reminder" model="ir.cron">
    <field name="name">Garage - Relance expertise</field>
    <field name="model_id" ref="garage_pro.model_garage_insurance_claim"/>
    <field name="code">model.cron_reminder_expertise()</field>
    <field name="interval_number">1</field>
    <field name="interval_type">days</field>
</record>

<!-- Alertes CT prochain -->
<record id="cron_ct_alerts" model="ir.cron">
    <field name="name">Garage - Alertes contrôle technique</field>
    <field name="model_id" ref="garage_pro.model_fleet_vehicle"/>
    <field name="code">model.cron_ct_alerts()</field>
    <field name="interval_number">7</field>
    <field name="interval_type">days</field>
</record>

<!-- Alertes entretien prochain -->
<record id="cron_maintenance_alerts" model="ir.cron">
    <field name="name">Garage - Alertes entretien</field>
    <field name="model_id" ref="garage_pro.model_garage_maintenance_plan_item"/>
    <field name="code">model.cron_maintenance_alerts()</field>
    <field name="interval_number">7</field>
    <field name="interval_type">days</field>
</record>

<!-- Alerte véhicule non récupéré > 7 jours après "prêt" -->
<record id="cron_vehicle_not_picked_up" model="ir.cron">
    <field name="name">Garage - Véhicule non récupéré</field>
    <field name="model_id" ref="garage_pro.model_garage_repair_order"/>
    <field name="code">model.cron_vehicle_not_picked_up()</field>
    <field name="interval_number">1</field>
    <field name="interval_type">days</field>
</record>
```

## Portail client (extension `portal`)

Étendre le portail Odoo natif pour que le client connecté puisse voir :
- Ses OR en cours avec statut
- Ses devis (avec bouton "Accepter" / "Refuser")
- Ses factures
- Les photos de son véhicule

```python
class CustomerPortal(CustomerPortal):
    # Ajouter un compteur dans le portail
    def _prepare_home_portal_values(self, counters):
        values = super()._prepare_home_portal_values(counters)
        partner = request.env.user.partner_id
        if 'repair_order_count' in counters:
            values['repair_order_count'] = request.env['garage.repair.order'].search_count([
                ('customer_id', '=', partner.id),
                ('state', 'not in', ['cancelled']),
            ])
        return values
```

---

# Module 14 — Qualité

## Modèle : `garage.quality.checklist`

```python
class GarageQualityChecklist(models.Model):
    _name = 'garage.quality.checklist'
    _description = 'Checklist contrôle qualité'
    _inherit = ['mail.thread']

    repair_order_id = fields.Many2one('garage.repair.order', string="OR", required=True)
    checklist_type = fields.Selection([
        ('bodywork', 'Contrôle carrosserie'),
        ('paint', 'Contrôle peinture'),
        ('mechanic', 'Contrôle mécanique'),
        ('general', 'Contrôle général pré-livraison'),
    ], string="Type de contrôle")

    item_ids = fields.One2many('garage.quality.check.item', 'checklist_id', string="Points de contrôle")
    is_fully_checked = fields.Boolean(compute='_compute_fully_checked', store=True)
    checked_by = fields.Many2one('res.users', string="Contrôlé par")
    check_date = fields.Datetime(string="Date du contrôle")
    overall_result = fields.Selection([
        ('pass', 'Conforme'),
        ('fail', 'Non conforme'),
        ('partial', 'Partiellement conforme'),
    ], compute='_compute_result', store=True)
    notes = fields.Text(string="Remarques générales")

    @api.model
    def create_from_repair_order(self, repair_order):
        """Crée une checklist auto basée sur les types d'opérations de l'OR"""
        checklist = self.create({
            'repair_order_id': repair_order.id,
            'checklist_type': 'general',
        })
        # Items standards pré-livraison
        standard_items = [
            ('Propreté extérieure du véhicule', 'visual'),
            ('Propreté intérieure du véhicule', 'visual'),
            ('Vérification éclairage', 'functional'),
            ('Vérification niveaux (huile, LR, lave-glace)', 'functional'),
            ('Pression pneus', 'measurement'),
        ]
        # Items carrosserie si applicable
        if repair_order.line_ids.filtered(lambda l: l.line_type == 'labor_body'):
            standard_items += [
                ('Ajustement jeux de carrosserie', 'measurement'),
                ('Alignement panneaux', 'visual'),
                ('Étanchéité joints', 'functional'),
            ]
        # Items peinture
        if repair_order.line_ids.filtered(lambda l: l.line_type == 'labor_paint'):
            standard_items += [
                ('Qualité peinture — pas de coulure', 'visual'),
                ('Qualité peinture — pas de grain', 'visual'),
                ('Raccord de teinte uniforme', 'visual'),
                ('Brillance et vernis', 'visual'),
            ]
        # Items mécanique
        if repair_order.line_ids.filtered(lambda l: l.line_type == 'labor_mech'):
            standard_items += [
                ('Essai routier effectué', 'functional'),
                ('Pas de bruit anormal', 'functional'),
                ('Voyants tableau de bord éteints', 'visual'),
                ('Codes défaut effacés', 'functional'),
            ]
        for item_name, check_type in standard_items:
            self.env['garage.quality.check.item'].create({
                'checklist_id': checklist.id,
                'name': item_name,
                'check_type': check_type,
            })
        return checklist

class GarageQualityCheckItem(models.Model):
    _name = 'garage.quality.check.item'
    _description = 'Point de contrôle qualité'
    _order = 'sequence, id'

    checklist_id = fields.Many2one('garage.quality.checklist', ondelete='cascade')
    sequence = fields.Integer(default=10)
    name = fields.Char(string="Point de contrôle", required=True)
    check_type = fields.Selection([
        ('visual', 'Contrôle visuel'),
        ('functional', 'Contrôle fonctionnel'),
        ('measurement', 'Mesure'),
    ], string="Type")
    result = fields.Selection([
        ('ok', 'OK'),
        ('nok', 'Non conforme'),
        ('na', 'Non applicable'),
    ], string="Résultat")
    notes = fields.Char(string="Remarque")
    photo = fields.Binary(string="Photo")
```

---

# Module 15 — Documentation

## Modèle : `garage.documentation`

```python
class GarageDocumentation(models.Model):
    _name = 'garage.documentation'
    _description = 'Document / Photo garage'
    _order = 'create_date desc'

    name = fields.Char(string="Description")
    repair_order_id = fields.Many2one('garage.repair.order', string="OR")
    claim_id = fields.Many2one('garage.insurance.claim', string="Sinistre")
    vehicle_id = fields.Many2one('fleet.vehicle', string="Véhicule")

    doc_type = fields.Selection([
        ('photo_before', 'Photo avant réparation'),
        ('photo_during', 'Photo pendant réparation'),
        ('photo_after', 'Photo après réparation'),
        ('photo_damage', 'Photo dommage'),
        ('accident_report', 'Constat amiable'),
        ('expertise_report', 'Rapport d\'expertise'),
        ('invoice_supplier', 'Facture fournisseur'),
        ('technical_report', 'Rapport technique'),
        ('courtesy_checkin', 'État des lieux courtoisie'),
        ('other', 'Autre'),
    ], string="Type de document", required=True)

    file = fields.Binary(string="Fichier", required=True)
    filename = fields.Char(string="Nom de fichier")
    file_size = fields.Integer(string="Taille (Ko)", compute='_compute_file_size')
    thumbnail = fields.Binary(string="Miniature", compute='_compute_thumbnail', store=True)

    damage_zone = fields.Selection([...], string="Zone (si photo dommage)")
    taken_by = fields.Many2one('res.users', string="Pris par", default=lambda self: self.env.user)
    taken_date = fields.Datetime(string="Date", default=fields.Datetime.now)
    notes = fields.Text(string="Notes")
    is_visible_portal = fields.Boolean(
        string="Visible sur le portail client",
        default=True,
    )
```

---

# Module 16 — Reporting

## Modèles SQL Views pour le reporting

```python
class GarageReportRevenue(models.Model):
    _name = 'garage.report.revenue'
    _description = 'Rapport CA garage'
    _auto = False  # Vue SQL
    _order = 'date desc'

    date = fields.Date(string="Date")
    month = fields.Char(string="Mois")
    year = fields.Char(string="Année")
    activity_type = fields.Selection([
        ('bodywork', 'Carrosserie'),
        ('paint', 'Peinture'),
        ('mechanic', 'Mécanique'),
        ('parts', 'Pièces'),
        ('subcontract', 'Sous-traitance'),
    ], string="Activité")
    revenue = fields.Monetary(string="CA HT", currency_field='currency_id')
    cost = fields.Monetary(string="Coût", currency_field='currency_id')
    margin = fields.Monetary(string="Marge", currency_field='currency_id')
    margin_rate = fields.Float(string="Taux marge (%)")
    ro_count = fields.Integer(string="Nombre d'OR")
    currency_id = fields.Many2one('res.currency')

    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute("""
            CREATE OR REPLACE VIEW %s AS (
                SELECT
                    row_number() OVER () AS id,
                    ro.actual_end_date::date AS date,
                    to_char(ro.actual_end_date, 'YYYY-MM') AS month,
                    to_char(ro.actual_end_date, 'YYYY') AS year,
                    CASE
                        WHEN rol.line_type IN ('labor_body') THEN 'bodywork'
                        WHEN rol.line_type IN ('labor_paint', 'paint_material') THEN 'paint'
                        WHEN rol.line_type IN ('labor_mech') THEN 'mechanic'
                        WHEN rol.line_type = 'parts' THEN 'parts'
                        WHEN rol.line_type = 'subcontract' THEN 'subcontract'
                        ELSE 'mechanic'
                    END AS activity_type,
                    SUM(rol.amount_total) AS revenue,
                    0 AS cost,
                    SUM(rol.amount_total) AS margin,
                    100.0 AS margin_rate,
                    COUNT(DISTINCT ro.id) AS ro_count,
                    ro.currency_id
                FROM garage_repair_order_line rol
                JOIN garage_repair_order ro ON ro.id = rol.repair_order_id
                WHERE ro.state IN ('delivered', 'invoiced')
                GROUP BY ro.actual_end_date::date, month, year,
                    activity_type, ro.currency_id
            )
        """ % self._table)
```

## KPIs à exposer en dashboard

| KPI | Source | Calcul |
|-----|--------|--------|
| CA HT total (période) | `garage.report.revenue` | SUM(revenue) |
| CA par activité | `garage.report.revenue` | GROUP BY activity_type |
| Taux productivité atelier | `garage.repair.order` | SUM(total_worked_hours) / SUM(total_allocated_hours) |
| Délai moyen réparation (jours) | `garage.repair.order` | AVG(actual_end_date - actual_start_date) |
| Nombre OR en cours | `garage.repair.order` | COUNT WHERE state IN (confirmed..qc_done) |
| Créances assurance en cours | `account.move` | SUM(amount_residual) WHERE garage_claim_id IS NOT NULL |
| Ancienneté créances assurance | `account.move` | GROUP BY tranches (0-30j, 30-60j, 60-90j, >90j) |
| Taux occupation postes | `garage.planning.slot` | SUM(duration) / capacité théorique |
| Véhicules courtoisie prêtés | `garage.courtesy.vehicle` | COUNT WHERE state = 'loaned' |
| OR en attente pièces | `garage.repair.order` | COUNT WHERE state = 'parts_waiting' |
| Devis en attente réponse | `garage.quotation` | COUNT WHERE state = 'sent' |
| Taux conversion devis → OR | `garage.quotation` | COUNT(converted) / COUNT(sent) |

### Vue dashboard (XML)
Utiliser une vue Kanban dashboard Odoo avec des widgets de type `aggregate`, `pie_chart`, `bar_chart`.

---

# Intégration CarVertical (Phase 2)

Voir fichier dédié : `integrations/carvertical.md`
