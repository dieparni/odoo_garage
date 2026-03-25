# Module 02 — Clients garage (`garage.customer` extension)

## Principe

Extension du modèle `res.partner` d'Odoo. On n'utilise PAS un modèle séparé : les clients garage sont des contacts Odoo enrichis de champs métier. Cela garantit la compatibilité avec la facturation, les achats, le CRM, et le portail.

---

## Modèle : extension `res.partner`

**Héritage** : `_inherit = 'res.partner'`

### Champs ajoutés

```python
# === IDENTIFICATION GARAGE ===
is_garage_customer = fields.Boolean(
    string="Client garage",
    default=False,
    help="Cocher pour activer les fonctionnalités garage sur ce contact",
)
garage_customer_type = fields.Selection([
    ('private', 'Particulier'),
    ('professional', 'Professionnel'),
    ('fleet_manager', 'Gestionnaire de flotte'),
    ('leasing_company', 'Société de leasing'),
    ('insurance_company', 'Compagnie d\'assurance'),
    ('subcontractor', 'Sous-traitant'),
    ('dealer', 'Concessionnaire'),
], string="Type client garage")
is_leasing_company = fields.Boolean(
    string="Société de leasing",
    compute='_compute_is_leasing',
    store=True,
)
is_insurance_company = fields.Boolean(
    string="Compagnie d'assurance",
    compute='_compute_is_insurance',
    store=True,
)
is_subcontractor = fields.Boolean(
    string="Sous-traitant",
    compute='_compute_is_subcontractor',
    store=True,
)

# === VÉHICULES ===
garage_vehicle_ids = fields.One2many(
    'fleet.vehicle',
    'driver_id',
    string="Véhicules (conducteur)",
    domain=[('active', '=', True)],
)
owned_vehicle_ids = fields.One2many(
    'fleet.vehicle',
    'owner_id',
    string="Véhicules possédés",
)
vehicle_count = fields.Integer(
    compute='_compute_vehicle_count',
    string="Nombre de véhicules",
)

# === FACTURATION GARAGE ===
garage_payment_term_id = fields.Many2one(
    'account.payment.term',
    string="Conditions de paiement garage",
    help="Conditions spécifiques pour les travaux garage (peut différer du défaut contact)",
)
garage_credit_limit = fields.Monetary(
    string="Plafond crédit garage",
    currency_field='currency_id',
    help="Montant maximum d'encours autorisé pour ce client",
)
garage_discount_rate = fields.Float(
    string="Remise garage (%)",
    help="Remise commerciale automatiquement appliquée sur les devis garage",
)
garage_price_list = fields.Selection([
    ('standard', 'Tarif standard'),
    ('fleet', 'Tarif flotte'),
    ('vip', 'Tarif VIP'),
    ('insurance', 'Tarif agréé assurance'),
], string="Grille tarifaire", default='standard')

# === PRÉFÉRENCES ===
preferred_language = fields.Selection([
    ('fr', 'Français'),
    ('nl', 'Néerlandais'),
    ('en', 'Anglais'),
    ('de', 'Allemand'),
], string="Langue de communication", default='fr')
preferred_contact_method = fields.Selection([
    ('email', 'Email'),
    ('sms', 'SMS'),
    ('phone', 'Téléphone'),
    ('portal', 'Portail en ligne'),
], string="Moyen de contact préféré", default='email')
receive_maintenance_alerts = fields.Boolean(
    string="Recevoir alertes entretien",
    default=True,
)
receive_ct_alerts = fields.Boolean(
    string="Recevoir alertes CT",
    default=True,
)

# === FLOTTE (si gestionnaire de flotte) ===
fleet_contact_ids = fields.One2many(
    'res.partner',
    'fleet_manager_id',
    string="Conducteurs de la flotte",
)
fleet_manager_id = fields.Many2one(
    'res.partner',
    string="Gestionnaire de flotte",
    domain="[('garage_customer_type', '=', 'fleet_manager')]",
    help="Le gestionnaire qui autorise les travaux pour ce conducteur",
)
fleet_approval_required = fields.Boolean(
    string="Approbation flotte requise",
    help="Si coché, les devis au-dessus du seuil nécessitent validation du gestionnaire",
)
fleet_approval_threshold = fields.Monetary(
    string="Seuil approbation (€)",
    currency_field='currency_id',
    help="Montant au-dessus duquel le gestionnaire doit approuver",
)

# === HISTORIQUE GARAGE ===
repair_order_ids = fields.One2many(
    'garage.repair.order',
    'customer_id',
    string="Ordres de réparation",
)
repair_order_count = fields.Integer(
    compute='_compute_ro_count',
)
total_invoiced_garage = fields.Monetary(
    string="Total facturé garage",
    compute='_compute_total_invoiced_garage',
    currency_field='currency_id',
)
last_visit_date = fields.Date(
    string="Dernière visite",
    compute='_compute_last_visit',
    store=True,
)

# === CONTENTIEUX ===
is_blocked_garage = fields.Boolean(
    string="Bloqué (garage)",
    help="Si coché, aucun nouveau devis/OR ne peut être créé pour ce client",
    tracking=True,
)
blocked_reason = fields.Text(string="Raison du blocage")
outstanding_garage_balance = fields.Monetary(
    string="Encours garage",
    compute='_compute_outstanding_balance',
    currency_field='currency_id',
)
```

### Méthodes

