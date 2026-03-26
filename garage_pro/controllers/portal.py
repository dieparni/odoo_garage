"""Portail client Garage Pro — consultation OR, devis, documents."""

from odoo import http
from odoo.http import request
from odoo.addons.portal.controllers.portal import CustomerPortal, pager as portal_pager


class GaragePortal(CustomerPortal):
    """Extension du portail client pour Garage Pro."""

    def _prepare_home_portal_values(self, counters):
        values = super()._prepare_home_portal_values(counters)
        partner = request.env.user.partner_id

        if 'repair_order_count' in counters:
            values['repair_order_count'] = (
                request.env['garage.repair.order'].search_count(
                    self._get_repair_order_domain(partner)
                )
            )
        if 'quotation_count' in counters:
            values['quotation_count'] = (
                request.env['garage.quotation'].search_count(
                    self._get_quotation_domain(partner)
                )
            )
        return values

    def _get_repair_order_domain(self, partner):
        return [
            ('customer_id', '=', partner.id),
            ('state', 'not in', ['cancelled']),
        ]

    def _get_quotation_domain(self, partner):
        return [
            ('customer_id', '=', partner.id),
            ('state', 'not in', ['cancelled']),
        ]

    # ------------------------------------------------------------------
    # Ordres de réparation
    # ------------------------------------------------------------------

    @http.route(
        ['/my/repair-orders', '/my/repair-orders/page/<int:page>'],
        type='http', auth='user', website=True,
    )
    def portal_my_repair_orders(self, page=1, sortby=None, **kw):
        """Liste des OR du client connecté."""
        partner = request.env.user.partner_id
        RepairOrder = request.env['garage.repair.order']
        domain = self._get_repair_order_domain(partner)

        sortings = {
            'date': {'label': 'Date', 'order': 'create_date desc'},
            'name': {'label': 'Référence', 'order': 'name'},
            'state': {'label': 'Statut', 'order': 'state'},
        }
        sortby = sortby if sortby in sortings else 'date'

        order_count = RepairOrder.search_count(domain)
        pager = portal_pager(
            url='/my/repair-orders',
            total=order_count,
            page=page,
            step=10,
            url_args={'sortby': sortby},
        )
        orders = RepairOrder.search(
            domain,
            order=sortings[sortby]['order'],
            limit=10,
            offset=pager['offset'],
        )

        values = self._prepare_portal_layout_values()
        values.update({
            'orders': orders,
            'page_name': 'repair_orders',
            'pager': pager,
            'sortby': sortby,
            'sortings': sortings,
            'default_url': '/my/repair-orders',
        })
        return request.render(
            'garage_pro.portal_my_repair_orders', values
        )

    @http.route(
        '/my/repair-orders/<int:order_id>',
        type='http', auth='user', website=True,
    )
    def portal_my_repair_order_detail(self, order_id, **kw):
        """Détail d'un OR."""
        partner = request.env.user.partner_id
        order = request.env['garage.repair.order'].sudo().browse(order_id)
        if not order.exists() or order.customer_id.id != partner.id:
            return request.redirect('/my/repair-orders')

        values = self._prepare_portal_layout_values()
        values.update({
            'order': order,
            'page_name': 'repair_order_detail',
        })
        return request.render(
            'garage_pro.portal_repair_order_detail', values
        )

    # ------------------------------------------------------------------
    # Devis
    # ------------------------------------------------------------------

    @http.route(
        ['/my/garage-quotations', '/my/garage-quotations/page/<int:page>'],
        type='http', auth='user', website=True,
    )
    def portal_my_quotations(self, page=1, sortby=None, **kw):
        """Liste des devis du client connecté."""
        partner = request.env.user.partner_id
        Quotation = request.env['garage.quotation']
        domain = self._get_quotation_domain(partner)

        sortings = {
            'date': {'label': 'Date', 'order': 'create_date desc'},
            'name': {'label': 'Référence', 'order': 'name'},
            'state': {'label': 'Statut', 'order': 'state'},
        }
        sortby = sortby if sortby in sortings else 'date'

        quotation_count = Quotation.search_count(domain)
        pager = portal_pager(
            url='/my/garage-quotations',
            total=quotation_count,
            page=page,
            step=10,
            url_args={'sortby': sortby},
        )
        quotations = Quotation.search(
            domain,
            order=sortings[sortby]['order'],
            limit=10,
            offset=pager['offset'],
        )

        values = self._prepare_portal_layout_values()
        values.update({
            'quotations': quotations,
            'page_name': 'garage_quotations',
            'pager': pager,
            'sortby': sortby,
            'sortings': sortings,
            'default_url': '/my/garage-quotations',
        })
        return request.render(
            'garage_pro.portal_my_quotations', values
        )

    @http.route(
        '/my/garage-quotations/<int:quotation_id>',
        type='http', auth='user', website=True,
    )
    def portal_my_quotation_detail(self, quotation_id, **kw):
        """Détail d'un devis."""
        partner = request.env.user.partner_id
        quotation = request.env['garage.quotation'].sudo().browse(
            quotation_id
        )
        if not quotation.exists() or quotation.customer_id.id != partner.id:
            return request.redirect('/my/garage-quotations')

        values = self._prepare_portal_layout_values()
        values.update({
            'quotation': quotation,
            'page_name': 'garage_quotation_detail',
        })
        return request.render(
            'garage_pro.portal_quotation_detail', values
        )

    @http.route(
        '/my/garage-quotations/<int:quotation_id>/accept',
        type='http', auth='user', website=True,
    )
    def portal_quotation_accept(self, quotation_id, **kw):
        """Accepter un devis depuis le portail."""
        partner = request.env.user.partner_id
        quotation = request.env['garage.quotation'].sudo().browse(
            quotation_id
        )
        if (quotation.exists()
                and quotation.customer_id.id == partner.id
                and quotation.state == 'sent'):
            quotation.action_approve()
        return request.redirect(
            '/my/garage-quotations/%d' % quotation_id
        )

    @http.route(
        '/my/garage-quotations/<int:quotation_id>/refuse',
        type='http', auth='user', website=True,
    )
    def portal_quotation_refuse(self, quotation_id, **kw):
        """Refuser un devis depuis le portail."""
        partner = request.env.user.partner_id
        quotation = request.env['garage.quotation'].sudo().browse(
            quotation_id
        )
        if (quotation.exists()
                and quotation.customer_id.id == partner.id
                and quotation.state == 'sent'):
            quotation.action_refuse()
        return request.redirect(
            '/my/garage-quotations/%d' % quotation_id
        )
