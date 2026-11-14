import time
import random
import threading
import pandas as pd
import joblib
import os
from collections import deque
from engine import OrderBook

model = joblib.load("slippage_model.pkl")

recent_trades = deque(maxlen=6)
running = True
market_lock = threading.Lock()
pause_market = threading.Event()
pause_market.set()

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def background_market_loop(book):
    global running
    
    while running:
        time.sleep(1.5)
        
        if not pause_market.is_set():
            continue
            
        with market_lock:
            side = random.choice(["BUY", "SELL"])
            is_whale = random.random() < 0.20
            size = random.randint(500, 2000) if is_whale else random.randint(1, 50)
            
            if random.random() < 0.6:
                result = book.execute_market_order(side, size)
                if result['filled_size'] > 0:
                    agent = "WHALE" if is_whale else "Retail"
                    recent_trades.append(f"{agent}: {side} {size} @ {result['vwap']:.2f}")
            else:
                mid = (book.bids[0].price + book.asks[0].price) / 2 if (book.bids and book.asks) else 150.0
                price = mid - 0.5 if side == "BUY" else mid + 0.5
                book.add_order(side, price, size)
                    
            book.cancel_random_order(cancel_probability=0.10)

            if len(book.bids) == 0 or len(book.asks) == 0:
                mid_price = 150.0
                if book.bids: mid_price = book.bids[0].price - 1.0
                elif book.asks: mid_price = book.asks[0].price + 1.0
                
                for i in range(1, 6):
                    book.add_order("BUY", mid_price - (i * 0.50), 1000)
                    book.add_order("SELL", mid_price + (i * 0.50), 1000)
                recent_trades.append("SYSTEM: Market Makers re-seeded the book")

def print_dashboard(book, message=""):
    clear_screen()
    print("="*60)
    print("      LIQUIDITYX LIVE TERMINAL (XGBoost AI Engine)")
    print("="*60)
    
    with market_lock:
        print("--- ASKS (SELLERS) ---")
        for order in reversed(book.asks[:4]):
            print(f"   {order.price:>7.2f} | Size: {int(order.size)}")
        print("-" * 60)
        print("--- BIDS (BUYERS) ---")
        for order in book.bids[:4]:
            print(f"   {order.price:>7.2f} | Size: {int(order.size)}")
        
        print("\n--- LIVE TAPE (Recent Activity) ---")
        if not recent_trades:
            print("   Waiting for market activity...")
        for trade in list(recent_trades)[::-1]:
            print(f"   {trade}")
    print("="*60)
    
    if message:
        print(f"\n{message}\n")

def get_safe_input(prompt, input_type=float):
    while True:
        try:
            return input_type(input(prompt))
        except ValueError:
            print(f"Invalid input. Please enter a valid {input_type.__name__}.")

def run_terminal():
    global running
    book = OrderBook(fee_bps=10, tick_size=0.01)
    
    for i in range(1, 6):
        book.add_order("BUY", 150.0 - (i * 0.50), 1000)
        book.add_order("SELL", 150.0 + (i * 0.50), 1000)

    market_thread = threading.Thread(target=background_market_loop, args=(book,), daemon=True)
    market_thread.start()

    while True:
        print_dashboard(book)
        print("\n1. MARKET ORDER")
        print("2. LIMIT ORDER")
        print("3. WAIT / REFRESH")
        print("4. EXIT")
        
        choice = input("\nSelect option [1/2/3/4]: ").strip()
        
        if choice == "4":
            running = False
            print("Shutting down...")
            break
            
        elif choice == "3":
            continue
            
        elif choice in ["1", "2"]:
            side = input("Side [BUY/SELL]: ").strip().upper()
            if side not in ["BUY", "SELL"]:
                print("Invalid side.")
                time.sleep(1)
                continue
                
            size = get_safe_input("Size: ", float)
            
            if choice == "1":
                # Pause the background market
                pause_market.clear() 
                
                # Calculate AI features safely
                with market_lock:
                    bid_depth = sum([o.size for o in book.bids])
                    ask_depth = sum([o.size for o in book.asks])
                    spread = book.asks[0].price - book.bids[0].price if (book.bids and book.asks) else 0.0
                    depth_to_consume = ask_depth if side == "BUY" else bid_depth
                    
                    features = pd.DataFrame([{
                        'requested_size': size, 'side_encoded': 1 if side == "BUY" else 0,
                        'book_bid_depth': bid_depth, 'book_ask_depth': ask_depth,
                        'spread': spread, 'consumption_ratio': size / (depth_to_consume + 1e-9),
                        'book_imbalance': bid_depth / (bid_depth + ask_depth + 1e-9)
                    }])
                    raw_prediction = model.predict(features)[0]
                    pred_slip = max(0.0, raw_prediction) 
                    
                print(f"\n[AI] Estimated Slippage: ${pred_slip:.4f}")
                confirm = input("Confirm Execution? [Y/N]: ").strip().upper()
                
                # Execute and prepare message
                if confirm == "Y":
                    with market_lock:
                        result = book.execute_market_order(side, size)
                        if result['filled_size'] > 0:
                            recent_trades.append(f"USER: {side} {size} @ {result['vwap']:.2f} (Slip: {result['slippage']:.2f})")
                            msg = f">>> TRADE EXECUTED: Filled {result['filled_size']} units at VWAP ${result['vwap']:.2f}"
                        else:
                            msg = "\n>>> Order failed: No liquidity available."
                else:
                    msg = "\n>>> Order cancelled by user."
                
                # Draw the screen AFTER the lock is released to show the impact immediately
                print_dashboard(book, msg)
                
                # Resume market
                pause_market.set()
                input("\nPress Enter to resume live market...")
                
            elif choice == "2":
                pause_market.clear()
                price = get_safe_input("Limit Price: ", float)
                with market_lock:
                    book.add_order(side, price, size)
                    recent_trades.append(f"USER: Placed {side} LIMIT {size} @ {price:.2f}")
                    msg = f"\n>>> Limit Order placed at {price:.2f}. Waiting to be filled."
                
                print_dashboard(book, msg)
                pause_market.set()
                input("\nPress Enter to resume live market...")

if __name__ == "__main__":
    run_terminal()