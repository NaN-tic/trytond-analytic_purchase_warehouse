# The COPYRIGHT file at the top level of this repository contains the full
# copyright notices and license terms.
from trytond.pool import Pool
from . import purchase

def register():
    Pool.register(
        purchase.Location,
        purchase.Purchase,
        purchase.PurchaseLine,
        module='analytic_purchase_warehouse', type_='model')
