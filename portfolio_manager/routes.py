from flask import render_template, request, redirect, url_for, flash, send_file, jsonify
import json
from portfolio_manager import app
from portfolio_manager.models import (
    get_model_class, get_model_fields, get_sheet_name,
    MODEL_DISPLAY_NAMES, MODEL_SHORT_CODES, DEFAULT_RETURNS
)
from portfolio_manager import api_services
from portfolio_manager.storage import (
    get_config, save_config, get_storage, set_storage_mode,
    FirebaseStorage, get_data, save_data, get_sheet_names
)
import pandas as pd
import io
from datetime import datetime

# App Configuration
APP_NAME = "TruWealthily"
APP_TAGLINE = "Your Wealth, Simplified"
app.secret_key = 'wealthpulse_secret_key_change_in_production'


def is_firebase_mode():
    """Check if Firebase storage mode is active"""
    config = get_config()
    return config.get('storage_mode') == 'firebase'


@app.context_processor
def inject_app_info():
    config = get_config()
    return {
        'app_name': APP_NAME,
        'app_tagline': APP_TAGLINE,
        'storage_mode': config.get('storage_mode', 'browser')
    }


def calculate_portfolio_summary_from_data(all_data):
    """Calculate portfolio summary from provided data"""
    summary = {
        'mutual_funds': 0, 'stocks': 0, 'real_estate': 0, 'gold': 0, 'silver': 0,
        'bank_balance': 0, 'fixed_deposits': 0, 'nps': 0, 'ppf': 0, 'epf': 0,
        'insurance_cover': 0, 'credit_card_outstanding': 0, 'loans_outstanding': 0,
        'total_assets': 0, 'total_liabilities': 0, 'net_worth': 0
    }
    
    for sheet, items in all_data.items():
        if sheet in ('Summary', 'Net Worth History') or not items:
            continue
        
        if sheet == 'Mutual Funds':
            for row in items:
                try:
                    summary['mutual_funds'] += float(row.get('units', 0) or 0) * float(row.get('current_nav', 0) or 0)
                except (ValueError, TypeError):
                    pass
        elif sheet == 'Stocks':
            for row in items:
                try:
                    summary['stocks'] += float(row.get('quantity', 0) or 0) * float(row.get('current_price', 0) or 0)
                except (ValueError, TypeError):
                    pass
        elif sheet == 'Real Estate':
            for row in items:
                try:
                    summary['real_estate'] += float(row.get('current_value', 0) or 0) - float(row.get('loan_outstanding', 0) or 0)
                except (ValueError, TypeError):
                    pass
        elif sheet == 'Gold':
            for row in items:
                try:
                    summary['gold'] += float(row.get('weight_grams', 0) or 0) * float(row.get('current_price_per_gram', 0) or 0)
                except (ValueError, TypeError):
                    pass
        elif sheet == 'Silver':
            for row in items:
                try:
                    summary['silver'] += float(row.get('weight_grams', 0) or 0) * float(row.get('current_price_per_gram', 0) or 0)
                except (ValueError, TypeError):
                    pass
        elif sheet == 'Bank Accounts':
            for row in items:
                try:
                    summary['bank_balance'] += float(row.get('balance', 0) or 0)
                except (ValueError, TypeError):
                    pass
        elif sheet == 'Fixed Deposits':
            for row in items:
                try:
                    summary['fixed_deposits'] += float(row.get('principal_amount', 0) or 0)
                except (ValueError, TypeError):
                    pass
        elif sheet == 'NPS Accounts':
            for row in items:
                try:
                    summary['nps'] += float(row.get('tier1_balance', 0) or 0)
                    summary['nps'] += float(row.get('tier2_balance', 0) or 0)
                except (ValueError, TypeError):
                    pass
        elif sheet == 'PPF':
            for row in items:
                try:
                    summary['ppf'] += float(row.get('current_balance', 0) or 0)
                except (ValueError, TypeError):
                    pass
        elif sheet == 'EPF':
            for row in items:
                try:
                    summary['epf'] += float(row.get('total_balance', 0) or 0)
                except (ValueError, TypeError):
                    pass
        elif sheet == 'Insurance Policies':
            for row in items:
                try:
                    summary['insurance_cover'] += float(row.get('sum_assured', 0) or 0)
                except (ValueError, TypeError):
                    pass
        elif sheet == 'Credit Cards':
            for row in items:
                try:
                    summary['credit_card_outstanding'] += float(row.get('outstanding_balance', 0) or 0)
                except (ValueError, TypeError):
                    pass
        elif sheet == 'Loans':
            for row in items:
                try:
                    summary['loans_outstanding'] += float(row.get('outstanding_amount', 0) or 0)
                except (ValueError, TypeError):
                    pass
    
    summary['total_assets'] = (
        summary['mutual_funds'] + summary['stocks'] + summary['real_estate'] +
        summary['gold'] + summary['silver'] + summary['bank_balance'] +
        summary['fixed_deposits'] + summary['nps'] + summary['ppf'] + summary['epf']
    )
    summary['total_liabilities'] = summary['loans_outstanding'] + summary['credit_card_outstanding']
    summary['net_worth'] = summary['total_assets'] - summary['total_liabilities']
    
    return summary


