# Module 03 — Assurances & Sinistres

## Principe

Deux modèles principaux : la compagnie d'assurance (configuration) et le sinistre (objet transactionnel lié à un véhicule et un client). Le sinistre est le pivot entre le devis/OR et le flux de facturation assurance.

---

## Modèle : `garage.insurance.company`

```python
class GarageInsuranceCompany(models.Model):
    _name = 'garage.insurance.company'
    _description = 'Compagnie d\'assurance'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string="Nom", required=True, tracking=True)
    partner_id = fields.Many2one(
        'res.partner',
        string="Contact Odoo",
        required=True,
        help="Le contact res.partner correspondant (pour facturation)",
        domain="[('is_company', '=', True)]",
    )
    code = fields.Char(string="Code interne", help="Code court (ex: AXA, ETH, AG)")
    active = fields.Boolean(default=True)

    # === CONTACTS ===
    expert_contact_ids = fields.One2many(
        'garage.insurance.expert',
        'company_id',
        string="Experts agréés",
    )
    main_contact_name = fields.Char(string="Contact principal")
    main_contact_phone = fields.Char(string="Téléphone contact")
    main_contact_email = fields.Char(string="Email contact")
    claims_email = fields.Char(
        string="Email déclaration sinistres",
        help="Email pour envoyer les devis et documents",
    )
    portal_url = fields.Char(string="URL portail en ligne")

    # === BARÈMES & TARIFICATION ===
    hourly_rate_bodywork = fields.Monetary(
        string="Taux horaire carrosserie agréé (€/h)",
        currency_field='currency_id',
        tracking=True,
    )
    hourly_rate_paint = fields.Monetary(
        string="Taux horaire peinture agréé (€/h)",
        currency_field='currency_id',
    )
    hourly_rate_mechanic = fields.Monetary(
        string="Taux horaire mécanique agréé (€/h)",
        currency_field='currency_id',
    )
    parts_coefficient = fields.Float(
        string="Coefficient pièces",
        default=1.0,
        help="Coefficient appliqué sur le prix catalogue des pièces (ex: 1.0 = prix catalogue)",
    )
    paint_material_rate = fields.Float(
        string="Taux matière peinture (€/h peinte)",
        help="Forfait matière peinture par heure de peinture allouée",
    )
    allows_aftermarket_parts = fields.Boolean(
        string="Accepte pièces aftermarket",
        default=False,
    )
    allows_used_parts = fields.Boolean(
        string="Accepte pièces d'occasion",
        default=False,
    )
    max_vehicle_age_used_parts = fields.Integer(
        string="Âge max véhicule pour pièces neuves (ans)",
        help="Au-delà de cet âge, l'assurance impose des pièces d'occasion",
    )

    # === CONDITIONS ===
    payment_term_id = fields.Many2one(
        'account.payment.term',
        string="Conditions de paiement",
    )
    average_payment_days = fields.Integer(
        string="Délai moyen constaté (jours)",
        help="Délai réel moyen de paiement observé",
    )
    convention_type = fields.Selection([
        ('direct', 'Convention directe (tiers payant)'),
        ('indirect', 'Indirect (via assuré)'),
        ('mixed', 'Mixte'),
    ], string="Type de convention", default='indirect')

    # === STATS ===
    claim_ids = fields.One2many('garage.insurance.claim', 'insurance_company_id', string="Sinistres")
    claim_count = fields.Integer(compute='_compute_claim_count')
    total_outstanding = fields.Monetary(
        string="Encours total",
        compute='_compute_outstanding',
        currency_field='currency_id',
    )
    currency_id = fields.Many2one('res.currency', default=lambda self: self.env.company.currency_id)

    # === NOTES ===
    notes = fields.Html(string="Notes / Particularités")
```

---

## Modèle : `garage.insurance.expert`

```python
class GarageInsuranceExpert(models.Model):
    _name = 'garage.insurance.expert'
    _description = 'Expert automobile'
    _inherit = ['mail.thread']

    name = fields.Char(string="Nom", required=True)
    company_id = fields.Many2one(
        'garage.insurance.company',
        string="Compagnie d'assurance",
    )
    partner_id = fields.Many2one('res.partner', string="Contact")
    phone = fields.Char(string="Téléphone")
    email = fields.Char(string="Email")
    expertise_type = fields.Selection([
        ('on_site', 'Sur place (se déplace)'),
        ('remote', 'Expertise à distance (photo/vidéo)'),
        ('both', 'Les deux'),
    ], string="Type d'expertise", default='on_site')
    active = fields.Boolean(default=True)
    notes = fields.Text(string="Notes")
```

