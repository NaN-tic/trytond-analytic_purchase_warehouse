# The COPYRIGHT file at the top level of this repository contains the full
# copyright notices and license terms.
from trytond.pool import Pool, PoolMeta
from trytond.pyson import Eval
from trytond.transaction import Transaction

__all__ = ['Location', 'Purchase', 'PurchaseLine']


class Location(metaclass=PoolMeta):
    __name__ = 'stock.location'

    @classmethod
    def enabled_location_types(cls):
        # Show companies field (with analytic accounts configuration) in
        # warehouse locations
        enabled_types = super(Location, cls).enabled_location_types()
        if 'warehouse' not in enabled_types:
            enabled_types.append('warehouse')
        return enabled_types


class Purchase(metaclass=PoolMeta):
    __name__ = 'purchase.purchase'

    @classmethod
    def __setup__(cls):
        super(Purchase, cls).__setup__()
        cls.lines.context['warehouse'] = Eval('warehouse')


class PurchaseLine(metaclass=PoolMeta):
    __name__ = 'purchase.line'

    @classmethod
    def default_analytic_accounts(cls):
        pool = Pool()
        Location = pool.get('stock.location')
        Purchase = pool.get('purchase.purchase')

        entries = super(PurchaseLine, cls).default_analytic_accounts()

        company_id = Purchase.default_company()
        warehouse = Transaction().context.get('warehouse')
        if warehouse:
            root2account = {}
            for location_company in Location(warehouse).companies:
                if location_company.company.id != company_id:
                    continue
                for entry in location_company.analytic_accounts:
                    root2account[entry.root.id] = entry.account.id
            if root2account:
                for entry in entries:
                    if entry['root'] in root2account:
                        entry['account'] = root2account[entry['root']]
        return entries