def build_forecast_assets(all_data, summary):
    """Build assets dictionary for forecasting from provided data"""
    assets = {}
    
    if summary['mutual_funds'] > 0:
        mf_items = all_data.get('Mutual Funds', [])
        avg_return = DEFAULT_RETURNS['mutual_fund_equity']
        if mf_items:
            returns = [float(r.get('expected_return', 0) or 0) for r in mf_items if r.get('expected_return')]
            if returns:
                avg_return = sum(returns) / len(returns)
        assets['Mutual Funds'] = {'value': summary['mutual_funds'], 'expected_return': avg_return}
    
    if summary['stocks'] > 0:
        stock_items = all_data.get('Stocks', [])
        avg_return = DEFAULT_RETURNS['stocks']
        if stock_items:
            returns = [float(r.get('expected_return', 0) or 0) for r in stock_items if r.get('expected_return')]
            if returns:
                avg_return = sum(returns) / len(returns)
        assets['Stocks'] = {'value': summary['stocks'], 'expected_return': avg_return}
    
    if summary['real_estate'] > 0:
        re_items = all_data.get('Real Estate', [])
        avg_return = DEFAULT_RETURNS['real_estate']
        if re_items:
            returns = [float(r.get('appreciation_rate', 0) or 0) for r in re_items if r.get('appreciation_rate')]
            if returns:
                avg_return = sum(returns) / len(returns)
        assets['Real Estate'] = {'value': summary['real_estate'], 'expected_return': avg_return}
    
    if summary['gold'] > 0:
        gold_items = all_data.get('Gold', [])
        avg_return = DEFAULT_RETURNS['gold']
        if gold_items:
            returns = [float(r.get('expected_return', 0) or 0) for r in gold_items if r.get('expected_return')]
            if returns:
                avg_return = sum(returns) / len(returns)
        assets['Gold'] = {'value': summary['gold'], 'expected_return': avg_return}
    
    if summary['silver'] > 0:
        silver_items = all_data.get('Silver', [])
        avg_return = DEFAULT_RETURNS['silver']
        if silver_items:
            returns = [float(r.get('expected_return', 0) or 0) for r in silver_items if r.get('expected_return')]
            if returns:
                avg_return = sum(returns) / len(returns)
        assets['Silver'] = {'value': summary['silver'], 'expected_return': avg_return}
    
    if summary['bank_balance'] > 0:
        assets['Bank Balance'] = {'value': summary['bank_balance'], 'expected_return': DEFAULT_RETURNS['savings']}
    
    if summary['nps'] > 0:
        nps_items = all_data.get('NPS Accounts', [])
        avg_return = DEFAULT_RETURNS['nps']
        if nps_items:
            returns = [float(r.get('expected_return', 0) or 0) for r in nps_items if r.get('expected_return')]
            if returns:
                avg_return = sum(returns) / len(returns)
        assets['NPS'] = {'value': summary['nps'], 'expected_return': avg_return}
    
    if summary['ppf'] > 0:
        assets['PPF'] = {'value': summary['ppf'], 'expected_return': DEFAULT_RETURNS['ppf']}
    
    if summary['epf'] > 0:
        assets['EPF'] = {'value': summary['epf'], 'expected_return': DEFAULT_RETURNS['epf']}
    
    return assets


