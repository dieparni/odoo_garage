# Manifest & Sécurité

## __manifest__.py

```python
{
    'name': 'Garage Pro',
    'version': '17.0.1.0.0',
    'category': 'Services/Garage',
    'summary': 'Gestion complète atelier carrosserie, peinture et mécanique',
    'description': """
        Module de gestion garage automobile :
        - Fiches véhicules étendues (VIN, peinture, historique)
        - Gestion sinistres et assurances
        - Devis et ordres de réparation multi-métier
        - Planning atelier et techniciens
        - Sous-traitance et véhicules de courtoisie
        - Facturation multi-payeur (client, assurance, franchise)
        - Contrôle qualité et documentation photo
        - Reporting et tableaux de bord
        - Intégration CarVertical (phase 2)
    """,
    'author': 'Volpe Services',
    'website': 'https://volpe-services.com',
    'license': 'LGPL-3',
    'depends': [
        'base',
        'contacts',
        'fleet',
        'stock',
        'purchase',
        'account',
        'calendar',
        'mail',
        'portal',
        'web',
        'hr',
    ],
    'data': [
        # Sécurité (TOUJOURS en premier)
        'security/garage_pro_groups.xml',
        'security/ir.model.access.csv',
        'security/garage_pro_rules.xml',

        # Données
        'data/garage_sequences.xml',
        'data/garage_product_categories.xml',
        'data/garage_mail_templates.xml',
        'data/garage_cron.xml',
        'data/garage_config_defaults.xml',

        # Vues
        'views/vehicle_views.xml',
        'views/customer_views.xml',
        'views/insurance_views.xml',
        'views/claim_views.xml',
        'views/quotation_views.xml',
        'views/repair_order_views.xml',
        'views/bodywork_views.xml',
        'views/paint_views.xml',
        'views/mechanic_views.xml',
        'views/planning_views.xml',
        'views/parts_views.xml',
        'views/subcontract_views.xml',
        'views/courtesy_views.xml',
        'views/documentation_views.xml',
        'views/quality_views.xml',
        'views/billing_views.xml',
        'views/reporting_views.xml',
        'views/config_views.xml',
        'views/menus.xml',

        # Wizards
        'wizard/quotation_to_repair_wizard.xml',
        'wizard/claim_supplement_wizard.xml',
        'wizard/courtesy_return_wizard.xml',
        'wizard/carvertical_lookup_wizard.xml',

        # Rapports
        'report/quotation_report.xml',
        'report/repair_order_report.xml',
        'report/invoice_garage_report.xml',
        'report/quality_checklist_report.xml',
    ],
    'demo': [
        'demo/garage_demo_data.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'garage_pro/static/src/css/garage.css',
            'garage_pro/static/src/js/**/*',
            'garage_pro/static/src/xml/**/*',
        ],
    },
    'installable': True,
    'application': True,
    'auto_install': False,
}
```

---

## Groupes de sécurité — `security/garage_pro_groups.xml`

```xml
<?xml version="1.0" encoding="utf-8"?>
<odoo>
    <record id="module_category_garage" model="ir.module.category">
        <field name="name">Garage</field>
        <field name="sequence">50</field>
    </record>

    <record id="group_receptionist" model="res.groups">
        <field name="name">Réceptionniste</field>
        <field name="category_id" ref="module_category_garage"/>
        <field name="comment">Peut créer des devis, accueillir les clients, consulter le planning.</field>
    </record>

    <record id="group_technician" model="res.groups">
        <field name="name">Technicien</field>
        <field name="category_id" ref="module_category_garage"/>
        <field name="implied_ids" eval="[(4, ref('group_receptionist'))]"/>
        <field name="comment">Peut pointer son temps, consommer des pièces, mettre à jour l'avancement.</field>
    </record>

    <record id="group_workshop_chief" model="res.groups">
        <field name="name">Chef d'atelier</field>
        <field name="category_id" ref="module_category_garage"/>
        <field name="implied_ids" eval="[(4, ref('group_technician'))]"/>
        <field name="comment">Peut gérer le planning, valider le QC, affecter les techniciens.</field>
    </record>

    <record id="group_accountant" model="res.groups">
        <field name="name">Comptable garage</field>
        <field name="category_id" ref="module_category_garage"/>
        <field name="implied_ids" eval="[(4, ref('group_receptionist'))]"/>
        <field name="comment">Peut créer des factures, gérer les paiements, suivre les créances assurance.</field>
    </record>

    <record id="group_manager" model="res.groups">
        <field name="name">Gérant</field>
        <field name="category_id" ref="module_category_garage"/>
        <field name="implied_ids" eval="[(4, ref('group_workshop_chief')), (4, ref('group_accountant'))]"/>
        <field name="comment">Accès complet : configuration, reporting, tous les modules.</field>
    </record>
</odoo>
```

