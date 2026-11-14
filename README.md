# LiquidityX: Market Microstructure & Execution Simulator

## Overview
LiquidityX is a Limit Order Book (LOB) simulator designed to model market microstructure and predict execution costs. We developed a Python-based matching engine, an Agent-Based Model (ABM) for order flow generation, and a Machine Learning pipeline to predict slippage prior to trade execution.

## Core Components
*   **`engine.py`:** A matching engine enforcing strict FIFO (Price-Time Priority), tick-size constraints, and transaction fees (BPS).
*   **`data_generator.py`:** An Agent-Based Model simulating heterogeneous market participants (Retail vs. Institutional) using a Poisson arrival process.
*   **`interactive_live.py`:** A CLI terminal for real-time order execution. It utilizes the trained ML model to provide pre-trade slippage estimates.
*   **`research/`:** Jupyter notebooks containing data exploration and the Machine Learning pipeline.

## Machine Learning Findings
We trained a Random Forest Regressor on 100,000 simulated ticks to predict slippage. 

Rather than relying solely on raw order size, we engineered a **Consumption Ratio** feature (Order Size / Available Book Depth). The model's Feature Importance analysis confirms that the Consumption Ratio (~53%) is the primary driver of price impact, heavily outweighing absolute order size and the current bid-ask spread.

## Current Status (V1)
*   Functional matching engine and live terminal.
*   Baseline Random Forest model (R² = 0.38). *Note: We consider this a robust baseline for stochastic financial data, as higher scores often indicate data leakage.*

## Roadmap (V2)
- [ ] Transition ML pipeline to XGBoost and introduce Book Imbalance features.
- [ ] Develop an automated backtester to calculate strategy PnL.
- [ ] Publish a quantitative research paper detailing the methodology.

## How to Run
1. Install dependencies: `pip install -r requirements.txt`
2. Generate synthetic market data: `python src/data_generator.py`
3. Launch the interactive terminal: `python src/interactive_live.py`