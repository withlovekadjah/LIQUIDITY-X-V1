import random
import time
import pandas as pd
from engine import OrderBook
#We import the class OrderBook from the engine.py file 

def generate_market_flowbook (book, num_ticks= 1000, arrival_rate = 0.8, market_order_prob = 0.4):
    """ Simulates an Agent-Based  Model (ABM) of a stock market.
    It generates a continuous flow of retail and institutional orders."""

    print(f"------ Starting Market Flowbook Simulation for {num_ticks} ticks ------")

    #We store the results here to later export them to a CSV file for our machine learning model
    trade_log = [] 

    for tick in range(num_ticks):
        #1. ARRIVAL PROBABILITY (USING POISSON PROCESS)

        # There is an 80% chance an order arrives at this specific tick
        #20% chance that no order arrives at this tick
        if random.random() > arrival_rate:
            continue

        #2. CALCULATE MIDPRICE
        if len(book.bids) > 0 and len(book.asks) > 0:
            mid_price = (book.bids[0].price + book.asks[0].price) / 2
        else:
            mid_price = 150 #Default mid price if the order book is empty

        side = random.choice(["BUY", "SELL"])

        #3. WHO IS TRADING (Retail vs Institutional)
        #We estimated retail traders participation in daily transactions at 25% chance . So we have a 25% chance it is a retail trader and 75% chance the trade is institutional

        is_retail = random.random() < 0.25 #returns true or false

        #4. ORDER TYPE (Market vs Limit)
        #Retail traders prefer Market orders, while institutional traders prefer Limit orders.
        #We estimated that retail traders use market orders 70% of the time, while institutional traders use market orders 30% of the time.
        # This are just arbitrary values

        is_market_order = random.random() < (0.7 if is_retail else 0.3) #returns true or false

        if  is_retail: #if is_retail is true

     #---------------------------- RETAIL TRADER-----------------------------------------------
           
            if is_market_order:
                size = random.randint(1,20)

                current_bid_depth = sum([o.size for o in book.bids])
                current_ask_depth = sum([o.size for o in book.asks])

                  # Calculate pre-trade spread
                current_spread = book.asks[0].price - book.bids[0].price if (book.bids and book.asks) else 0.0

                result = book.execute_market_order(side, size)

                #If the trade filled, we log it

                if result["filled_size"] > 0:
                    
                    trade_log.append({
                        "tick" : tick,
                        "agent": "Retail",
                        "type" : "Market",
                        "side" : side,
                        "requested_size" : size,
                        "book_bid_depth": current_bid_depth, 
                        "book_ask_depth": current_ask_depth, 
                        "filled_size" : result["filled_size"],
                        "vwap" : result["vwap"],
                        "slippage" : result["slippage"],
                        "spread": current_spread})
                
            else:
                    #Retail limit order
                    size = random.randint(10,50)
                    distance = random.uniform(0.5, 2.0)
                    price = mid_price - distance if side =="BUY" else mid_price + distance

                    book.add_order(side,price,size)
        else:
        #----------------------------------INSTITUTIONAL TRADER---------------------------------------
           
            if is_market_order:
                #We are dealing with large lot sizes
                size =  random.randint(1000,5000)

                current_bid_depth = sum([o.size for o in book.bids])
                current_ask_depth = sum([o.size for o in book.asks])

                # Calculate pre-trade spread
                current_spread = book.asks[0].price - book.bids[0].price if (book.bids and book.asks) else 0.0

                result = book.execute_market_order (side, size)
                
                
                if result["filled_size"] > 0:

                    trade_log.append({
                        "tick" : tick,
                        "agent": "Institution",
                        "type" : "Market",
                        "side" : side,
                        "requested_size" : size,
                        "book_bid_depth": current_bid_depth, 
                        "book_ask_depth": current_ask_depth, 
                        "filled_size" : result["filled_size"],
                        "vwap" : result["vwap"],
                        "slippage" : result["slippage"],
                        "spread": current_spread})

                #If the whale whipped out the book, we must replenish it so the simulation doesn't break
                if len(book.bids) == 0 or len(book.asks) == 0 :
                    for _ in range(10):
                        book.add_order("BUY", mid_price - 1.0, 1000)
                        book.add_order("SELL", mid_price + 1.0, 1000)

            else:
                #institutional limit order
                size = random.randint(500,2000)
                distance = random.uniform(1.0,3.0)
                price = mid_price - distance if side == "BUY" else mid_price + distance
                
                book.add_order(side, price, size)
        
        #5. MARKET MAKERS CANCEL ORDERS
        #We chose 10% as the chance an order is pulled from the book to simulate a dynamic market
        book.cancel_random_order(cancel_probability=0.10)

    print(f"--- Simulation Complete. {len(trade_log)} Market Orders Executed. ---")
    return trade_log

## ==========================================
# RUNNING THE GENERATOR
# ==========================================
if __name__ == "__main__":
    my_book = OrderBook(fee_bps=10, tick_size=0.01)
    
    print("Seeding initial book...")
    for i in range(1, 6):
        my_book.add_order("BUY", 150.0 - (i * 0.50), 1000)
        my_book.add_order("SELL", 150.0 + (i * 0.50), 1000)
        
    # Run for 5,000 ticks to get lots of data!
    results = generate_market_flowbook(my_book, num_ticks=100000, arrival_rate=0.80)
    
    # Save to CSV using Pandas
    df = pd.DataFrame(results)
    df.to_csv("slippage_data.csv", index=False)
    
    print(f"\n Data successfully saved to slippage_data.csv!")
    print(f"Total market orders logged: {len(df)}")
    print(df.tail(5))




  