def get_all_firebase_data():
    """Get all data from Firebase storage as dictionary"""
    all_data = {}
    sheet_names = get_sheet_names()
    for sheet in sheet_names:
        if sheet == 'Summary':
            continue
        df = get_data(sheet)
        if not df.empty:
            all_data[sheet] = df.to_dict('records')
        else:
            all_data[sheet] = []
    return all_data


# ============================================================================
# PAGE ROUTES
# ============================================================================

@app.route('/')
def index():
    """Dashboard view"""
    config = get_config()
    empty_summary = {
        'mutual_funds': 0, 'stocks': 0, 'real_estate': 0, 'gold': 0, 'silver': 0,
        'bank_balance': 0, 'fixed_deposits': 0, 'nps': 0, 'ppf': 0, 'epf': 0,
        'insurance_cover': 0, 'credit_card_outstanding': 0, 'loans_outstanding': 0,
        'total_assets': 0, 'total_liabilities': 0, 'net_worth': 0
    }
    
    if is_firebase_mode():
        # Firebase mode: load data server-side
        all_data = get_all_firebase_data()
        summary = calculate_portfolio_summary_from_data(all_data)
        history = all_data.get('Net Worth History', [])
        return render_template('index.html', 
                             all_data=all_data, 
                             summary=summary,
                             networth_history=history,
                             model_types=MODEL_SHORT_CODES,
                             display_names=MODEL_DISPLAY_NAMES)
    else:
        # Browser mode: data loaded client-side
        return render_template('index.html', 
                             all_data={}, 
                             summary=empty_summary,
                             networth_history=[],
                             model_types=MODEL_SHORT_CODES,
                             display_names=MODEL_DISPLAY_NAMES)


@app.route('/add', methods=['GET', 'POST'])
def add_item():
    """Add item form page"""
    item_type = request.args.get('type') or request.form.get('type')
    fields = get_model_fields(item_type) if item_type else []
    
    # Firebase mode: handle form submission server-side
    if is_firebase_mode() and request.method == 'POST' and fields and request.form.get(fields[0]):
        sheet_name = get_sheet_name(item_type)
        data = {field: request.form.get(field, '') for field in fields}
        
        df = get_data(sheet_name)
        new_df = pd.DataFrame([data])
        df = pd.concat([df, new_df], ignore_index=True)
        save_data(sheet_name, df)
        
        flash(f'Successfully added new item!', 'success')
        return redirect(url_for('view_items', item_type=item_type))
    
    return render_template('add.html', 
                         type=item_type, 
                         fields=fields,
                         model_types=MODEL_SHORT_CODES,
                         display_names=MODEL_DISPLAY_NAMES)


@app.route('/view/<item_type>')
def view_items(item_type):
    """View items page"""
    sheet_name = get_sheet_name(item_type)
    
    if is_firebase_mode():
        # Firebase mode: load data server-side
        df = get_data(sheet_name)
        items = df.to_dict('records') if not df.empty else []
    else:
        # Browser mode: data loaded client-side
        items = []
    
    return render_template('view.html',
                         item_type=item_type,
                         sheet_name=sheet_name,
                         items=items,
                         model_types=MODEL_SHORT_CODES,
                         display_names=MODEL_DISPLAY_NAMES)


