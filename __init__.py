# The COPYRIGHT file at the top level of this repository contains the full
# copyright notices and license terms.
from trytond.pool import Pool
from .product import *
from .production import *

def register():
    Pool.register(
        Product,
        Production,
        module='production_phantom', type_='model')