---

## Modèle : `garage.insurance.claim`

C'est le modèle le plus critique du module assurance. Il représente un sinistre.

```python
class GarageInsuranceClaim(models.Model):
    _name = 'garage.insurance.claim'
    _description = 'Sinistre assurance'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'create_date desc'

    name = fields.Char(
        string="Référence sinistre",
        default='Nouveau',
        readonly=True,
        copy=False,
    )

    # === STATUT ===
    state = fields.Selection([
        ('draft', 'Brouillon'),
        ('declared', 'Déclaré'),
        ('expertise_pending', 'En attente d\'expertise'),
        ('expertise_done', 'Expertise réalisée'),
        ('approved', 'Accord reçu'),
        ('supplement_pending', 'Supplément en attente'),
        ('supplement_approved', 'Supplément approuvé'),
        ('work_in_progress', 'Travaux en cours'),
        ('invoiced', 'Facturé'),
        ('paid', 'Payé'),
        ('vei', 'VEI (Perte totale)'),
        ('disputed', 'Litige'),
        ('cancelled', 'Annulé'),
    ], string="Statut", default='draft', tracking=True, group_expand='_group_expand_states')

    # === LIENS ===
    vehicle_id = fields.Many2one(
        'fleet.vehicle', string="Véhicule", required=True, tracking=True,
    )
    customer_id = fields.Many2one(
        'res.partner', string="Client (assuré)", required=True, tracking=True,
    )
    insurance_company_id = fields.Many2one(
        'garage.insurance.company', string="Compagnie d'assurance", required=True, tracking=True,
    )
    expert_id = fields.Many2one(
        'garage.insurance.expert', string="Expert assigné",
        domain="[('company_id', '=', insurance_company_id)]",
    )
    quotation_id = fields.Many2one(
        'garage.quotation', string="Devis principal",
    )
    repair_order_id = fields.Many2one(
        'garage.repair.order', string="Ordre de réparation",
    )

    # === SINISTRE ===
    claim_date = fields.Date(string="Date du sinistre", required=True, tracking=True)
    declaration_date = fields.Date(string="Date de déclaration")
    claim_type = fields.Selection([
        ('collision', 'Collision'),
        ('theft', 'Vol'),
        ('vandalism', 'Vandalisme'),
        ('hail', 'Grêle'),
        ('glass', 'Bris de glace'),
        ('natural', 'Catastrophe naturelle'),
        ('fire', 'Incendie'),
        ('parking', 'Dommage parking'),
        ('animal', 'Collision animale'),
        ('other', 'Autre'),
    ], string="Type de sinistre", required=True, tracking=True)
    claim_description = fields.Html(string="Circonstances du sinistre")
    has_third_party = fields.Boolean(string="Tiers impliqué")
    third_party_info = fields.Text(
        string="Informations tiers",
        help="Nom, assurance, immatriculation du tiers",
    )
    police_report = fields.Boolean(string="PV de police établi")
    police_report_number = fields.Char(string="Numéro PV")

    # === ASSURANCE CLIENT ===
    policy_number = fields.Char(string="N° de police")
    insurance_claim_number = fields.Char(
        string="N° sinistre assurance",
        help="Numéro attribué par la compagnie d'assurance",
        tracking=True,
    )

    # === FRANCHISE ===
    franchise_type = fields.Selection([
        ('none', 'Pas de franchise'),
        ('fixed', 'Montant fixe'),
        ('percentage', 'Pourcentage'),
        ('variable', 'Variable (selon contrat)'),
    ], string="Type de franchise", default='fixed')
    franchise_amount = fields.Monetary(
        string="Montant franchise (€)",
        currency_field='currency_id',
        tracking=True,
    )
    franchise_percentage = fields.Float(
        string="Franchise (%)",
        help="Pourcentage du montant total des réparations",
    )
    franchise_computed = fields.Monetary(
        string="Franchise calculée",
        compute='_compute_franchise',
        currency_field='currency_id',
        store=True,
    )

    # === EXPERTISE ===
    expertise_date = fields.Datetime(string="Date expertise prévue")
    expertise_done_date = fields.Datetime(string="Date expertise réalisée")
    expertise_type = fields.Selection([
        ('on_site', 'Sur place'),
        ('remote', 'À distance (photos)'),
        ('waived', 'Dispensé d\'expertise'),
    ], string="Type d'expertise")
    expertise_report = fields.Binary(string="Rapport d'expertise")
    expertise_report_filename = fields.Char(string="Nom fichier expertise")

    # === MONTANTS ===
    estimated_amount = fields.Monetary(
        string="Montant estimé (devis)",
        currency_field='currency_id',
    )
    approved_amount = fields.Monetary(
        string="Montant approuvé (expert)",
        currency_field='currency_id',
        tracking=True,
    )
    supplement_amount = fields.Monetary(
        string="Montant supplément",
        currency_field='currency_id',
    )
    total_approved = fields.Monetary(
        string="Total approuvé",
        compute='_compute_total_approved',
        currency_field='currency_id',
        store=True,
    )
    invoiced_amount = fields.Monetary(
        string="Montant facturé",
        compute='_compute_invoiced',
        currency_field='currency_id',
    )
    paid_amount = fields.Monetary(
        string="Montant payé",
        compute='_compute_paid',
        currency_field='currency_id',
    )

    # === VEI ===
    is_vei = fields.Boolean(string="Véhicule Économiquement Irréparable")
    vei_vehicle_value = fields.Monetary(
        string="Valeur vénale véhicule",
        currency_field='currency_id',
    )
    vei_repair_cost = fields.Monetary(
        string="Coût réparation estimé",
        currency_field='currency_id',
    )
    vei_customer_decision = fields.Selection([
        ('pending', 'En attente de décision'),
        ('accept_loss', 'Accepte la perte totale'),
        ('repair_own_cost', 'Répare à ses frais'),
        ('contest', 'Conteste la décision'),
    ], string="Décision client VEI")

    # === SUPPLÉMENT ===
    supplement_ids = fields.One2many(
        'garage.insurance.supplement',
        'claim_id',
        string="Suppléments",
    )
    supplement_count = fields.Integer(compute='_compute_supplement_count')

    # === DOCUMENTS ===
    accident_report = fields.Binary(string="Constat amiable")
    accident_report_filename = fields.Char()
    document_ids = fields.One2many(
        'garage.documentation',
        'claim_id',
        string="Documents / Photos",
    )

    currency_id = fields.Many2one('res.currency', default=lambda self: self.env.company.currency_id)

    # === SÉQUENCE ===
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', 'Nouveau') == 'Nouveau':
                vals['name'] = self.env['ir.sequence'].next_by_code('garage.insurance.claim') or 'Nouveau'
        return super().create(vals_list)
```