@app.route('/edit/<item_type>/<int:row_index>', methods=['GET', 'POST'])
def edit_item(item_type, row_index):
    """Edit item page"""
    sheet_name = get_sheet_name(item_type)
    fields = get_model_fields(item_type)
    
    if is_firebase_mode():
        # Firebase mode: handle server-side
        df = get_data(sheet_name)
        
        if row_index >= len(df):
            flash('Item not found!', 'error')
            return redirect(url_for('view_items', item_type=item_type))
        
        if request.method == 'POST':
            for field in fields:
                if field in request.form:
                    df.at[row_index, field] = request.form[field]
            save_data(sheet_name, df)
            flash('Successfully updated item!', 'success')
            return redirect(url_for('view_items', item_type=item_type))
        
        item = df.iloc[row_index].to_dict()
    else:
        # Browser mode: data loaded client-side
        item = {}
    
    return render_template('edit.html', 
                         item_type=item_type, 
                         item=item,
                         row_index=row_index,
                         fields=fields,
                         model_types=MODEL_SHORT_CODES,
                         display_names=MODEL_DISPLAY_NAMES)


@app.route('/delete/<item_type>/<int:row_index>')
def delete_item(item_type, row_index):
    """Delete item - Firebase mode only"""
    if is_firebase_mode():
        sheet_name = get_sheet_name(item_type)
        df = get_data(sheet_name)
        
        if row_index < len(df):
            df = df.drop(df.index[row_index]).reset_index(drop=True)
            save_data(sheet_name, df)
            flash('Successfully deleted item!', 'success')
        else:
            flash('Item not found!', 'error')
    
    return redirect(url_for('view_items', item_type=item_type))


@app.route('/networth')
def networth_tracker():
    """Net worth tracker page"""
    empty_summary = {
        'mutual_funds': 0, 'stocks': 0, 'real_estate': 0, 'gold': 0, 'silver': 0,
        'bank_balance': 0, 'fixed_deposits': 0, 'nps': 0, 'ppf': 0, 'epf': 0,
        'insurance_cover': 0, 'credit_card_outstanding': 0, 'loans_outstanding': 0,
        'total_assets': 0, 'total_liabilities': 0, 'net_worth': 0
    }
    
    if is_firebase_mode():
        all_data = get_all_firebase_data()
        summary = calculate_portfolio_summary_from_data(all_data)
        history = all_data.get('Net Worth History', [])
    else:
        summary = empty_summary
        history = []
    
    return render_template('networth.html',
                         summary=summary,
                         history=history,
                         model_types=MODEL_SHORT_CODES,
                         display_names=MODEL_DISPLAY_NAMES)


@app.route('/networth/snapshot', methods=['POST'])
def save_networth_snapshot():
    """Save net worth snapshot - Firebase mode"""
    if is_firebase_mode():
        all_data = get_all_firebase_data()
        summary = calculate_portfolio_summary_from_data(all_data)
        
        snapshot = {
            'record_date': datetime.now().strftime('%Y-%m-%d'),
            'mutual_funds': round(summary['mutual_funds'], 2),
            'stocks': round(summary['stocks'], 2),
            'real_estate': round(summary['real_estate'], 2),
            'gold': round(summary['gold'], 2),
            'silver': round(summary['silver'], 2),
            'bank_balance': round(summary['bank_balance'], 2),
            'nps': round(summary['nps'], 2),
            'ppf': round(summary['ppf'], 2),
            'epf': round(summary['epf'], 2),
            'total_assets': round(summary['total_assets'], 2),
            'total_liabilities': round(summary['total_liabilities'], 2),
            'net_worth': round(summary['net_worth'], 2),
        }
        
        df = get_data('Net Worth History')
        new_df = pd.DataFrame([snapshot])
        df = pd.concat([df, new_df], ignore_index=True)
        save_data('Net Worth History', df)
        
        flash('Net worth snapshot saved successfully!', 'success')
    
    return redirect(url_for('networth_tracker'))


@app.route('/networth/delete/<int:row_index>')
def delete_networth_record(row_index):
    """Delete net worth record - Firebase mode"""
    if is_firebase_mode():
        df = get_data('Net Worth History')
        if row_index < len(df):
            df = df.drop(df.index[row_index]).reset_index(drop=True)
            save_data('Net Worth History', df)
            flash('Record deleted successfully!', 'success')
        else:
            flash('Record not found!', 'error')
    
    return redirect(url_for('networth_tracker'))


