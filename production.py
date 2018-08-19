from decimal import Decimal

from trytond.pool import PoolMeta, Pool

__all__ = ['Production']


class Production(metaclass=PoolMeta):
    __name__ = 'production'

    def explode_bom(self):
        super(Production, self).explode_bom()
        if self.inputs:

            inputs = self.inputs

            new_inputs = []
            products = [i.product for i in inputs]
            for _input, product in zip(inputs, products):
                if not product.phantom:
                    new_inputs.append(_input)
                    continue
                if not product.boms:
                    continue
                bom = product.boms[0].bom
                factor = bom.compute_factor(product, _input.quantity,
                    _input.uom)

                from_location = _input.from_location
                to_location = _input.to_location
                for input_ in bom.inputs:
                    quantity = input_.compute_quantity(factor)
                    move = self._explode_move_values(from_location,
                        to_location, self.company, input_, quantity)
                    if move:
                        new_inputs.append(move)
            self.inputs = new_inputs

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
                    new_move.planned_date = self.planned_date
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
