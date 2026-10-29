# StockYield

A dark finance-style desktop dashboard for the Design and Analysis of Algorithms project. It finds the best historical buy/sell pair using a divide-and-conquer maximum-subarray algorithm.

## Run on Windows

```powershell
python -m pip install -r requirements.txt
python -m unittest -v test_algorithm.py
python app.py
```

## Features

- CustomTkinter dashboard and interactive Matplotlib price chart\n- Hover over chart points to inspect day/price; click a point to select it\n- Mouse-wheel zoom plus Matplotlib toolbar controls for pan, zoom, and reset
- Manual price entry or CSV import (prefers a `Close` column)
- Best historical buy/sell days, profit and percentage return
- Recursive divide-and-conquer trace
- CSV report export
- Algorithm tests compared with a brute-force reference

The app analyzes only the historical prices you provide; it does not fetch live market data. Results are theoretical and exclude trading fees, taxes, and slippage.
