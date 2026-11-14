import time
import random

class Order:
    def __init__(self,order_id, side, price,size):
        self.order_id = order_id     #UNIQUE ORDER ID
        self.side = side             #BUY OR SELL
        self.price = float(price)         #THE PRICE IT WILL BE TRADED AT
        self.size = float(size)             #THE LOT SIZE OF OUR TRADE
        self.timestamp = time.time() #THE EXACT MILLISECOND THEY ARRIVE
        self.status = "RESTING"
    
    #TELLING PYTHON HOW TO PRINT THE ORDER IF WE ASK IT TO
    def __repr__ (self):
        return f"[{self.order_id}] {self.side} {self.size} @ {self.price:.2f}"

class OrderBook:
    """ We create the order book that will hold the different orders"""
    #------------------------------ ADDING ORDERS------------------------------------

    def __init__(self, fee_bps=10,tick_size=0.01):
        self.bids = []
        self.asks = []
        self.order_counter = 1
        self.fee_bps = fee_bps
        self.tick_size = tick_size #Represents the minimum price increase

    def add_order (self, side, price,size):
        """ Creating a function to add in new limit orders into the order book"""
        #0. We start by making sure the price is a multiple of the tick size. If not, we round it to the nearest tick size.
        price = round(price / self.tick_size) * self.tick_size

        #1. Creating a unique order ID of the type ORD-001, ORD-002, ORD-003, etc
        order_id = f"ORD-{self.order_counter:03d}"

        #We want the numerical part to have at least 3 digits, when the order counter is 1 or 33, 
        #the program adds 0s infront of them to make them 3 digits long. 
        # This is done using the :03d format specifier in the f-string.

        self.order_counter +=1 #Increment the counter for the next order

        #2. Creating the actual orders using our function from the Order class
        new_order = Order(order_id, side, price,size)

        #3. Classifying the order in the correct list/ side
        if side == "BUY":
            self.bids.append(new_order)
        elif side == "SELL":
            self.asks.append(new_order)
        else:
            raise ValueError("Side must be either 'BUY' or 'SELL'")

        #4.Sorting the bok automatically
        self.sort_book()
        #print(f"Added order: {new_order}")

    #------------------------------------SORTING THE ORDER BOOK------------------------------------
    def sort_book(self):
        """Sorting the order book so that the best prices are always at the top of the book"""
        #Bids are sorted from highest to lowesr (-x.price -> price in descending order)
        #If 2 prices are at the same price, the one that arrived first (oldest timestamp) is placed higher
        self.bids.sort(key=lambda x: (-x.price, x.timestamp))

        #Asks are sorted from lowest to highest (x.price -> price in ascending order)
        #If 2 prices are at the same price, the one that arrived first (oldest timestamp) is placed higher
        self.asks.sort(key=lambda x: (x.price, x.timestamp))

    #------------------------------------- AGGREGATE DEPTH ----------------------------------
    def get_level_2_data(self):
        """Aggregates level 3 orders into level 2 price levels."""
        
        #1. Aggregate asks
        #Using a dictionary to sum up sizes at the same price
        ask_depth = {}
        for order in self.asks:
            price = order.price
            if price not in ask_depth:
                ask_depth[price] = 0
            ask_depth[price] += order.size
            
        #2. Aggregate bids
        bid_depth = {}
        for order in self.bids:
            price = order.price
            if price not in bid_depth:
                bid_depth[price] = 0
            bid_depth[price] += order.size

        #3. Return the data
        return {
            "asks": ask_depth,
            "bids": bid_depth
        }

    def execute_market_order(self, side, size):
        """ This sweeps the book. if you BUY, it hits the ASKS. If you SELL, it hits the BIDS."""

        remaining_size = size
        total_cost = 0
        filled_size = 0
        first_fill_price = None 

        book_to_sweep = self.asks if side == "BUY" else self.bids

        while remaining_size > 0 and len(book_to_sweep) > 0:
            best_level = book_to_sweep[0]  # Get the best price level (first order in the sorted list)
            
            if first_fill_price is None:
                first_fill_price = best_level.price  # Record the price of the first fill
            
            fill_amount = min(remaining_size, best_level.size)  # Determine how much we can fill at this level

            #Math
            total_cost += (fill_amount * best_level.price)
            filled_size += fill_amount
            remaining_size -= fill_amount
            best_level.size -= fill_amount  # Reduce the size of the order at this level

            if best_level.size == 0:
                book_to_sweep.pop(0)  # Remove the order if it's fully filled

        # Transaction fee calculation
        #The fee is a percentage of the total value of the trade, calculated in basis points (bps). 1 bps = 0.01%
        fee_rate = self.fee_bps / 10000.0 # Convert bps to a decimal
        transaction_fee = total_cost * fee_rate  # Calculate the fee based on the total cost of the trade

        #Calculate VWAP (Volume Weighted Average Price) (Total cost/ Total filled)
        vwap = total_cost / filled_size if filled_size > 0 else 0

        #Calculate slippage (difference between the first fill price and the VWAP)
        slippage = abs(vwap - first_fill_price) if first_fill_price is not None else 0
        return {
            "side": side,
            "filled_size": filled_size,
            "remaining_size": remaining_size,
            "vwap": vwap,
            "slippage": slippage,
            "transaction_fee": transaction_fee
        }

    def cancel_random_order(self, cancel_probability=0.1):
        """ We simulate market makers pulling their liquidity. It removes a percentage of
        random orders from both sides of the book"""
        
        # We use [:] to create a copy of the list so we can safely remove items while looping
        for order in self.bids[:]:
            if random.random() < cancel_probability:
                self.bids.remove(order)
                
        for order in self.asks[:]:
            if random.random() < cancel_probability:
                self.asks.remove(order)
