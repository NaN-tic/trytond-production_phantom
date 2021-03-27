# The COPYRIGHT file at the top level of this repository contains the full
# copyright notices and license terms.
from trytond.pool import Pool
from . import product
from . import production

def register():
    Pool.register(
        product.Product,
        production.Production,
        module='production_phantom', type_='model')
