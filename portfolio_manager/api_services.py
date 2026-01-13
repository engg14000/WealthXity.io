"""
API Services for fetching live prices of various assets
"""
import requests
import re
from typing import Optional, Dict, List
from datetime import datetime
from bs4 import BeautifulSoup

# MFAPI.in - Free Indian Mutual Fund API
MFAPI_BASE_URL = "https://api.mfapi.in"

def get_mutual_fund_nav(scheme_code: str) -> Optional[Dict]:
    """
    Fetch latest NAV for a mutual fund scheme using MFAPI.in
    
    Args:
        scheme_code: AMFI scheme code (e.g., '119551' for Axis Bluechip Fund)
    
    Returns:
        Dictionary with nav and date, or None if failed
    """
    try:
        url = f"{MFAPI_BASE_URL}/mf/{scheme_code}/latest"
        response = requests.get(url, timeout=10,verify=False)
        if response.status_code == 200:
            data = response.json()
            return {
                'nav': float(data.get('data', [{}])[0].get('nav', 0)),
                'date': data.get('data', [{}])[0].get('date', ''),
                'scheme_name': data.get('meta', {}).get('scheme_name', ''),
            }
    except Exception as e:
        print(f"Error fetching NAV for {scheme_code}: {e}")
    return None

def search_mutual_funds(query: str) -> List[Dict]:
    """
    Search for mutual funds by name
    
    Args:
        query: Search query (fund name or part of it)
    
    Returns:
        List of matching funds with scheme codes
    """
    try:
        url = f"{MFAPI_BASE_URL}/mf/search?q={query}"
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            return response.json()
    except Exception as e:
        print(f"Error searching mutual funds: {e}")
    return []

def get_mutual_fund_history(scheme_code: str) -> List[Dict]:
    """
    Fetch NAV history for a mutual fund scheme
    
    Args:
        scheme_code: AMFI scheme code
    
    Returns:
        List of NAV data points with dates
    """
    try:
        url = f"{MFAPI_BASE_URL}/mf/{scheme_code}"
        response = requests.get(url, timeout=15)
        if response.status_code == 200:
            data = response.json()
            return data.get('data', [])
    except Exception as e:
        print(f"Error fetching history for {scheme_code}: {e}")
    return []

def update_all_mutual_fund_navs(funds_data: List[Dict]) -> List[Dict]:
    """
    Update NAVs for all mutual funds in the portfolio
    
    Args:
        funds_data: List of fund dictionaries with scheme_code
    
    Returns:
        Updated list with current NAVs
    """
    updated_funds = []
    for fund in funds_data:
        scheme_code = fund.get('scheme_code', '')
        if scheme_code:
            nav_data = get_mutual_fund_nav(scheme_code)
            if nav_data:
                fund['current_nav'] = nav_data['nav']
        updated_funds.append(fund)
    return updated_funds

# Metal prices from Thangamayil (Indian jeweller with live rates)
def get_metal_rates() -> Dict:
    """
    Fetch live gold and silver rates from thangamayil.com
    
    Returns:
        Dictionary with gold_22k, gold_24k, gold_18k, silver prices in INR per gram
    """
    rates = {
        'gold_22k': None,
        'gold_24k': None,
        'gold_18k': None,
        'silver': None,
        'last_updated': None
    }
    
    try:
        url = 'https://www.thangamayil.com/scheme/index/rateshistory/'
        response = requests.get(url, timeout=10, verify=False)
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Extract rates from the marquee tag
        marquee = soup.find('div', id='board-rates')
        if marquee:
            text = marquee.get_text()
            gold_22k_match = re.search(r'GOLD RATE 22k \(1gm\) - ₹(\d+)', text)
            if gold_22k_match:
                rates['gold_22k'] = int(gold_22k_match.group(1))
        
        # Extract rates from the list items
        rates_list = soup.find('ul', class_='rates-list')
        if rates_list:
            for li in rates_list.find_all('li'):
                li_text = li.get_text()
                price_span = li.find('span', class_='price')
                if price_span:
                    price_text = price_span.get_text().strip('₹').replace(',', '')
                    try:
                        price = int(float(price_text))
                        if 'Gold 18k' in li_text:
                            rates['gold_18k'] = price
                        elif 'Gold 24k' in li_text:
                            rates['gold_24k'] = price
                        elif 'Silver' in li_text:
                            rates['silver'] = price
                    except ValueError:
                        pass
        
        # Extract last updated time
        last_updated_div = soup.find('div', class_='card-header')
        if last_updated_div:
            last_updated_text = last_updated_div.get_text()
            last_updated_match = re.search(r'Last updated on : ([\d/ :AMP]+)', last_updated_text)
            if last_updated_match:
                rates['last_updated'] = last_updated_match.group(1)
        
    except Exception as e:
        print(f"Error fetching metal rates: {e}")
    
    return rates


def get_gold_price() -> Optional[Dict]:
    """
    Fetch current gold price in INR per gram
    """
    rates = get_metal_rates()
    if rates.get('gold_24k') or rates.get('gold_22k'):
        return {
            'price_per_gram_24k': rates.get('gold_24k'),
            'price_per_gram_22k': rates.get('gold_22k'),
            'price_per_gram_18k': rates.get('gold_18k'),
            'currency': 'INR',
            'last_updated': rates.get('last_updated'),
            'timestamp': datetime.now().isoformat()
        }
    return None


def get_silver_price() -> Optional[Dict]:
    """
    Fetch current silver price in INR per gram
    """
    rates = get_metal_rates()
    if rates.get('silver'):
        return {
            'price_per_gram': rates.get('silver'),
            'currency': 'INR',
            'last_updated': rates.get('last_updated'),
            'timestamp': datetime.now().isoformat()
        }
    return None

def calculate_future_value(present_value: float, annual_return: float, years: int) -> float:
    """
    Calculate future value with compound interest
    
    Args:
        present_value: Current value
        annual_return: Expected annual return in percentage
        years: Number of years
    
    Returns:
        Future value
    """
    return present_value * ((1 + annual_return / 100) ** years)

def generate_forecast(assets: Dict, years: int = 10) -> List[Dict]:
    """
    Generate year-by-year forecast for all assets
    
    Args:
        assets: Dictionary with asset values and expected returns
        years: Number of years to forecast
    
    Returns:
        List of yearly projections
    """
    projections = []
    
    for year in range(years + 1):
        year_data = {'year': year}
        total = 0
        
        for asset_name, asset_info in assets.items():
            value = asset_info.get('value', 0)
            return_rate = asset_info.get('expected_return', 8)
            future_val = calculate_future_value(value, return_rate, year)
            year_data[asset_name] = round(future_val, 2)
            total += future_val
        
        year_data['total'] = round(total, 2)
        projections.append(year_data)
    
    return projections
