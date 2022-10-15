from decimal import Decimal
from trytond.pool import PoolMeta, Pool
from trytond.model import dualmethod
from trytond.modules.product import round_price


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

    @dualmethod
    def set_moves(cls, productions):
        Move = Pool().get('stock.move')

        super(Production, cls).set_moves(productions)

        to_delete = []
        for production in productions:
            cost = Decimal(0)
            for move in production.inputs:
                if not move.product.phantom or not move.product.boms:
                    cost += (Decimal(str(move.internal_quantity)) *
                        move.product.cost_price)
                    continue
                to_delete.append(move)
                bom = move.product.boms[0].bom
                factor = bom.compute_factor(move.product, move.quantity,
                    move.uom)
                for input_ in bom.inputs:
                    quantity = input_.compute_quantity(factor)
                    product = input_.product
                    new_move = production._move(move.from_location,
                            move.to_location, move.company, product,
                            input_.uom, quantity)
                    if new_move:
                        new_move.production_input = production
                        new_move.planned_date = production.planned_date
                        # TODO: This should be outside the loop
                        new_move.save()
                        cost += Decimal(str(quantity)) * product.cost_price
            if to_delete:
                for output in production.outputs:
                    if move.product == production.product:
                        move.unit_price = round_price(
                            cost / Decimal(str(output.internal_quantity)))
                        move.save()
                # TODO: We still miss a way to invalidate the cache of self
                Move.delete(to_delete)
