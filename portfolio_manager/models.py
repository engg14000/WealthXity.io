from dataclasses import dataclass, asdict, fields
from typing import Dict, Type, List

@dataclass
class MutualFund:
    fund_name: str
    scheme_code: str  # AMFI scheme code for API lookup
    folio_number: str
    amc: str
    units: float
    purchase_nav: float
    current_nav: float
    investment_date: str
    category: str  # Equity, Debt, Hybrid, etc.
    expected_return: float  # Expected annual return % for forecasting

@dataclass
class Stock:
    stock_name: str
    symbol: str  # NSE/BSE symbol
    exchange: str  # NSE or BSE
    quantity: int
    purchase_price: float
    current_price: float
    purchase_date: str
    sector: str
    expected_return: float  # Expected annual return %

@dataclass
class RealEstate:
    property_name: str
    property_type: str  # Residential, Commercial, Land, Plot
    location: str
    purchase_date: str
    purchase_value: float
    current_value: float
    appreciation_rate: float  # Annual appreciation rate %
    loan_outstanding: float  # If any loan on property
    rental_income: float  # Monthly rental income if any

@dataclass
class Gold:
    item_name: str
    item_type: str  # Physical, Digital, SGB, Gold ETF
    weight_grams: float
    purchase_price_per_gram: float
    current_price_per_gram: float
    purchase_date: str
    purity: str  # 24K, 22K, 18K
    expected_return: float  # Expected annual return %

@dataclass
class Silver:
    item_name: str
    item_type: str  # Physical, Digital, Silver ETF
    weight_grams: float
    purchase_price_per_gram: float
    current_price_per_gram: float
    purchase_date: str
    purity: str  # 999, 925
    expected_return: float  # Expected annual return %

@dataclass
class BankAccount:
    bank_name: str
    account_number: str
    account_type: str  # Savings, Current, FD, RD
    branch: str
    ifsc_code: str
    balance: float
    interest_rate: float  # For FD/RD
    nominee: str

@dataclass
class NPSAccount:
    pran_number: str
    subscriber_name: str
    tier1_balance: float
    tier2_balance: float
    fund_manager: str
    scheme_preference: str  # Aggressive, Moderate, Conservative
    expected_return: float  # Expected annual return %

@dataclass
class PPF:
    account_number: str
    bank_name: str
    opening_date: str
    maturity_date: str
    current_balance: float
    yearly_contribution: float
    interest_rate: float  # Current PPF rate

@dataclass
class EPF:
    uan_number: str
    employer_name: str
    employee_contribution: float
    employer_contribution: float
    total_balance: float
    interest_rate: float

@dataclass
class FixedDeposit:
    fd_name: str
    bank_name: str
    account_number: str
    principal_amount: float
    interest_rate: float
    start_date: str
    maturity_date: str
    maturity_amount: float
    interest_payout: str  # Monthly, Quarterly, At Maturity
    nominee: str

@dataclass
class Insurance:
    policy_name: str
    policy_number: str
    insurer: str
    policy_type: str  # Term, Endowment, ULIP, Health
    premium_amount: float
    premium_frequency: str  # Monthly, Quarterly, Yearly
    sum_assured: float
    start_date: str
    maturity_date: str
    nominee: str

@dataclass
class CreditCard:
    card_name: str
    card_number_last4: str
    bank_name: str
    credit_limit: float
    outstanding_balance: float
    billing_date: int
    due_date: int
    reward_points: float

@dataclass
class Loan:
    loan_name: str
    loan_account_number: str
    lender: str
    loan_type: str  # Home, Car, Personal, Education
    principal_amount: float
    outstanding_amount: float
    interest_rate: float
    emi_amount: float
    tenure_months: int
    start_date: str
    end_date: str

@dataclass
class NetWorthHistory:
    record_date: str
    mutual_funds: float
    stocks: float
    real_estate: float
    gold: float
    silver: float
    bank_balance: float
    nps: float
    ppf: float
    epf: float
    total_assets: float
    total_liabilities: float
    net_worth: float

# Default expected returns for forecasting (annual %)
DEFAULT_RETURNS: Dict[str, float] = {
    'mutual_fund_equity': 12.0,
    'mutual_fund_debt': 7.0,
    'mutual_fund_hybrid': 10.0,
    'stocks': 12.0,
    'real_estate': 8.0,
    'gold': 8.0,
    'silver': 7.0,
    'nps': 10.0,
    'ppf': 7.1,
    'epf': 8.25,
    'fd': 7.0,
    'savings': 3.5,
}

# Model registry for easy lookup
MODEL_REGISTRY: Dict[str, Type] = {
    'mutualfund': MutualFund,
    'stock': Stock,
    'realestate': RealEstate,
    'gold': Gold,
    'silver': Silver,
    'bankaccount': BankAccount,
    'fixeddeposit': FixedDeposit,
    'npsaccount': NPSAccount,
    'ppf': PPF,
    'epf': EPF,
    'insurance': Insurance,
    'creditcard': CreditCard,
    'loan': Loan,
    'networthhistory': NetWorthHistory,
}

# Display names for UI
MODEL_DISPLAY_NAMES: Dict[str, str] = {
    'mutualfund': 'Mutual Funds',
    'stock': 'Stocks',
    'realestate': 'Real Estate',
    'gold': 'Gold',
    'silver': 'Silver',
    'bankaccount': 'Bank Accounts',
    'fixeddeposit': 'Fixed Deposits',
    'npsaccount': 'NPS Accounts',
    'ppf': 'PPF',
    'epf': 'EPF',
    'insurance': 'Insurance Policies',
    'creditcard': 'Credit Cards',
    'loan': 'Loans',
    'networthhistory': 'Net Worth History',
}

# Short codes for URL routing
MODEL_SHORT_CODES: Dict[str, str] = {
    'mf': 'mutualfund',
    'stock': 'stock',
    'realestate': 'realestate',
    'gold': 'gold',
    'silver': 'silver',
    'bank': 'bankaccount',
    'fd': 'fixeddeposit',
    'nps': 'npsaccount',
    'ppf': 'ppf',
    'epf': 'epf',
    'insurance': 'insurance',
    'cc': 'creditcard',
    'loan': 'loan',
}

# Asset categories for net worth calculation
ASSET_CATEGORIES = {
    'investments': ['mutualfund', 'stock', 'npsaccount', 'ppf', 'epf'],
    'real_assets': ['realestate', 'gold', 'silver'],
    'liquid': ['bankaccount', 'fixeddeposit'],
    'liabilities': ['loan', 'creditcard'],
}

def get_model_class(type_code: str) -> Type:
    """Get model class from short code or full name"""
    if type_code in MODEL_SHORT_CODES:
        type_code = MODEL_SHORT_CODES[type_code]
    return MODEL_REGISTRY.get(type_code.lower())

def get_model_fields(type_code: str) -> List[str]:
    """Get field names for a model type"""
    model_class = get_model_class(type_code)
    if model_class:
        return [f.name for f in fields(model_class)]
    return []

def get_sheet_name(type_code: str) -> str:
    """Get Excel sheet name for a model type"""
    if type_code in MODEL_SHORT_CODES:
        type_code = MODEL_SHORT_CODES[type_code]
    return MODEL_DISPLAY_NAMES.get(type_code.lower(), type_code)
