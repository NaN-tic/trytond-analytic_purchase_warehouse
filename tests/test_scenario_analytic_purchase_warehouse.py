import unittest
from decimal import Decimal

from proteus import Model
from trytond.modules.account.tests.tools import create_chart, get_accounts
from trytond.modules.account_invoice.tests.tools import create_payment_term
from trytond.modules.company.tests.tools import create_company, get_company
from trytond.tests.test_tryton import drop_db
from trytond.tests.tools import activate_modules


class Test(unittest.TestCase):

    def setUp(self):
        drop_db()
        super().setUp()

    def tearDown(self):
        drop_db()
        super().tearDown()

    def test(self):

        # Activate analytic_purchase_warehouse
        config = activate_modules('analytic_purchase_warehouse')

        # Create company
        _ = create_company()
        company = get_company()

        # Reload the context
        User = Model.get('res.user')
        Group = Model.get('res.group')
        config._context = User.get_preferences(True, config.context)

        # Create purchase user
        purchase_user = User()
        purchase_user.name = 'Purchase'
        purchase_user.login = 'purchase'
        purchase_group, = Group.find([('name', '=', 'Purchase')])
        purchase_user.groups.append(purchase_group)
        purchase_user.save()

        # Create chart of accounts
        _ = create_chart(company)
        accounts = get_accounts(company)
        revenue = accounts['revenue']
        expense = accounts['expense']

        # Create an analytic hierarchy
        AnalyticAccount = Model.get('analytic_account.account')
        root1 = AnalyticAccount(name='Root 1', type='root')
        root1.save()
        analytic_account = AnalyticAccount(name='Account 1.1',
                                           root=root1,
                                           parent=root1)
        analytic_account.save()
        analytic_account = AnalyticAccount(name='Account 1.2',
                                           root=root1,
                                           parent=root1)
        analytic_account.save()
        root1.reload()

        # Create a second analytic hierarchy
        root2 = AnalyticAccount(name='Root 1', type='root')
        root2.save()
        analytic_account = AnalyticAccount(name='Account 2.1',
                                           root=root2,
                                           parent=root2)
        analytic_account.save()
        analytic_account = AnalyticAccount(name='Account 2.2',
                                           root=root2,
                                           parent=root2)
        analytic_account.save()
        root2.reload()

        # Create parties
        Party = Model.get('party.party')
        supplier = Party(name='Supplier')
        supplier.save()

        # Create account category
        ProductCategory = Model.get('product.category')
        account_category = ProductCategory(name="Account Category")
        account_category.accounting = True
        account_category.account_expense = expense
        account_category.account_revenue = revenue
        account_category.save()

        # Create product
        ProductUom = Model.get('product.uom')
        unit, = ProductUom.find([('name', '=', 'Unit')])
        ProductTemplate = Model.get('product.template')
        template = ProductTemplate()
        template.name = 'product'
        template.account_category = account_category
        template.default_uom = unit
        template.type = 'goods'
        template.purchasable = True
        template.list_price = Decimal('10')
        template.cost_price_method = 'fixed'
        template.save()
        product, = template.products

        # Create payment term
        payment_term = create_payment_term()
        payment_term.save()

        # Create a warehouse with assigned analytic accounts
        Location = Model.get('stock.location')
        input_loc2 = Location(name='Input 2')
        input_loc2.save()
        output_loc2 = Location(name='Output 2')
        output_loc2.save()
        storage_loc2 = Location(name='Storage 2')
        storage_loc2.save()
        warehouse2, = Location.create([{
            'name': 'Warehouse 2',
            'type': 'warehouse',
            'input_location': input_loc2.id,
            'output_location': output_loc2.id,
            'storage_location': storage_loc2.id,
        }], config.context)
        warehouse2 = Location(warehouse2)
        company_location = warehouse2.companies.new()
        self.assertEqual(len(company_location.analytic_accounts), 2)

        for entry in company_location.analytic_accounts:
            if entry.root.id == root1.id:
                entry.account = root1.childs[0]
            else:
                entry.account = root2.childs[-1]

        warehouse2.save()
        self.assertEqual(
            warehouse2.companies[0].analytic_accounts[0].account.name,
            'Account 1.1')
        self.assertEqual(
            warehouse2.companies[0].analytic_accounts[1].account.name,
            'Account 2.2')

        # Prepare purchase to warehouse without analytic accounts
        config.user = purchase_user.id
        Purchase = Model.get('purchase.purchase')
        warehouse1, = Location.find([('code', '=', 'WH')])
        purchase = Purchase()
        purchase.party = supplier
        purchase.warehouse = warehouse1
        purchase.payment_term = payment_term
        purchase.invoice_method = 'order'
        purchase_line = purchase.lines.new()
        purchase_line.product = product
        purchase_line.quantity = 2.0
        purchase_line.unit_price = product.cost_price
        purchase.save()
        self.assertEqual(len(purchase.lines[0].analytic_accounts), 2)
        self.assertEqual(
            all(e.account == None for e in purchase.lines[0].analytic_accounts),
            True)

        # Prepare purchase to warehouse with analytic accounts
        purchase = Purchase()
        purchase.party = supplier
        purchase.warehouse = warehouse2
        purchase.payment_term = payment_term
        purchase.invoice_method = 'order'
        purchase_line = purchase.lines.new()
        purchase_line.product = product
        purchase_line.quantity = 3.0
        purchase_line.unit_price = product.cost_price
        purchase.save()
        self.assertEqual(purchase.lines[0].analytic_accounts[0].account.name,
                         'Account 1.1')
        self.assertEqual(purchase.lines[0].analytic_accounts[1].account.name,
                         'Account 2.2')

        # Prepare purchase without warehouse when add first line and set warehouse with
        # analytic account before add second line
        purchase = Purchase()
        purchase.party = supplier
        purchase.warehouse
        purchase.payment_term = payment_term
        purchase.invoice_method = 'order'
        purchase_line = purchase.lines.new()
        purchase_line.product = product
        purchase_line.quantity = 4.0
        purchase_line.unit_price = product.cost_price
        purchase.warehouse = warehouse2
        purchase_line = purchase.lines.new()
        purchase_line.product = product
        purchase_line.quantity = 5.0
        purchase_line.unit_price = product.cost_price
        purchase.save()
        self.assertEqual(len(purchase.lines[0].analytic_accounts), 2)
        self.assertEqual(
            all(e.account == None for e in purchase.lines[0].analytic_accounts),
            True)
        self.assertEqual(purchase.lines[1].analytic_accounts[0].account.name,
                         'Account 1.1')
        self.assertEqual(purchase.lines[1].analytic_accounts[1].account.name,
                         'Account 2.2')