```python
@api.depends('garage_customer_type')
def _compute_is_leasing(self):
    for rec in self:
        rec.is_leasing_company = rec.garage_customer_type == 'leasing_company'

@api.depends('garage_customer_type')
def _compute_is_insurance(self):
    for rec in self:
        rec.is_insurance_company = rec.garage_customer_type == 'insurance_company'

@api.depends('garage_customer_type')
def _compute_is_subcontractor(self):
    for rec in self:
        rec.is_subcontractor = rec.garage_customer_type == 'subcontractor'

def _compute_outstanding_balance(self):
    """Calcule l'encours : factures garage non payées"""
    for rec in self:
        invoices = self.env['account.move'].search([
            ('partner_id', '=', rec.id),
            ('move_type', '=', 'out_invoice'),
            ('payment_state', 'not in', ['paid', 'reversed']),
            # Filtrer uniquement les factures garage — via un tag ou un champ custom
        ])
        rec.outstanding_garage_balance = sum(invoices.mapped('amount_residual'))

@api.constrains('is_blocked_garage')
def _check_blocked_with_reason(self):
    for rec in self:
        if rec.is_blocked_garage and not rec.blocked_reason:
            raise ValidationError("Veuillez indiquer la raison du blocage.")
```

### Vues

**Extension du formulaire `res.partner`** (ne pas recréer, hériter) :
- Nouveau notebook page "Garage" visible si `is_garage_customer = True`
- Onglet "Garage — Général" : type client, grille tarifaire, remise, conditions paiement
- Onglet "Garage — Véhicules" : liste des véhicules, bouton "Ajouter un véhicule"
- Onglet "Garage — Flotte" : visible si `garage_customer_type == 'fleet_manager'`
- Onglet "Garage — Historique" : OR passés, montant total facturé, dernière visite
- Onglet "Garage — Préférences" : langue, canal, alertes
- Bouton smart "X Réparations" en haut du formulaire
- Bouton smart "X Véhicules"
- Bannière d'alerte si `is_blocked_garage` : "⚠ Ce client est bloqué. Raison : ..."

**Extension de la liste `res.partner`** :
- Ajouter colonnes optionnelles : type garage, véhicules, encours
- Filtre "Clients garage" sur `is_garage_customer`

---

## Cas de figure détaillés

### 1. Particulier avec plusieurs véhicules
Le contact `res.partner` est lié à N véhicules via `driver_id`. Quand il vient au garage, on sélectionne le véhicule concerné dans le devis/OR.

### 2. Professionnel (entreprise)
- Le `res.partner` entreprise est le client facturable
- Les conducteurs sont des contacts enfants (`parent_id` = l'entreprise)
- Chaque conducteur peut être `driver_id` sur un ou plusieurs véhicules
- Le devis peut être au nom de l'entreprise même si c'est le conducteur qui amène le véhicule

### 3. Gestionnaire de flotte
- Un `res.partner` avec `garage_customer_type = 'fleet_manager'`
- Ses conducteurs sont liés via `fleet_manager_id`
- Workflow : le conducteur amène le véhicule → devis créé → si montant > seuil → notification au gestionnaire → approbation → OR
- Le gestionnaire reçoit un récapitulatif mensuel de tous les travaux sur sa flotte

### 4. Société de leasing
- Le propriétaire réel du véhicule est la société de leasing
- Le payeur peut être : le leaseur, le conducteur, ou l'employeur du conducteur
- Mapping : véhicule.`leasing_company_id` → la société de leasing / véhicule.`driver_id` → le conducteur / devis.`invoice_partner_id` → le payeur (peut être différent du conducteur)

### 5. Client assurance (en tant que payeur)
- Géré séparément dans le module assurance
- Le `res.partner` de l'assurance est utilisé comme `invoice_partner_id` sur la partie assurance de la facture

### 6. Client mauvais payeur
- `is_blocked_garage = True` → un `@api.constrains` ou `check` dans le modèle devis empêche la création de nouveau devis
- Le déblocage nécessite le groupe `garage_pro.group_manager`
- Historique des blocages via le chatter (`tracking=True`)

### 7. Client frontalier (Luxembourg)
- `res.partner` avec adresse Luxembourg et TVA intracommunautaire (LU...)
- Impact facturation : autoliquidation TVA (mécanisme natif Odoo via `account.fiscal.position`)
- S'assurer que la position fiscale "Intracommunautaire" est correctement mappée

### 8. Client éphémère
- Particulier de passage, pas de fidélisation
- Création rapide avec minimum d'infos (nom, téléphone, email)
- Flag `is_garage_customer = True` automatique si créé depuis un devis garage

---

## Points d'attention

1. **Ne jamais dupliquer `res.partner`** : utiliser `_inherit`, pas `_name`
2. **Filtres domaine** : dans les M2O vers `res.partner`, toujours mettre un `domain` pertinent pour ne pas afficher tous les contacts Odoo dans les sélections garage
3. **Compatibilité comptable** : les champs ajoutés ne doivent pas interférer avec le flux standard de facturation Odoo
4. **RGPD** : prévoir une action "Anonymiser" pour droit à l'oubli (effacer données personnelles, garder les données comptables obligatoires)
5. **Performance** : `vehicle_count` et `repair_order_count` sont des `compute` sans `store` si les données changent fréquemment, ou `store=True` avec triggers si on veut du reporting
