from trytond.model import fields
from trytond.pool import PoolMeta
from trytond.pyson import Bool, Eval

__all__ = ['Product']

class Product:
    __name__ = 'product.product'
    __metaclass__ = PoolMeta
    # TODO: Phantom should only be available with products whose UOM is 'unit'
    phantom = fields.Boolean('Phantom', states={
            'invisible': ~Bool(Eval('boms', [])),
            })
