from decimal import Decimal
from itertools import izip
from trytond.pool import PoolMeta, Pool

__all__ = ['Production']


class Production:
    __name__ = 'production'
    __metaclass__ = PoolMeta

    def explode_bom(self):
        Product = Pool().get('product.product')
        Uom = Pool().get('product.uom')
        Location = Pool().get('stock.location')

        changes = super(Production, self).explode_bom()
        if not changes.get('inputs', {}).get('add'):
            return changes

        additions = changes['inputs']['add']
        cost = changes.get('cost', Decimal(0))

        new_additions = []
        products = Product.browse([x[1]['product'] for x in additions])
        for addition, product in izip(additions, products):
            if not product.phantom:
                new_additions.append(addition)
                continue
            if not product.boms:
                continue
            bom = product.boms[0].bom
            factor = bom.compute_factor(product, addition[1]['quantity'],
                Uom(addition[1]['uom']))

            from_location = Location(addition[1]['from_location'])
            to_location = Location(addition[1]['to_location'])
            uom_quantity = Uom.compute_qty(Uom(addition[1]['uom']),
                    addition[1]['quantity'], product.default_uom)
            cost -= (Decimal(str(uom_quantity)) * product.cost_price)
            for input_ in bom.inputs:
                quantity = input_.compute_quantity(factor)
                values = self._explode_move_values(from_location,
                    to_location,self.company, input_, quantity)
                if values:
                    new_additions.append((addition[0], values))
                    uom_quantity = Uom.compute_qty(input_.uom, quantity,
                        input_.product.default_uom)
                    cost += (Decimal(str(uom_quantity)) *
                        input_.product.cost_price)
        changes['inputs']['add'] = new_additions
        changes['cost'] = cost
        return changes

    def set_moves(self):
        Move = Pool().get('stock.move')
        Product = Pool().get('product.product')
        Template = Pool().get('product.template')

        super(Production, self).set_moves()
        to_delete = []
        cost = Decimal(0)
        for move in self.inputs:
            if not move.product.phantom or not move.product.boms:
                cost += (Decimal(str(move.internal_quantity)) *
                    move.product.cost_price)
                continue
            to_delete.append(move)
            bom = move.product.boms[0].bom
            factor = bom.compute_factor(move.product, move.quantity, move.uom)
            for input_ in bom.inputs:
                quantity = input_.compute_quantity(factor)
                product = input_.product
                new_move = self._move(move.from_location, move.to_location,
                    move.company, product, input_.uom, quantity)
                if new_move:
                    new_move.production_input = self
                    # TODO: This should be outside the loop
                    new_move.save()
                    cost += Decimal(str(quantity)) * product.cost_price
        if hasattr(Product, 'cost_price'):
            digits = Product.cost_price.digits
        else:
            digits = Template.cost_price.digits
        if to_delete:
            for output in self.outputs:
                if move.product == self.product:
                    move.unit_price = Decimal(
                        cost / Decimal(str(output.internal_quantity))
                        ).quantize(Decimal(str(10 ** -digits[1])))
                    move.save()
            # TODO: We still miss a way to invalidate the cache of self
            Move.delete(to_delete)
