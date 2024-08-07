import datetime
import unittest
from decimal import Decimal

from dateutil.relativedelta import relativedelta

from proteus import Model
from trytond.modules.company.tests.tools import create_company
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

        # Imports
        today = datetime.date.today()
        today - relativedelta(days=1)

        # Install production Module
        activate_modules('production_phantom')

        # Create company
        _ = create_company()

        # Create product
        ProductUom = Model.get('product.uom')
        unit, = ProductUom.find([('name', '=', 'Unit')])
        ProductTemplate = Model.get('product.template')
        Product = Model.get('product.product')
        product = Product()
        template = ProductTemplate()
        template.producible = True
        template.name = 'product'
        template.default_uom = unit
        template.type = 'goods'
        template.list_price = Decimal(30)
        template.save()
        product.template = template
        product.cost_price = Decimal(20)
        product.save()

        # Create Components
        component1 = Product()
        template1 = ProductTemplate()
        template1.name = 'component 1'
        template1.default_uom = unit
        template1.producible = True
        template1.type = 'goods'
        template1.list_price = Decimal(5)
        template1.save()
        component1.template = template1
        component1.cost_price = Decimal(1)
        component1.save()
        component2 = Product()
        template2 = ProductTemplate()
        template2.producible = True
        template2.name = 'component 2'
        template2.default_uom = unit
        template2.type = 'goods'
        template2.list_price = Decimal(7)
        template2.save()
        component2.template = template2
        component2.cost_price = Decimal(5)
        component2.save()

        # Create Sub Components
        subcomponent1 = Product()
        template1 = ProductTemplate()
        template1.name = 'subcomponent 1'
        template1.default_uom = unit
        template1.type = 'goods'
        template1.list_price = Decimal(5)
        template1.save()
        subcomponent1.template = template1
        subcomponent1.save()
        meter, = ProductUom.find([('symbol', '=', 'm')])
        centimeter, = ProductUom.find([('symbol', '=', 'cm')])
        subcomponent2 = Product()
        template2 = ProductTemplate()
        template2.name = 'subcomponent 2'
        template2.default_uom = meter
        template2.type = 'goods'
        template2.list_price = Decimal(7)
        template2.save()
        subcomponent2.template = template2
        subcomponent2.cost_price = Decimal(5)
        subcomponent2.save()

        # Create Bill of Material of Component 1
        BOM = Model.get('production.bom')
        BOMInput = Model.get('production.bom.input')
        BOMOutput = Model.get('production.bom.output')
        component1_bom = BOM(name='product')
        input1 = BOMInput()
        component1_bom.inputs.append(input1)
        input1.product = subcomponent1
        input1.quantity = 5
        input2 = BOMInput()
        component1_bom.inputs.append(input2)
        input2.product = subcomponent2
        input2.quantity = 150
        input2.uom = centimeter
        output = BOMOutput()
        component1_bom.outputs.append(output)
        output.product = component1
        output.quantity = 1
        component1_bom.save()
        ProductBom = Model.get('product.product-production.bom')
        component1.boms.append(ProductBom(bom=component1_bom))
        component1.phantom = True
        component1.save()

        # Create Bill of Material
        BOM = Model.get('production.bom')
        BOMInput = Model.get('production.bom.input')
        BOMOutput = Model.get('production.bom.output')
        bom = BOM(name='product')
        input1 = BOMInput()
        bom.inputs.append(input1)
        input1.product = component1
        input1.quantity = 5
        input2 = BOMInput()
        bom.inputs.append(input2)
        input2.product = component2
        input2.quantity = 2
        output = BOMOutput()
        bom.outputs.append(output)
        output.product = product
        output.quantity = 1
        bom.save()
        ProductBom = Model.get('product.product-production.bom')
        product.boms.append(ProductBom(bom=bom))
        product.save()

        # Make a production
        Production = Model.get('production')
        production = Production()
        production.product = product
        production.bom = bom
        production.quantity = 2
        self.assertEqual(
            sorted([i.quantity
                    for i in production.inputs]), [4.0, 50.0, 1500.0])
        output, = production.outputs
        self.assertEqual(output.quantity, 2)
        production.save()
        self.assertEqual(production.cost, Decimal('95.0000'))
