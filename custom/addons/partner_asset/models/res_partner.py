# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class ResPartner(models.Model):
    _name = 'res.partner'
    _inherit = 'res.partner'

    is_supplier = fields.Boolean(string='Est un Fournisseur', default=False,store=True)
    is_customer = fields.Boolean(string='Est un client',default=False,store=True)
    
    assignment_ids = fields.One2many('partner.asset.assignment', 'partner_id')
    asset_nbr = fields.Integer('Nombre de Borne', compute='_compute_asset_nbr', store=True)
    assignment_id = fields.Many2one('partner.asset.assignment', string="Borne")
    # model_asset = fields.Many2one(related='assignment_id.asset_model', store=True)
    asset_ids = fields.Many2many('partner.asset', compute="_compute_asset_ids",store=True)
    
    commission = fields.Float(string='Commission')

    contract_ids = fields.One2many('partner.contract', 'partner_id', string='Contracts')

    # inter_fullname = fields.Char(
    #     compute="_compute_name_inter",
    #     inverse="_inverse_name_inter_after_cleaning_whitespace",
    #     required=False,
    #     store=True,
    #     readonly=False,
    #     string="Nom complet Inter"
    # )
    lastname_inter = fields.Char("Nom Interlocuteur", index=True)
    firstname_inter = fields.Char("Prenom Interlocuteur", index=True)
    email_inter = fields.Char("Email Inter", index=True)

    # @api.model
    # def create(self, vals):
    #     """Add inverted names at creation if unavailable."""
    #     context = dict(self.env.context)
    #     inter_fullname = vals.get("inter_fullname", context.get("default_inter_fullname"))
    #
    #     if inter_fullname is not None:
    #         # Calculate the splitted fields
    #         inverted = self._get_inverse_name_inter(
    #             self._get_whitespace_cleaned_name_inter(inter_fullname),
    #             vals.get("is_company", self.default_get(["is_company"])["is_company"]),
    #         )
    #         for key, value in inverted.items():
    #             if not vals.get(key) or context.get("copy"):
    #                 vals[key] = value
    #
    #         # Remove the combined fields
    #         if "inter_fullname" in vals:
    #             del vals["inter_fullname"]
    #         if "default_inter_fullname" in context:
    #             del context["default_inter_fullname"]
    #     # pylint: disable=W8121
    #     return super(ResPartner, self.with_context(context)).create(vals)
    #
    #
    # @api.depends("lastname_inter", "firstname_inter")
    # def _compute_name_inter(self):
    #     for record in self:
    #         record.inter_fullname = record._get_computed_name(record.lastname_inter, record.firstname_inter)
    #
    # def _inverse_name_inter_after_cleaning_whitespace(self):
    #
    #     for record in self:
    #         # Remove unneeded whitespace
    #         clean = record._get_whitespace_cleaned_name_inter(record.firstname_inter)
    #         record.firstname_inter = clean
    #         record._inverse_name_inter()
    #
    # @api.model
    # def _get_whitespace_cleaned_name_inter(self, name, comma=False):
    #
    #     if isinstance(name, bytes):
    #         # With users coming from LDAP, name can be a byte encoded string.
    #         # This happens with FreeIPA for instance.
    #         name = name.decode("utf-8")
    #
    #     try:
    #         name = " ".join(name.split()) if name else name
    #     except UnicodeDecodeError:
    #         # with users coming from LDAP, name can be a str encoded as utf-8
    #         # this happens with ActiveDirectory for instance, and in that case
    #         # we get a UnicodeDecodeError during the automatic ASCII -> Unicode
    #         # conversion that Python does for us.
    #         # In that case we need to manually decode the string to get a
    #         # proper unicode string.
    #         name = " ".join(name.decode("utf-8").split()) if name else name
    #
    #     if comma:
    #         name = name.replace(" ,", ",")
    #         name = name.replace(", ", ",")
    #     return name
    #
    # @api.model
    # def _get_inverse_name_inter(self, name, is_company=False):
    #
    #     # Company name goes to the lastname
    #     if is_company or not name:
    #         parts = [name or False, False]
    #     # Guess name splitting
    #     else:
    #         order = self._get_names_order()
    #         # Remove redundant spaces
    #         name = self._get_whitespace_cleaned_name_inter(
    #             name, comma=(order == "last_first_comma")
    #         )
    #         parts = name.split("," if order == "last_first_comma" else " ", 1)
    #         if len(parts) > 1:
    #             if order == "first_last":
    #                 parts = [" ".join(parts[1:]), parts[0]]
    #             else:
    #                 parts = [parts[0], " ".join(parts[1:])]
    #         else:
    #             while len(parts) < 2:
    #                 parts.append(False)
    #     return {"lastname_inter": parts[0], "firstname_inter": parts[1]}
    #
    # def _inverse_name_inter(self):
    #
    #     for record in self:
    #         parts = record._get_inverse_name_inter(record.name_inter, record.is_company)
    #         record.lastname_inter = parts["lastname_inter"]
    #         record.firstname_inter = parts["firstname_inter"]

    def button_asset_upgrade(self):
        for rec in self:
            if rec.assignment_ids:
                rec.assignment_id = rec.assignment_ids[0]
                rec.commission = rec.active_contract_id.commission_percentage

    
    @api.depends('assignment_ids')
    def _compute_asset_ids(self):
        for rec in self:
            rec.asset_ids = rec.assignment_ids.asset_id
    
    @api.depends('assignment_ids')
    def _compute_asset_nbr(self):
        for rec in self:
            rec.asset_nbr = len(rec.assignment_ids)
    
    @api.onchange('assignment_ids')
    def _onchange_assgnement(self):
        for rec in self:
            if rec.assignment_ids:
                rec.assignment_id = rec.assignment_ids[0]
    
    def _actualise_assgnement(self):
        for rec in self:
            if rec.assignment_ids:
                rec.assignment_id = rec.assignment_ids[0]

            
    def action_view_asset_assignment(self):
        action = self.env['ir.actions.act_window']._for_xml_id('partner_asset.action_asset_config_assignment')
        action["domain"] = [("partner_id", "=", self.id)]
        action["context"] = {'default_partner_id': self.id}
        return action



class PartnerContract(models.Model):
    _name = 'partner.contract'
    _description = 'Contract for a customer'

    name = fields.Char(string='Intitulé du contrat', required=True)
    partner_id = fields.Many2one('res.partner', string='Client')
    commission_percentage = fields.Float(string='Commission')
    start_date = fields.Date(string='Date Début')
    end_date = fields.Date(string='Date Fin')
    payment_terms = fields.Selection([
        ('net', 'Net'),
        ('15_days', '15 Jours'),
        ('30_days', '30 Jours'),
        ('45_days', '45 Jours')
    ], string='Modalités de paiement')
    contract_type = fields.Selection([
        ('maintenance', 'Maintenance'),
        ('service', 'Service'),
        ('asset', 'Borne')
    ], string='Type Contract')

