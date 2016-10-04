# The COPYRIGHT file at the top level of this repository contains the full
# copyright notices and license terms.
try:
    from trytond.modules.analytic_purchase_warehouse.tests.test_analytic_purchase_warehouse import suite
except ImportError:
    from .test_analytic_purchase_warehouse import suite

__all__ = ['suite']