---

## Droits d'accès — `security/ir.model.access.csv`

```csv
id,name,model_id:id,group_id:id,perm_read,perm_write,perm_create,perm_unlink
access_vehicle_receptionist,fleet.vehicle receptionist,fleet.model_fleet_vehicle,garage_pro.group_receptionist,1,1,1,0
access_vehicle_manager,fleet.vehicle manager,fleet.model_fleet_vehicle,garage_pro.group_manager,1,1,1,1
access_insurance_company_receptionist,garage.insurance.company receptionist,model_garage_insurance_company,garage_pro.group_receptionist,1,0,0,0
access_insurance_company_manager,garage.insurance.company manager,model_garage_insurance_company,garage_pro.group_manager,1,1,1,1
access_claim_receptionist,garage.insurance.claim receptionist,model_garage_insurance_claim,garage_pro.group_receptionist,1,1,1,0
access_claim_manager,garage.insurance.claim manager,model_garage_insurance_claim,garage_pro.group_manager,1,1,1,1
access_quotation_receptionist,garage.quotation receptionist,model_garage_quotation,garage_pro.group_receptionist,1,1,1,0
access_quotation_manager,garage.quotation manager,model_garage_quotation,garage_pro.group_manager,1,1,1,1
access_repair_order_receptionist,garage.repair.order receptionist,model_garage_repair_order,garage_pro.group_receptionist,1,1,0,0
access_repair_order_technician,garage.repair.order technician,model_garage_repair_order,garage_pro.group_technician,1,1,0,0
access_repair_order_chief,garage.repair.order chief,model_garage_repair_order,garage_pro.group_workshop_chief,1,1,1,0
access_repair_order_manager,garage.repair.order manager,model_garage_repair_order,garage_pro.group_manager,1,1,1,1
access_ro_line_technician,garage.repair.order.line technician,model_garage_repair_order_line,garage_pro.group_technician,1,1,0,0
access_ro_line_chief,garage.repair.order.line chief,model_garage_repair_order_line,garage_pro.group_workshop_chief,1,1,1,0
access_ro_line_manager,garage.repair.order.line manager,model_garage_repair_order_line,garage_pro.group_manager,1,1,1,1
access_planning_technician,garage.planning.slot technician,model_garage_planning_slot,garage_pro.group_technician,1,0,0,0
access_planning_chief,garage.planning.slot chief,model_garage_planning_slot,garage_pro.group_workshop_chief,1,1,1,1
access_quality_chief,garage.quality.checklist chief,model_garage_quality_checklist,garage_pro.group_workshop_chief,1,1,1,0
access_quality_manager,garage.quality.checklist manager,model_garage_quality_checklist,garage_pro.group_manager,1,1,1,1
access_documentation_technician,garage.documentation technician,model_garage_documentation,garage_pro.group_technician,1,1,1,0
access_courtesy_receptionist,garage.courtesy.vehicle receptionist,model_garage_courtesy_vehicle,garage_pro.group_receptionist,1,1,0,0
access_courtesy_manager,garage.courtesy.vehicle manager,model_garage_courtesy_vehicle,garage_pro.group_manager,1,1,1,1
access_subcontract_chief,garage.subcontract.order chief,model_garage_subcontract_order,garage_pro.group_workshop_chief,1,1,1,0
access_bodywork_technician,garage.bodywork.operation technician,model_garage_bodywork_operation,garage_pro.group_technician,1,1,0,0
access_paint_technician,garage.paint.operation technician,model_garage_paint_operation,garage_pro.group_technician,1,1,0,0
access_mechanic_technician,garage.mechanic.operation technician,model_garage_mechanic_operation,garage_pro.group_technician,1,1,0,0
access_report_revenue_manager,garage.report.revenue manager,model_garage_report_revenue,garage_pro.group_manager,1,0,0,0
access_report_revenue_accountant,garage.report.revenue accountant,model_garage_report_revenue,garage_pro.group_accountant,1,0,0,0
```

---

## Menu principal — `views/menus.xml`

