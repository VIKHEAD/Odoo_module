# -*- coding: utf-8 -*-
# from odoo import http


# class VkpProjectExt(http.Controller):
#     @http.route('/vkp_project_ext/vkp_project_ext/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/vkp_project_ext/vkp_project_ext/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('vkp_project_ext.listing', {
#             'root': '/vkp_project_ext/vkp_project_ext',
#             'objects': http.request.env['vkp_project_ext.vkp_project_ext'].search([]),
#         })

#     @http.route('/vkp_project_ext/vkp_project_ext/objects/<model("vkp_project_ext.vkp_project_ext"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('vkp_project_ext.object', {
#             'object': obj
#         })
