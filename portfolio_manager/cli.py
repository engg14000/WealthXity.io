import argparse

def get_parser():
    """Returns the argument parser"""
    parser = argparse.ArgumentParser(description='Portfolio Manager')
    subparsers = parser.add_subparsers(dest='command', help='Commands', required=True)

    # Add command
    add_parser = subparsers.add_parser('add', help='Add a new item to the portfolio')
    add_subparsers = add_parser.add_subparsers(dest='type', help='Type of item to add', required=True)

    # Mutual Fund
    mf_parser = add_subparsers.add_parser('mf', help='Add a mutual fund')
    mf_parser.add_argument('--name', required=True)
    mf_parser.add_argument('--units', type=float, required=True)
    mf_parser.add_argument('--purchase_price', type=float, required=True)
    mf_parser.add_argument('--current_price', type=float, required=True)

    # Bank Account
    bank_parser = add_subparsers.add_parser('bank', help='Add a bank account')
    bank_parser.add_argument('--bank_name', required=True)
    bank_parser.add_argument('--account_number', required=True)
    bank_parser.add_argument('--balance', type=float, required=True)

    # NPS Account
    nps_parser = add_subparsers.add_parser('nps', help='Add an NPS account')
    nps_parser.add_argument('--pran', required=True)
    nps_parser.add_argument('--tier1_balance', type=float, required=True)
    nps_parser.add_argument('--tier2_balance', type=float, required=True)

    # Insurance
    ins_parser = add_subparsers.add_parser('insurance', help='Add an insurance policy')
    ins_parser.add_argument('--policy_name', required=True)
    ins_parser.add_argument('--premium', type=float, required=True)
    ins_parser.add_argument('--sum_assured', type=float, required=True)

    # Credit Card
    cc_parser = add_subparsers.add_parser('cc', help='Add a credit card')
    cc_parser.add_argument('--card_name', required=True)
    cc_parser.add_argument('--outstanding_balance', type=float, required=True)
    cc_parser.add_argument('--credit_limit', type=float, required=True)

    # Loan
    loan_parser = add_subparsers.add_parser('loan', help='Add a loan')
    loan_parser.add_argument('--loan_name', required=True)
    loan_parser.add_argument('--principal', type=float, required=True)
    loan_parser.add_argument('--interest_rate', type=float, required=True)
    loan_parser.add_argument('--tenure', type=int, required=True)

    # View command
    view_parser = subparsers.add_parser('view', help='View portfolio items')
    view_parser.add_argument('type', nargs='?', default='all', 
                             choices=['mf', 'bank', 'nps', 'insurance', 'cc', 'loan', 'all'],
                             help='Type of item to view')

    # Update command
    update_parser = subparsers.add_parser('update', help='Update an item in the portfolio')
    update_parser.add_argument('type', choices=['mf', 'bank', 'nps', 'insurance', 'cc', 'loan'], help='Type of item to update')
    update_parser.add_argument('name', help='Name/Identifier of the item to update')
    # Add arguments for fields to update
    update_parser.add_argument('--units', type=float)
    update_parser.add_argument('--purchase_price', type=float)
    update_parser.add_argument('--current_price', type=float)
    update_parser.add_argument('--balance', type=float)
    update_parser.add_argument('--tier1_balance', type=float)
    update_parser.add_argument('--tier2_balance', type=float)
    update_parser.add_argument('--premium', type=float)
    update_parser.add_argument('--sum_assured', type=float)
    update_parser.add_argument('--outstanding_balance', type=float)
    update_parser.add_argument('--credit_limit', type=float)
    update_parser.add_argument('--principal', type=float)
    update_parser.add_argument('--interest_rate', type=float)
    update_parser.add_argument('--tenure', type=int)

    # Delete command
    delete_parser = subparsers.add_parser('delete', help='Delete an item from the portfolio')
    delete_parser.add_argument('type', choices=['mf', 'bank', 'nps', 'insurance', 'cc', 'loan'], help='Type of item to delete')
    delete_parser.add_argument('name', help='Name/Identifier of the item to delete')

    return parser