@app.route('/networth/purge', methods=['POST'])
def purge_networth_history():
    """Purge all net worth history - Firebase mode"""
    if is_firebase_mode():
        save_data('Net Worth History', pd.DataFrame())
        flash('All history records purged successfully!', 'success')
    
    return redirect(url_for('networth_tracker'))


@app.route('/forecast')
def forecast():
    """Forecast page"""
    empty_summary = {
        'mutual_funds': 0, 'stocks': 0, 'real_estate': 0, 'gold': 0, 'silver': 0,
        'bank_balance': 0, 'fixed_deposits': 0, 'nps': 0, 'ppf': 0, 'epf': 0,
        'insurance_cover': 0, 'credit_card_outstanding': 0, 'loans_outstanding': 0,
        'total_assets': 0, 'total_liabilities': 0, 'net_worth': 0
    }
    forecast_years = int(request.args.get('years', 10))
    
    if is_firebase_mode():
        all_data = get_all_firebase_data()
        summary = calculate_portfolio_summary_from_data(all_data)
        assets = build_forecast_assets(all_data, summary)
        projections = api_services.generate_forecast(assets, forecast_years)
    else:
        summary = empty_summary
        assets = {}
        projections = []
    
    return render_template('forecast.html',
                         summary=summary,
                         assets=assets,
                         projections=projections,
                         forecast_years=forecast_years,
                         default_returns=DEFAULT_RETURNS,
                         model_types=MODEL_SHORT_CODES,
                         display_names=MODEL_DISPLAY_NAMES)


@app.route('/settings')
def settings():
    """Settings page"""
    config = get_config()
    return render_template('settings.html',
                         config=config,
                         default_returns=DEFAULT_RETURNS,
                         model_types=MODEL_SHORT_CODES,
                         display_names=MODEL_DISPLAY_NAMES)


@app.route('/settings/storage', methods=['POST'])
def update_storage_settings():
    """Update storage mode settings"""
    storage_mode = request.form.get('storage_mode', 'browser')
    
    if storage_mode == 'firebase':
        firebase_config = {
            'service_account_path': request.form.get('firebase_service_account_path', ''),
            'user_id': request.form.get('firebase_user_id', 'default_user'),
        }
        
        if 'firebase_service_account_file' in request.files:
            file = request.files['firebase_service_account_file']
            if file and file.filename.endswith('.json'):
                firebase_config['service_account_json'] = json.load(file)
        
        try:
            set_storage_mode('firebase', firebase_config)
            flash('Storage mode switched to Firebase Firestore!', 'success')
        except Exception as e:
            flash(f'Failed to connect to Firebase: {str(e)}', 'error')
            set_storage_mode('browser')
    else:
        set_storage_mode('browser')
        flash('Storage mode switched to Browser (localStorage)!', 'success')
    
    return redirect(url_for('settings'))


@app.route('/privacy')
def privacy_policy():
    """Privacy policy page"""
    return render_template('privacy.html',
                         model_types=MODEL_SHORT_CODES,
                         display_names=MODEL_DISPLAY_NAMES)


@app.route('/import')
def import_data():
    """Import page"""
    return render_template('import.html',
                         model_types=MODEL_SHORT_CODES,
                         display_names=MODEL_DISPLAY_NAMES)


# ============================================================================
# STATELESS API ENDPOINTS - For Browser mode (frontend sends data in payload)
# ============================================================================

@app.route('/api/calculate-summary', methods=['POST'])
def api_calculate_summary():
    """Stateless: Calculate portfolio summary from provided data"""
    try:
        data = request.get_json() or {}
        summary = calculate_portfolio_summary_from_data(data)
        return jsonify({'success': True, 'summary': summary})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})


