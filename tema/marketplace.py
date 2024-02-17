"""
This module represents the Marketplace.

Computer Systems Architecture Course
Assignment 1
March 2021
"""
from threading import Lock
import unittest
import logging
import logging.handlers
import time

class Marketplace:
    """
    Class that represents the Marketplace. It's the central part of the implementation.
    The producers and consumers use its methods concurrently.
    """
    def __init__(self, queue_size_per_producer):
        """
        Constructor

        :type queue_size_per_producer: Int
        :param queue_size_per_producer: the maximum size of a queue associated with each producer
        """
        # initializare logger
        self.logger = logging.getLogger('marketplace_log')
        self.logger.setLevel(logging.INFO)
        rotating_handler = logging.handlers.RotatingFileHandler('file.log',
                              maxBytes = 10000, backupCount = 10)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        formatter.converter = time.gmtime
        rotating_handler.setFormatter(formatter)
        self.logger.addHandler(rotating_handler)

        self.queue_size_per_producer = queue_size_per_producer
        # variabila ce genereaza id pentru producatori
        self.producer_id = 0
        self.producer_id_lock = Lock()
        # dictionar ce stocheaza produsele pentru fiecare producator
        self.products_per_producer = {}
        # variabila ce genereaza id pentru cosurile de cumparaturi
        self.cart_id = 0
        self.cart_id_lock = Lock()
        # dictionar ce stocheaza produsele din fiecare cos
        self.cart_list = {}
        self.remove_lock = Lock()
        # lista de produse disponibile in magazin
        self.market_products = []
        # dictionar ce stocheaza tot ce a fost produs pe parcursul executiei
        self.producer_stock = {}

    def register_producer(self):
        """
        Returns an id for the producer that calls this.
        """
        # inregistrare sincronizata a producatorilor
        with self.producer_id_lock:
            self.logger.info('Register new producer')
            self.producer_id += 1
            self.products_per_producer[self.producer_id] = []
            self.producer_stock[self.producer_id] = []
            self.logger.info('Producer registered with ID {%s}', self.producer_id)
        return self.producer_id


    def publish(self, producer_id, product):
        """
        Adds the product provided by the producer to the marketplace

        :type producer_id: String
        :param producer_id: producer id

        :type product: Product
        :param product: the Product that will be published in the Marketplace

        :returns True or False. If the caller receives False, it should wait and then try again.
        """
        self.logger.info('Producer {%s} is publishing new product {%s}', producer_id, product.name)
        size = len(self.products_per_producer[producer_id])
        # daca s-a atins capacitatea maxima de productie
        if size == self.queue_size_per_producer:
            self.logger.warning('Cannot publish right now. You need to wait')
            return False

        # adaug in listele aferente
        self.market_products.append(product)
        self.products_per_producer[producer_id].append(product)
        self.producer_stock[producer_id].append(product)

        self.logger.info('Product succesfully published by {%s}', producer_id)
        return True

    def new_cart(self):
        """
        Creates a new cart for the consumer

        :returns an int representing the cart_id
        """
        # generare sincronizata de cosuri de cumparaturi
        with self.cart_id_lock:
            self.logger.info('Generating new cart')
            self.cart_id += 1
            self.logger.info('New cart generated with ID {%s}', self.cart_id)
        self.cart_list[self.cart_id] = []
        return self.cart_id

    def add_to_cart(self, cart_id, product):
        """
        Adds a product to the given cart. The method returns

        :type cart_id: Int
        :param cart_id: id cart

        :type product: Product
        :param product: the product to add to cart

        :returns True or False. If the caller receives False, it should wait and then try again
        """
        self.logger.info('Add product {%s} to the cart with ID {%s}' ,product.name, cart_id)

        # 2 consumatori nu pot accesa acelasi produs
        with self.remove_lock:
            if product not in self.market_products:
                self.logger.warning('Please wait, product not available')
                return False
            self.market_products.remove(product)
            # caut elementul in dictionarul producatori-produse, apo il sterg
            for _, products in self.products_per_producer.items():
                for prod in products:
                    if prod == product:
                        products.remove(product)
                        break

        self.cart_list[cart_id].append(product)

        self.logger.info('Product succesfully added to cart with ID {%s}', cart_id)
        return True

    def remove_from_cart(self, cart_id, product):
        """
        Removes a product from cart.

        :type cart_id: Int
        :param cart_id: id cart

        :type product: Product
        :param product: the product to remove from cart
        """
        self.logger.info('Remove {%s} from cart with ID {%s}' ,product.name, cart_id)

        self.cart_list[cart_id].remove(product)
        # produsul devine disponibil
        self.market_products.append(product)
        # caut produsul in stoc, apoi il adaug in dictionarul producator-produse
        for key, value in self.producer_stock.items():
            if value == product:
                prod_id = key
                self.products_per_producer[prod_id].append(product)
                break
        self.logger.info('Product succesfully removed from cart')
        return True


    def place_order(self, cart_id):
        """
        Return a list with all the products in the cart.

        :type cart_id: Int
        :param cart_id: id cart
        """
        # caut cheia in dictionarul de cosuri, apoi ii intorc valoarea
        for key in self.cart_list:
            if key == cart_id:
                self.logger.info('Here are the products from the cart {%s}', cart_id)
                return self.cart_list[cart_id]
        self.logger.warning('Cart with ID {%s} not found', cart_id)
        return None

    class TestMarketplace(unittest.TestCase):
        def setUp(self):
            self.marketplace = Marketplace(2)
            self.prod1 = self.marketplace.register_producer()
            self.prod2 = self.marketplace.register_producer()
            self.tea1 = Tea(name="Green Tea", price=10, type="Green")
            self.tea2 = Tea(name="Green tea", price=20, type="Green")
            self.coffee = Coffee(name="Espresso", price=15, acidity="High", roast_level="Dark")
            self.cart1 = self.marketplace.new_cart()

        def test_register_producer(self):
            """ Unitary test for register_producer"""
            self.assertEqual(self.prod1, 1)
            self.assertEqual(len(self.marketplace.products_per_producer[self.prod1]), 0)
            self.assertEqual(len(self.marketplace.producer_stock[self.prod1]), 0)

            self.assertEqual(self.prod2, 2)
            self.assertEqual(len(self.marketplace.products_per_producer[self.prod2]), 0)
            self.assertEqual(len(self.marketplace.producer_stock[self.prod2]), 0)

        def test_publish(self):

            # Test when queue is not full
            res1 = self.marketplace.publish(self.prod1, self.tea1)
            self.assertTrue(res1)

            # Test when queue is full
            res2 = self.marketplace.publish(self.prod1, self.tea2)
            res3 = self.marketplace.publish(self.prod1, self.coffee)
            self.assertTrue(res2)
            self.assertFalse(res3)

        def test_newcart(self):
            self.assertEqual(self.cart1, 1)
            self.assertEqual(len(self.marketplace.cart_list[self.cart1]), 0)

            cart2 = self.marketplace.new_cart()
            self.assertEqual(cart2, 2)
            self.assertEqual(len(self.marketplace.cart_list[cart2]), 0)

        def test_add_to_cart(self):

            self.marketplace.publish(self.prod1, self.tea1)
            self.marketplace.publish(self.prod1, self.tea2)

            # Test when product is available
            res1 = self.marketplace.add_to_cart(self.cart1, self.tea1)
            self.assertTrue(res1)

            # Test when product is not available
            res2 = self.marketplace.add_to_cart(self.cart1, self.coffee)
            self.assertFalse(res2)

        def test_remove_from_cart(self):
            self.marketplace.publish(self.prod1, self.tea1)
            self.marketplace.publish(self.prod1, self.tea2)

            self.marketplace.add_to_cart(self.cart1, self.tea1)

            # Test when product is in cart
            res1 = self.marketplace.remove_from_cart(self.cart1, self.tea1)
            self.assertTrue(res1)

        def test_place_order(self):
            self.marketplace.publish(self.prod1, self.tea1)
            self.marketplace.publish(self.prod1, self.tea2)

            self.marketplace.add_to_cart(self.cart1, self.tea1)
            self.marketplace.add_to_cart(self.cart1, self.tea2)

            # Test when cart exists
            res1 = self.marketplace.place_order(self.cart1)
            self.assertCountEqual(res1, [self.tea1, self.tea2])

            # Test when cart does not exist
            res2 = self.marketplace.place_order(2)
            self.assertIsNone(res2)

        if __name__ == '__main__':
            unittest.main()
