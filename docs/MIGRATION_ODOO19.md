# Migration Garage Pro — Odoo 17 → Odoo 19

## Objectif

Migrer le module `garage_pro` de Odoo 17 vers Odoo 19. Le saut couvre 2 versions majeures (17→18→19). Ce document liste TOUS les changements à appliquer au code, dans l'ordre.

## Prérequis serveur

Avant de toucher au code, vérifier et mettre à jour le serveur :

```bash
# Vérifier Python (doit être >= 3.11)
python3 --version

# Si Python < 3.11 :
apt-get install -y python3.12 python3.12-venv python3.12-dev
update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.12 1

# Vérifier PostgreSQL (16 recommandé)
psql --version

# Vérifier Node.js (doit être >= 18)
node --version
```

## Étape 1 — Créer une branche de migration

```bash
cd /opt/garage_pro
git checkout -b migration/odoo19
```

## Étape 2 — Installer Odoo 19 CE

```bash
# Renommer l'ancien
mv /opt/odoo17 /opt/odoo17_backup

# Cloner Odoo 19
git clone --depth 1 --branch 19.0 https://github.com/odoo/odoo.git /opt/odoo19

# Installer les dépendances Python
cd /opt/odoo19
pip3 install -r requirements.txt --break-system-packages

# Mettre à jour la config
sed -i 's|/opt/odoo17|/opt/odoo19|g' /etc/odoo/odoo.conf

# Mettre à jour l'alias odoo
cat > /usr/local/bin/odoo << 'EOF'
#!/bin/bash
exec python3 /opt/odoo19/odoo-bin -c /etc/odoo/odoo.conf "$@"
EOF
chmod +x /usr/local/bin/odoo
```

## Étape 3 — Recréer la DB de test sur Odoo 19

```bash
# Supprimer l'ancienne DB de test
sudo -u postgres dropdb garage_test 2>/dev/null
sudo -u postgres createdb -O odoo garage_test

# Initialiser avec Odoo 19
odoo -d garage_test -i base,contacts,fleet,stock,purchase,account,calendar,mail,portal,web,hr --stop-after-init --without-demo=all
```

## Étape 4 — Corrections du code

Appliquer dans l'ordre. Pour chaque correction, chercher dans TOUS les fichiers du module.

---

### 4.1 — `__manifest__.py` : version

```bash
grep -n "version" garage_pro/__manifest__.py
```

Changer :
```python
# AVANT
'version': '17.0.1.0.0',

# APRÈS
'version': '19.0.1.0.0',
```

---

### 4.2 — XML : `attrs=` (supprimé depuis v18)

```bash
grep -rn "attrs=" garage_pro/views/*.xml
```

Pour chaque occurrence, remplacer :

```xml
<!-- AVANT -->
<field name="claim_id" attrs="{'invisible': [('is_insurance_claim', '=', False)]}"/>
<field name="franchise_amount" attrs="{'invisible': [('franchise_type', '=', 'none')], 'required': [('franchise_type', '!=', 'none')]}"/>
<button name="action_approve" attrs="{'invisible': [('state', '!=', 'sent')]}"/>

<!-- APRÈS -->
<field name="claim_id" invisible="not is_insurance_claim"/>
<field name="franchise_amount" invisible="franchise_type == 'none'" required="franchise_type != 'none'"/>
<button name="action_approve" invisible="state != 'sent'"/>
```