```xml
<?xml version="1.0" encoding="utf-8"?>
<odoo>
    <!-- Menu racine -->
    <menuitem id="garage_menu_root"
        name="Garage"
        sequence="30"
        web_icon="garage_pro,static/description/icon.png"/>

    <!-- Niveau 1 -->
    <menuitem id="garage_menu_reception" name="Réception" parent="garage_menu_root" sequence="10"/>
    <menuitem id="garage_menu_workshop" name="Atelier" parent="garage_menu_root" sequence="20"/>
    <menuitem id="garage_menu_insurance" name="Assurances" parent="garage_menu_root" sequence="30"/>
    <menuitem id="garage_menu_billing" name="Facturation" parent="garage_menu_root" sequence="40"/>
    <menuitem id="garage_menu_stock" name="Pièces & Stock" parent="garage_menu_root" sequence="50"/>
    <menuitem id="garage_menu_reporting" name="Reporting" parent="garage_menu_root" sequence="60"/>
    <menuitem id="garage_menu_config" name="Configuration" parent="garage_menu_root" sequence="90"/>

    <!-- Réception -->
    <menuitem id="garage_menu_vehicles" name="Véhicules" parent="garage_menu_reception" action="garage_vehicle_action" sequence="10"/>
    <menuitem id="garage_menu_customers" name="Clients" parent="garage_menu_reception" action="garage_customer_action" sequence="20"/>
    <menuitem id="garage_menu_quotations" name="Devis" parent="garage_menu_reception" action="garage_quotation_action" sequence="30"/>
    <menuitem id="garage_menu_courtesy" name="Véh. courtoisie" parent="garage_menu_reception" action="garage_courtesy_action" sequence="40"/>

    <!-- Atelier -->
    <menuitem id="garage_menu_repair_orders" name="Ordres de réparation" parent="garage_menu_workshop" action="garage_repair_order_action" sequence="10"/>
    <menuitem id="garage_menu_planning" name="Planning" parent="garage_menu_workshop" action="garage_planning_action" sequence="20"/>
    <menuitem id="garage_menu_quality" name="Contrôle qualité" parent="garage_menu_workshop" action="garage_quality_action" sequence="30"/>
    <menuitem id="garage_menu_subcontract" name="Sous-traitance" parent="garage_menu_workshop" action="garage_subcontract_action" sequence="40"/>

    <!-- Assurances -->
    <menuitem id="garage_menu_claims" name="Sinistres" parent="garage_menu_insurance" action="garage_claim_action" sequence="10"/>
    <menuitem id="garage_menu_insurance_companies" name="Compagnies" parent="garage_menu_insurance" action="garage_insurance_company_action" sequence="20"/>

    <!-- Facturation -->
    <menuitem id="garage_menu_invoices" name="Factures garage" parent="garage_menu_billing" action="garage_invoice_action" sequence="10"/>

    <!-- Configuration -->
    <menuitem id="garage_menu_config_posts" name="Postes de travail" parent="garage_menu_config" action="garage_post_action" sequence="10"/>
    <menuitem id="garage_menu_config_paint_systems" name="Systèmes peinture" parent="garage_menu_config" action="garage_paint_system_action" sequence="20"/>
    <menuitem id="garage_menu_config_settings" name="Paramètres" parent="garage_menu_config" action="garage_config_settings_action" sequence="90"/>
</odoo>
```

---

## Paramètres par défaut — `data/garage_config_defaults.xml`

```xml
<?xml version="1.0" encoding="utf-8"?>
<odoo>
    <data noupdate="1">
        <record id="garage_default_hourly_body" model="ir.config_parameter">
            <field name="key">garage_pro.default_hourly_rate_body</field>
            <field name="value">55.0</field>
        </record>
        <record id="garage_default_hourly_paint" model="ir.config_parameter">
            <field name="key">garage_pro.default_hourly_rate_paint</field>
            <field name="value">55.0</field>
        </record>
        <record id="garage_default_hourly_mech" model="ir.config_parameter">
            <field name="key">garage_pro.default_hourly_rate_mech</field>
            <field name="value">60.0</field>
        </record>
        <record id="garage_default_vat_rate" model="ir.config_parameter">
            <field name="key">garage_pro.default_vat_rate</field>
            <field name="value">21.0</field>
        </record>
        <record id="garage_default_quotation_validity_days" model="ir.config_parameter">
            <field name="key">garage_pro.quotation_validity_days</field>
            <field name="value">30</field>
        </record>
    </data>
</odoo>
```
