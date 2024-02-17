"""
This module represents the Consumer.

Computer Systems Architecture Course
Assignment 1
March 2021
"""

from threading import Thread
from time import sleep


class Consumer(Thread):
    """
    Class that represents a consumer.
    """

    def __init__(self, carts, marketplace, retry_wait_time, **kwargs):
        """
        Constructor.

        :type carts: List
        :param carts: a list of add and remove operations

        :type marketplace: Marketplace
        :param marketplace: a reference to the marketplace

        :type retry_wait_time: Time
        :param retry_wait_time: the number of seconds that a producer must wait
        until the Marketplace becomes available

        :type kwargs:
        :param kwargs: other arguments that are passed to the Thread's __init__()
        """

        Thread.__init__(self, **kwargs)
        self.carts = carts
        self.marketplace = marketplace
        self.retry_wait_time = retry_wait_time
        self.name = kwargs['name']

    def run(self):
        for cart in self.carts:
            cart_id = self.marketplace.new_cart()

            for operation in cart:
                quantity = operation["quantity"]
                op_type = operation["type"]
                product = operation["product"]

                # consumare produs
                while quantity:
                    if op_type == "add":
                        ret = self.marketplace.add_to_cart(cart_id, product)
                    elif op_type == "remove":
                        ret = self.marketplace.remove_from_cart(cart_id, product)

                    # verificare succes sau esec
                    if ret is True:
                        quantity -= 1
                    else:
                        sleep(self.retry_wait_time)

            # afisare produse
            items = self.marketplace.place_order(cart_id)
            for i in items:
                print(f"{self.name} bought {i}")