@app.route('/api/calculate-forecast', methods=['POST'])
def api_calculate_forecast():
    """Stateless: Calculate forecast from provided data"""
    try:
        payload = request.get_json() or {}
        all_data = payload.get('data', {})
        years = int(payload.get('years', 10))
        
        summary = calculate_portfolio_summary_from_data(all_data)
        assets = build_forecast_assets(all_data, summary)
        projections = api_services.generate_forecast(assets, years)
        
        return jsonify({
            'success': True,
            'summary': summary,
            'assets': assets,
            'projections': projections
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})


@app.route('/api/create-snapshot', methods=['POST'])
def api_create_snapshot():
    """Stateless: Create net worth snapshot from provided data"""
    try:
        data = request.get_json() or {}
        summary = calculate_portfolio_summary_from_data(data)
        
        snapshot = {
            'record_date': datetime.now().strftime('%Y-%m-%d'),
            'mutual_funds': round(summary['mutual_funds'], 2),
            'stocks': round(summary['stocks'], 2),
            'real_estate': round(summary['real_estate'], 2),
            'gold': round(summary['gold'], 2),
            'silver': round(summary['silver'], 2),
            'bank_balance': round(summary['bank_balance'], 2),
            'nps': round(summary['nps'], 2),
            'ppf': round(summary['ppf'], 2),
            'epf': round(summary['epf'], 2),
            'total_assets': round(summary['total_assets'], 2),
            'total_liabilities': round(summary['total_liabilities'], 2),
            'net_worth': round(summary['net_worth'], 2),
        }
        
        return jsonify({'success': True, 'snapshot': snapshot})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})


@app.route('/api/update-mf-nav', methods=['POST'])
def api_update_mf_nav():
    """Update NAVs for mutual funds"""
    try:
        if is_firebase_mode():
            # Firebase mode: update in database
            df = get_data('Mutual Funds')
            if df.empty:
                return jsonify({'success': False, 'message': 'No mutual funds found'})
            
            updated_count = 0
            for idx, row in df.iterrows():
                scheme_code = str(row.get('scheme_code', '')).strip()
                if scheme_code:
                    nav_data = api_services.get_mutual_fund_nav(scheme_code)
                    if nav_data and nav_data.get('nav'):
                        df.at[idx, 'current_nav'] = nav_data['nav']
                        updated_count += 1
            
            save_data('Mutual Funds', df)
            return jsonify({'success': True, 'message': f'Updated {updated_count} mutual fund NAVs'})
        else:
            # Browser mode: update provided funds and return
            funds = request.get_json() or []
            updated_funds = []
            updated_count = 0
            
            for fund in funds:
                scheme_code = str(fund.get('scheme_code', '')).strip()
                if scheme_code:
                    nav_data = api_services.get_mutual_fund_nav(scheme_code)
                    if nav_data and nav_data.get('nav'):
                        fund['current_nav'] = nav_data['nav']
                        updated_count += 1
                updated_funds.append(fund)
            
            return jsonify({
                'success': True, 
                'message': f'Updated {updated_count} mutual fund NAVs',
                'funds': updated_funds
            })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})


@app.route('/api/search-mf')
def search_mf():
    """Search mutual funds by name"""
    query = request.args.get('q', '')
    if not query or len(query) < 3:
        return jsonify([])
    results = api_services.search_mutual_funds(query)
    return jsonify(results[:20])


@app.route('/api/get-mf-nav/<scheme_code>')
def get_mf_nav(scheme_code):
    """Get NAV for a specific mutual fund"""
    nav_data = api_services.get_mutual_fund_nav(scheme_code)
    if nav_data:
        return jsonify(nav_data)
    return jsonify({'error': 'Unable to fetch NAV'}), 404


@app.route('/api/metal-prices')
def get_metal_prices():
    """Get current gold and silver prices"""
    return jsonify({
        'gold': api_services.get_gold_price(),
        'silver': api_services.get_silver_price()
    })


@app.route('/api/get-storage-mode')
def api_get_storage_mode():
    """Get current storage mode"""
    config = get_config()
    return jsonify({'storage_mode': config.get('storage_mode', 'browser')})