### Workflow sinistre — méthodes d'action

```python
def action_declare(self):
    """Brouillon → Déclaré"""
    self.write({'state': 'declared', 'declaration_date': fields.Date.today()})

def action_request_expertise(self):
    """Déclaré → En attente d'expertise"""
    self.write({'state': 'expertise_pending'})
    # Créer une activité pour relancer si pas d'expertise sous 5 jours
    self.activity_schedule(
        'mail.mail_activity_data_todo',
        date_deadline=fields.Date.today() + timedelta(days=5),
        summary="Relancer expert pour expertise sinistre %s" % self.name,
    )

def action_expertise_done(self):
    """En attente → Expertise réalisée"""
    self.write({
        'state': 'expertise_done',
        'expertise_done_date': fields.Datetime.now(),
    })

def action_approve(self):
    """Expertise réalisée → Approuvé"""
    if not self.approved_amount:
        raise UserError("Veuillez saisir le montant approuvé par l'expert avant de valider.")
    self.write({'state': 'approved'})

def action_request_supplement(self):
    """Ouvre le wizard de supplément"""
    return {
        'type': 'ir.actions.act_window',
        'name': 'Demande de supplément',
        'res_model': 'garage.insurance.supplement.wizard',
        'view_mode': 'form',
        'target': 'new',
        'context': {'default_claim_id': self.id},
    }

def action_mark_vei(self):
    """Marquer comme VEI"""
    self.write({
        'state': 'vei',
        'is_vei': True,
        'vei_customer_decision': 'pending',
    })

def action_start_work(self):
    """Approuvé → Travaux en cours (vérifie que l'OR existe)"""
    if not self.repair_order_id:
        raise UserError("Aucun ordre de réparation n'est lié à ce sinistre.")
    self.write({'state': 'work_in_progress'})

def action_dispute(self):
    """Passer en litige"""
    self.write({'state': 'disputed'})

def action_cancel(self):
    """Annuler le sinistre"""
    self.write({'state': 'cancelled'})
```

---