Règles de conversion `attrs` → attributs directs :
- `'invisible': [('field', '=', value)]` → `invisible="field == value"`
- `'invisible': [('field', '!=', value)]` → `invisible="field != value"`
- `'invisible': [('field', '=', False)]` → `invisible="not field"`
- `'invisible': [('field', '=', True)]` → `invisible="field"`
- `'invisible': [('field', 'in', [a, b])]` → `invisible="field in ('a', 'b')"`
- `'required': [('field', '=', value)]` → `required="field == value"`
- `'readonly': [('field', '=', value)]` → `readonly="field == value"`
- Conditions multiples (AND) : `[('a', '=', 1), ('b', '=', 2)]` → `invisible="a == 1 and b == 2"`
- Conditions OR (dans attrs c'était via `'|'`) → `invisible="a == 1 or b == 2"`

---

### 4.3 — XML : `<kanban-box>` → `<card>` (v19)

```bash
grep -rn "kanban-box" garage_pro/views/*.xml
```

Remplacement global :
```bash
sed -i 's/t-name="kanban-box"/t-name="card"/g' garage_pro/views/*.xml
```

Dans les vues kanban v19, le `<div class="oe_kanban_global_click">` n'est plus nécessaire dans `<card>`. Le `<card>` est lui-même cliquable. Simplifier :

```xml
<!-- AVANT (v17) -->
<templates>
    <t t-name="kanban-box">
        <div t-attf-class="oe_kanban_global_click">
            <strong><field name="name"/></strong>
            <field name="state"/>
        </div>
    </t>
</templates>

<!-- APRÈS (v19) -->
<templates>
    <t t-name="card">
        <strong><field name="name"/></strong>
        <field name="state"/>
    </t>
</templates>
```

---

### 4.4 — Sécurité : `ir.module.category` → `res.groups.privilege` (v19)

Fichier : `garage_pro/security/garage_pro_groups.xml`

```xml
<!-- AVANT (v17) -->
<record id="module_category_garage" model="ir.module.category">
    <field name="name">Garage</field>
    <field name="sequence">50</field>
</record>

<record id="group_receptionist" model="res.groups">
    <field name="name">Réceptionniste</field>
    <field name="category_id" ref="module_category_garage"/>
</record>

<!-- APRÈS (v19) -->
<record id="group_privilege_garage" model="res.groups.privilege">
    <field name="name">Garage</field>
</record>

<record id="group_receptionist" model="res.groups">
    <field name="name">Réceptionniste</field>
    <field name="privilege_id" ref="group_privilege_garage"/>
</record>
```

Appliquer ce changement à TOUS les groupes dans le fichier :
- `group_receptionist`
- `group_technician`
- `group_workshop_chief`
- `group_accountant`
- `group_manager`

Tous doivent utiliser `privilege_id` au lieu de `category_id`.

---

### 4.5 — Python : `self._context` → `self.env.context`

```bash
grep -rn "self\._context" garage_pro/models/*.py
```

Remplacement :
```bash
sed -i 's/self\._context/self.env.context/g' garage_pro/models/*.py
```

---

### 4.6 — Python : import `registry`

```bash
grep -rn "from odoo import.*registry" garage_pro/models/*.py garage_pro/controllers/*.py
```

Si trouvé :
```python
# AVANT
from odoo import registry

# APRÈS
from odoo.modules.registry import Registry
```

---

### 4.7 — Python : import `xlsxwriter`

```bash
grep -rn "from odoo.tools.misc import xlsxwriter" garage_pro/
```

Si trouvé :
```python
# AVANT
from odoo.tools.misc import xlsxwriter

# APRÈS
import xlsxwriter
```

---

### 4.8 — Python : API deprecated

Chercher et corriger :

```bash
grep -rn "@api.returns\|_company_default_get\|@api.one\|@api.multi" garage_pro/models/*.py
```

- `@api.returns` → supprimer la ligne
- `@api.one` → supprimer la ligne (n'existe plus depuis v13)
- `@api.multi` → supprimer la ligne (c'est le comportement par défaut)
- `_company_default_get()` → remplacer par `lambda self: self.env.company`

---

### 4.9 — Python : champs renommés dans les modules natifs

Chercher toutes les références aux champs qui ont changé :

```bash
# tax_id → tax_ids (sur les lignes de vente/achat)
grep -rn "tax_id" garage_pro/models/*.py | grep -v "tax_ids"

# product_uom → product_uom_id
grep -rn "product_uom[^_]" garage_pro/models/*.py

# Vérifier le champ VIN dans fleet.vehicle v19
grep -rn "vin_sn\|\.vin" garage_pro/models/*.py
```

Pour le VIN, vérifier comment il s'appelle en v19 :
```bash
grep -n "vin" /opt/odoo19/addons/fleet/models/fleet_vehicle.py
```

Si le champ a changé de nom, mettre à jour TOUTES les références dans garage_pro.

---

### 4.10 — Python : contrôleurs JSON-RPC (v19)

```bash
grep -rn "type='json'\|type=\"json\"" garage_pro/controllers/*.py 2>/dev/null
```

En v19, les routes `type='json'` utilisent JSON-RPC. Vérifier que les contrôleurs (portail, API CarVertical) sont compatibles.

---

### 4.11 — SCSS : Dart Sass strict (v18+)

```bash
find garage_pro/static -name "*.scss" 2>/dev/null
```

Si des fichiers SCSS existent :
- Remplacer `@import` par `@use`
- Remplacer `$var / 3` par `math.div($var, 3)`
- Vérifier qu'aucun `/` n'est utilisé pour la division

---

### 4.12 — JS/OWL : assets et CSP

```bash
find garage_pro/static/src -name "*.js" -o -name "*.xml" 2>/dev/null
```

Si du JS custom existe :
- Vérifier qu'il est déclaré dans `__manifest__.py` → `assets` → `web.assets_backend`
- Pas de `<script>` inline dans les QWeb templates
- Pas de chargement depuis un CDN externe (tout doit être vendorisé dans `static/lib/`)

---

### 4.13 — Vérifier les héritages des modules natifs

Comparer les modèles hérités pour détecter les conflits :

```bash
# fleet.vehicle — notre héritage principal
diff <(grep "fields\.\|def " /opt/odoo19/addons/fleet/models/fleet_vehicle.py) \
     <(grep "fields\.\|def " garage_pro/models/vehicle.py)

# account.move — notre extension facturation
grep "fields\.\|def " /opt/odoo19/addons/account/models/account_move.py | head -50

# stock.move — notre extension pièces
grep "fields\.\|def " /opt/odoo19/addons/stock/models/stock_move.py | head -30

# res.partner — notre extension client
grep "fields\.\|def " /opt/odoo19/addons/base/models/res_partner.py | head -50
```

Si un champ qu'on ajoute existe maintenant nativement en v19, SUPPRIMER notre champ custom et utiliser le natif. Ne pas créer de doublons.

---

## Étape 5 — Tester l'installation

```bash
cd /opt/garage_pro
odoo -d garage_test -u garage_pro --stop-after-init 2>&1 | tail -50
```

Si ça échoue :
1. Lire le traceback ENTIER
2. Identifier le fichier et la ligne
3. Corriger
4. Relancer
5. Répéter jusqu'à succès

Erreurs fréquentes à ce stade :
- `KeyError` ou `AttributeError` sur un champ → champ renommé, voir §4.9
- `Invalid XML` → attrs mal converti, voir §4.2
- `Unknown model` → un modèle natif a changé de nom
- `Cannot find column` → champ supprimé dans le module natif hérité

---

## Étape 6 — Lancer les tests

```bash
odoo -d garage_test --test-enable --test-tags garage_pro --stop-after-init 2>&1 | grep -E "FAIL|ERROR|OK|test_"
```

Pour chaque test qui échoue :
1. Lire le message d'erreur
2. Vérifier si c'est le code ou le test qui est faux
3. Corriger le code en priorité (sauf si le test est objectivement faux à cause d'un changement d'API v19)

---

## Étape 7 — Vérifications manuelles

Tester chaque vue dans le navigateur (http://IP:8069) :

```
□ Menu Garage visible
□ Véhicules : form, tree, kanban → pas d'erreur
□ Clients : form avec onglet Garage → pas d'erreur
□ Sinistres : form, kanban par statut → workflow complet
□ Devis : création, envoi, acceptation, conversion en OR
□ OR : workflow complet, planning, facturation
□ Facturation : split assurance/franchise
□ Portail client : accessible, données visibles
□ Rapports PDF : devis, OR, facture → génération OK
```

---

## Étape 8 — Commit et push

```bash
cd /opt/garage_pro
git add -A
git commit -m "🚀 Migration Odoo 17 → 19 complète"
git push origin migration/odoo19
```

---

## Étape 9 — Mettre à jour PROGRESS.md

Ajouter dans PROGRESS.md :

```markdown
### 🔧 Migration Odoo 19
- [ ] Prérequis serveur OK (Python 3.11+, PG 16)
- [ ] Odoo 19 installé dans /opt/odoo19
- [ ] DB de test recréée sur Odoo 19
- [ ] __manifest__.py → 19.0.1.0.0
- [ ] attrs= supprimés des XML
- [ ] kanban-box → card
- [ ] ir.module.category → res.groups.privilege
- [ ] self._context → self.env.context
- [ ] Imports deprecated corrigés
- [ ] Champs renommés vérifiés (VIN, tax_id, product_uom)
- [ ] Héritages natifs vérifiés (fleet, account, stock, partner)
- [ ] JS/SCSS compatibles
- [ ] Module s'installe sur Odoo 19
- [ ] Tests passent
- [ ] Vérification manuelle OK
- [ ] Commit + push sur branche migration/odoo19
```

---

## Checklist finale

```
□ __manifest__.py → version 19.0.1.0.0
□ Tous les attrs= convertis en attributs directs
□ Tous les kanban-box remplacés par card
□ ir.module.category → res.groups.privilege
□ self._context → self.env.context
□ Imports deprecated corrigés (registry, xlsxwriter, api.returns)
□ Champs renommés corrigés (tax_id→tax_ids, product_uom→product_uom_id, vin_sn→?)
□ JS/SCSS compatibles CSP + dart-sass
□ Héritages vérifiés (fleet.vehicle, account.move, stock.move, res.partner)
□ Module s'installe
□ Tests passent
□ Vues fonctionnent dans le navigateur
```
