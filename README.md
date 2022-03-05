# Stock-Buyer-1
Python script that uses public API and Webull platform to execute algorithmic stock trades.

## Installation and setup
Download all files
Make sure that the following packages are installed from pip:  
- webull
- requests  

Create the following three text files in the same directory as the project
- "To_buy.txt": leave empty
- "Bought.txt": leave empty
- "Personal_data.txt"  
-- Put (in order, one per line) api key, webull email, webull password, login code, multi-factor authentication question number, question answer

## Usage
Run app.py
The program will use the text files created to access and store data.
It will use the paper-trading capability of webull for trading.