@app.route('/api/update-metal-prices', methods=['POST'])
def api_update_metal_prices():
    """Update gold and silver prices in holdings"""
    try:
        # Fetch live rates
        rates = api_services.get_metal_rates()
        
        if not rates.get('gold_24k') and not rates.get('silver'):
            return jsonify({'success': False, 'message': 'Unable to fetch metal prices'})
        
        if is_firebase_mode():
            # Firebase mode: update in database
            updated_gold = 0
            updated_silver = 0
            
            # Update Gold holdings
            gold_df = get_data('Gold')
            if not gold_df.empty:
                for idx, row in gold_df.iterrows():
                    purity = str(row.get('purity', '')).upper()
                    if '24' in purity and rates.get('gold_24k'):
                        gold_df.at[idx, 'current_price_per_gram'] = rates['gold_24k']
                        updated_gold += 1
                    elif '22' in purity and rates.get('gold_22k'):
                        gold_df.at[idx, 'current_price_per_gram'] = rates['gold_22k']
                        updated_gold += 1
                    elif '18' in purity and rates.get('gold_18k'):
                        gold_df.at[idx, 'current_price_per_gram'] = rates['gold_18k']
                        updated_gold += 1
                save_data('Gold', gold_df)
            
            # Update Silver holdings
            silver_df = get_data('Silver')
            if not silver_df.empty:
                for idx, row in silver_df.iterrows():
                    purity = str(row.get('purity', '')).upper()
                    if rates.get('silver'):
                        if '999' in purity:
                            silver_df.at[idx, 'current_price_per_gram'] = rates['silver']
                        elif '925' in purity:
                            silver_df.at[idx, 'current_price_per_gram'] = int(rates['silver'] * 0.925)
                        else:
                            silver_df.at[idx, 'current_price_per_gram'] = rates['silver']
                        updated_silver += 1
                save_data('Silver', silver_df)
            
            return jsonify({
                'success': True,
                'message': f'Updated {updated_gold} gold and {updated_silver} silver items',
                'rates': rates
            })
        else:
            # Browser mode: update provided data and return
            payload = request.get_json() or {}
            gold_items = payload.get('gold', [])
            silver_items = payload.get('silver', [])
            
            updated_gold = []
            updated_silver = []
            
            # Update Gold holdings
            for item in gold_items:
                purity = str(item.get('purity', '')).upper()
                if '24' in purity and rates.get('gold_24k'):
                    item['current_price_per_gram'] = rates['gold_24k']
                elif '22' in purity and rates.get('gold_22k'):
                    item['current_price_per_gram'] = rates['gold_22k']
                elif '18' in purity and rates.get('gold_18k'):
                    item['current_price_per_gram'] = rates['gold_18k']
                updated_gold.append(item)
            
            # Update Silver holdings
            for item in silver_items:
                purity = str(item.get('purity', '')).upper()
                if rates.get('silver'):
                    if '999' in purity:
                        item['current_price_per_gram'] = rates['silver']
                    elif '925' in purity:
                        item['current_price_per_gram'] = int(rates['silver'] * 0.925)
                    else:
                        item['current_price_per_gram'] = rates['silver']
                updated_silver.append(item)
            
            return jsonify({
                'success': True,
                'message': f'Updated {len(updated_gold)} gold and {len(updated_silver)} silver items',
                'gold': updated_gold,
                'silver': updated_silver,
                'rates': rates
            })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})


