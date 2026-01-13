"""
API Services for fetching live prices of various assets
"""
import requests
from typing import Optional, Dict, List
from datetime import datetime

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

# Gold price API (using a free API)
def get_gold_price() -> Optional[Dict]:
    """
    Fetch current gold price in INR per gram
    Note: This uses a free API with limited requests
    """
    try:
        # Using metals.live API (free tier)
        url = "https://www.metals.live/api/v1/spot/gold"
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            # Convert from USD/oz to INR/gram (approximate)
            usd_per_oz = float(data[0].get('price', 0))
            # Get USD to INR rate (approximate, you can use another API)
            usd_to_inr = 83.0  # Approximate rate
            gram_per_oz = 31.1035
            inr_per_gram = (usd_per_oz * usd_to_inr) / gram_per_oz
            return {
                'price_per_gram_24k': round(inr_per_gram, 2),
                'price_per_gram_22k': round(inr_per_gram * 0.9167, 2),
                'currency': 'INR',
                'timestamp': datetime.now().isoformat()
            }
    except Exception as e:
        print(f"Error fetching gold price: {e}")
    return None

def get_silver_price() -> Optional[Dict]:
    """
    Fetch current silver price in INR per gram
    """
    try:
        url = "https://www.metals.live/api/v1/spot/silver"
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            usd_per_oz = float(data[0].get('price', 0))
            usd_to_inr = 83.0
            gram_per_oz = 31.1035
            inr_per_gram = (usd_per_oz * usd_to_inr) / gram_per_oz
            return {
                'price_per_gram': round(inr_per_gram, 2),
                'currency': 'INR',
                'timestamp': datetime.now().isoformat()
            }
    except Exception as e:
        print(f"Error fetching silver price: {e}")
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