## Modèle : `garage.insurance.supplement`

```python
class GarageInsuranceSupplement(models.Model):
    _name = 'garage.insurance.supplement'
    _description = 'Supplément sinistre'
    _inherit = ['mail.thread']
    _order = 'create_date desc'

    claim_id = fields.Many2one('garage.insurance.claim', required=True, ondelete='cascade')
    name = fields.Char(string="Description", required=True)
    amount = fields.Monetary(string="Montant supplément", currency_field='currency_id')
    reason = fields.Html(string="Justification détaillée")
    state = fields.Selection([
        ('draft', 'Brouillon'),
        ('sent', 'Envoyé à l\'expert'),
        ('approved', 'Approuvé'),
        ('rejected', 'Refusé'),
    ], default='draft', tracking=True)
    approved_amount = fields.Monetary(string="Montant approuvé", currency_field='currency_id')
    expert_response_date = fields.Date(string="Date réponse expert")
    document_ids = fields.Many2many('ir.attachment', string="Pièces jointes (photos)")
    currency_id = fields.Many2one('res.currency', default=lambda self: self.env.company.currency_id)
```

---

## Vues

### Formulaire sinistre
- **Statusbar** en haut avec tous les états
- **En-tête** : véhicule, client, assurance, expert, n° sinistre
- **Onglet "Sinistre"** : type, date, circonstances, tiers, PV
- **Onglet "Expertise"** : dates, rapport, montants approuvés
- **Onglet "Suppléments"** : liste inline des suppléments avec statut
- **Onglet "VEI"** : visible si `is_vei = True` — valeur vénale, coût réparation, décision client
- **Onglet "Documents"** : constat, photos, rapports
- **Onglet "Financier"** : franchise, montant approuvé, facturé, payé, encours
- **Boutons** : "Déclarer", "Demander expertise", "Expertise OK", "Approuver", "Supplément", "VEI", "Litige", "Annuler"
- **Bouton smart** : lien vers le devis et l'OR

### Liste sinistres
- Colonnes : référence, date sinistre, véhicule, client, assurance, type, montant approuvé, statut
- Filtres : par statut, par assurance, par type, par date, "En attente expertise", "Suppléments en cours", "VEI", "Litiges"

### Kanban sinistres
- Groupé par statut
- Carte : référence, véhicule (immat), client, montant, date

### Formulaire compagnie d'assurance
- En-tête : nom, code, contact Odoo
- Onglet "Barèmes" : taux horaires, coefficient pièces, matière peinture
- Onglet "Contacts" : experts, contacts déclaration
- Onglet "Conditions" : paiement, convention, notes
- Onglet "Statistiques" : nombre sinistres, encours, délai moyen

---

## Séquences

```xml
<record id="garage_seq_claim" model="ir.sequence">
    <field name="name">Sinistre garage</field>
    <field name="code">garage.insurance.claim</field>
    <field name="prefix">SIN/%(year)s/</field>
    <field name="padding">4</field>
</record>
```

---

## Cas de figure spéciaux — gestion technique

### Double sinistre
Un véhicule peut avoir 2 sinistres ouverts simultanément. Le `claim_id` sur le devis/OR doit permettre cette distinction. Chaque sinistre a son propre devis, son propre OR, sa propre facturation.

### Expertise dispensée
Certaines assurances (surtout pour petits montants < 1000€) dispensent d'expertise. Le sinistre passe directement de "Déclaré" à "Approuvé" avec `expertise_type = 'waived'`.

### Retard expert — impact planning
Quand un sinistre est bloqué en "En attente d'expertise" :
- Le véhicule occupe de la place dans l'atelier (impact planning)
- Un véhicule de courtoisie est potentiellement attribué (coût)
- Un cron job doit envoyer des relances automatiques après X jours

### VEI — Workflow complet
1. L'expert déclare VEI → `action_mark_vei()`
2. On informe le client → notification email
3. Le client décide :
   - `accept_loss` → le véhicule est récupéré par l'assurance, facturation des heures de démontage/expertise
   - `repair_own_cost` → on crée un OR normal, le client paie tout, pas de facturation assurance
   - `contest` → contre-expertise, le sinistre passe en "Litige"

### Grêle — Traitement en lot
- Type sinistre = 'hail'
- Souvent PDR (débosselage sans peinture) → sous-traitance
- Le garage peut recevoir 20 véhicules grêlés d'un coup → nécessité de planifier en batch
- Possibilité de créer des OR groupés avec un wizard dédié (futur)