@app.route('/api/export-excel', methods=['POST'])
def api_export_excel():
    """Export data to Excel file"""
    try:
        if is_firebase_mode():
            # Firebase mode: export from database
            data = get_all_firebase_data()
        else:
            # Browser mode: export provided data
            data = request.get_json() or {}
        
        output = io.BytesIO()
        
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            if not data:
                pd.DataFrame().to_excel(writer, sheet_name='Summary', index=False)
            else:
                for sheet_name, records in data.items():
                    if records:
                        df = pd.DataFrame(records)
                        df.to_excel(writer, sheet_name=sheet_name, index=False)
                    else:
                        pd.DataFrame().to_excel(writer, sheet_name=sheet_name, index=False)
        
        output.seek(0)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        return send_file(
            output,
            as_attachment=True,
            download_name=f'truwealthily_backup_{timestamp}.xlsx',
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@app.route('/api/import-excel', methods=['POST'])
def api_import_excel():
    """Import data from Excel file"""
    if 'file' not in request.files:
        return jsonify({'success': False, 'message': 'No file uploaded'})
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'success': False, 'message': 'No file selected'})
    
    if not file.filename.endswith('.xlsx'):
        return jsonify({'success': False, 'message': 'Please upload a valid Excel (.xlsx) file'})
    
    try:
        wb = pd.ExcelFile(file)
        all_data = {}
        
        for sheet_name in wb.sheet_names:
            df = pd.read_excel(wb, sheet_name=sheet_name)
            
            if is_firebase_mode():
                # Firebase mode: save to database
                save_data(sheet_name, df)
            
            if not df.empty:
                records = df.to_dict('records')
                for record in records:
                    for k, v in record.items():
                        if pd.isna(v):
                            record[k] = None
                all_data[sheet_name] = records
            else:
                all_data[sheet_name] = []
        
        return jsonify({'success': True, 'message': 'Data imported successfully', 'data': all_data})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})


# ============================================================================
# FIREBASE-ONLY API ENDPOINTS - CRUD operations for Firebase mode
# ============================================================================

@app.route('/api/firebase/add-item', methods=['POST'])
def api_firebase_add_item():
    """Add item - Firebase mode only"""
    if not is_firebase_mode():
        return jsonify({'success': False, 'message': 'Not in Firebase mode'})
    
    try:
        payload = request.get_json()
        sheet_name = payload.get('sheet_name')
        item = payload.get('item')
        
        if not sheet_name or not item:
            return jsonify({'success': False, 'message': 'Missing sheet_name or item'})
        
        df = get_data(sheet_name)
        new_df = pd.DataFrame([item])
        df = pd.concat([df, new_df], ignore_index=True)
        save_data(sheet_name, df)
        
        return jsonify({'success': True, 'message': 'Item added successfully'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})


@app.route('/api/firebase/update-item', methods=['POST'])
def api_firebase_update_item():
    """Update item - Firebase mode only"""
    if not is_firebase_mode():
        return jsonify({'success': False, 'message': 'Not in Firebase mode'})
    
    try:
        payload = request.get_json()
        sheet_name = payload.get('sheet_name')
        row_index = payload.get('row_index')
        item = payload.get('item')
        
        if sheet_name is None or row_index is None or not item:
            return jsonify({'success': False, 'message': 'Missing parameters'})
        
        df = get_data(sheet_name)
        if row_index >= len(df):
            return jsonify({'success': False, 'message': 'Item not found'})
        
        for key, value in item.items():
            df.at[row_index, key] = value
        
        save_data(sheet_name, df)
        return jsonify({'success': True, 'message': 'Item updated successfully'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})


@app.route('/api/firebase/delete-item', methods=['POST'])
def api_firebase_delete_item():
    """Delete item - Firebase mode only"""
    if not is_firebase_mode():
        return jsonify({'success': False, 'message': 'Not in Firebase mode'})
    
    try:
        payload = request.get_json()
        sheet_name = payload.get('sheet_name')
        row_index = payload.get('row_index')
        
        if sheet_name is None or row_index is None:
            return jsonify({'success': False, 'message': 'Missing parameters'})
        
        df = get_data(sheet_name)
        if row_index >= len(df):
            return jsonify({'success': False, 'message': 'Item not found'})
        
        df = df.drop(df.index[row_index]).reset_index(drop=True)
        save_data(sheet_name, df)
        
        return jsonify({'success': True, 'message': 'Item deleted successfully'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})


@app.route('/api/firebase/get-data')
def api_firebase_get_data():
    """Get all data - Firebase mode only"""
    if not is_firebase_mode():
        return jsonify({'success': False, 'message': 'Not in Firebase mode'})
    
    try:
        all_data = get_all_firebase_data()
        return jsonify({'success': True, 'data': all_data})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})


if __name__ == '__main__':
    app.run(debug=True)
