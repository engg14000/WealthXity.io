from flask import render_template, request, redirect, url_for, flash, send_file, jsonify
import json
from portfolio_manager import app, database
from portfolio_manager.models import (
    get_model_class, get_model_fields, get_sheet_name,
    MODEL_DISPLAY_NAMES, MODEL_SHORT_CODES, DEFAULT_RETURNS
)
from portfolio_manager import api_services
from portfolio_manager.storage import get_config, save_config, set_storage_mode, export_to_excel, import_from_excel, load_browser_data, export_browser_data, is_browser_storage
import pandas as pd
import os
from datetime import datetime

# App Configuration
APP_NAME = "WealthXity"
APP_TAGLINE = "Your Wealth, Simplified"
app.secret_key = 'wealthpulse_secret_key_change_in_production'

# Make app name available in all templates
@app.context_processor
def inject_app_info():
    config = get_config()
    return {
        'app_name': APP_NAME,
        'app_tagline': APP_TAGLINE,
        'storage_mode': config.get('storage_mode', 'excel')
    }

def calculate_portfolio_summary():
    """Calculate comprehensive portfolio summary including all asset types"""
    sheet_names = database.get_sheet_names()
    
    summary = {
        'mutual_funds': 0,
        'stocks': 0,
        'real_estate': 0,
        'gold': 0,
        'silver': 0,
        'bank_balance': 0,
        'fixed_deposits': 0,
        'nps': 0,
        'ppf': 0,
        'epf': 0,
        'insurance_cover': 0,
        'credit_card_outstanding': 0,
        'loans_outstanding': 0,
        'total_assets': 0,
        'total_liabilities': 0,
        'net_worth': 0,
    }
    
    all_data = {}
    
    for sheet in sheet_names:
        if sheet == 'Summary' or sheet == 'Net Worth History':
            continue
        df = database.get_data(sheet)
        if not df.empty:
            all_data[sheet] = df.to_dict('records')
            
            if sheet == 'Mutual Funds':
                for _, row in df.iterrows():
                    try:
                        summary['mutual_funds'] += float(row.get('units', 0)) * float(row.get('current_nav', 0))
                    except (ValueError, TypeError):
                        pass
            elif sheet == 'Stocks':
                for _, row in df.iterrows():
                    try:
                        summary['stocks'] += float(row.get('quantity', 0)) * float(row.get('current_price', 0))
                    except (ValueError, TypeError):
                        pass
            elif sheet == 'Real Estate':
                for _, row in df.iterrows():
                    try:
                        summary['real_estate'] += float(row.get('current_value', 0)) - float(row.get('loan_outstanding', 0))
                    except (ValueError, TypeError):
                        pass
            elif sheet == 'Gold':
                for _, row in df.iterrows():
                    try:
                        summary['gold'] += float(row.get('weight_grams', 0)) * float(row.get('current_price_per_gram', 0))
                    except (ValueError, TypeError):
                        pass
            elif sheet == 'Silver':
                for _, row in df.iterrows():
                    try:
                        summary['silver'] += float(row.get('weight_grams', 0)) * float(row.get('current_price_per_gram', 0))
                    except (ValueError, TypeError):
                        pass
            elif sheet == 'Bank Accounts':
                summary['bank_balance'] += df['balance'].astype(float).sum() if 'balance' in df.columns else 0
            elif sheet == 'Fixed Deposits':
                summary['fixed_deposits'] += df['principal_amount'].astype(float).sum() if 'principal_amount' in df.columns else 0
            elif sheet == 'NPS Accounts':
                if 'tier1_balance' in df.columns:
                    summary['nps'] += df['tier1_balance'].astype(float).sum()
                if 'tier2_balance' in df.columns:
                    summary['nps'] += df['tier2_balance'].astype(float).sum()
            elif sheet == 'PPF':
                summary['ppf'] += df['current_balance'].astype(float).sum() if 'current_balance' in df.columns else 0
            elif sheet == 'EPF':
                summary['epf'] += df['total_balance'].astype(float).sum() if 'total_balance' in df.columns else 0
            elif sheet == 'Insurance Policies':
                summary['insurance_cover'] += df['sum_assured'].astype(float).sum() if 'sum_assured' in df.columns else 0
            elif sheet == 'Credit Cards':
                summary['credit_card_outstanding'] += df['outstanding_balance'].astype(float).sum() if 'outstanding_balance' in df.columns else 0
            elif sheet == 'Loans':
                summary['loans_outstanding'] += df['outstanding_amount'].astype(float).sum() if 'outstanding_amount' in df.columns else 0
    
    # Calculate totals
    summary['total_assets'] = (
        summary['mutual_funds'] + summary['stocks'] + summary['real_estate'] +
        summary['gold'] + summary['silver'] + summary['bank_balance'] +
        summary['fixed_deposits'] + summary['nps'] + summary['ppf'] + summary['epf']
    )
    summary['total_liabilities'] = summary['loans_outstanding'] + summary['credit_card_outstanding']
    summary['net_worth'] = summary['total_assets'] - summary['total_liabilities']
    
    return summary, all_data

@app.route('/')
def index():
    """Dashboard view showing all portfolio data with summary"""
    summary, all_data = calculate_portfolio_summary()
    
    # Get net worth history for chart
    history_df = database.get_data('Net Worth History')
    networth_history = history_df.to_dict('records') if not history_df.empty else []
    
    return render_template('index.html', 
                         all_data=all_data, 
                         summary=summary,
                         networth_history=networth_history,
                         model_types=MODEL_SHORT_CODES,
                         display_names=MODEL_DISPLAY_NAMES)

@app.route('/add', methods=['GET', 'POST'])
def add_item():
    """Add a new item to the portfolio"""
    item_type = request.args.get('type') or request.form.get('type')
    fields = []
    
    if item_type:
        fields = get_model_fields(item_type)

    if request.method == 'POST' and fields and request.form.get(fields[0]):
        sheet_name = get_sheet_name(item_type)
        data = {field: request.form.get(field, '') for field in fields}
        
        df = database.get_data(sheet_name)
        new_df = pd.DataFrame([data])
        df = pd.concat([df, new_df], ignore_index=True)
        database.save_data(sheet_name, df)
        
        flash(f'Successfully added new {sheet_name.rstrip("s")}!', 'success')
        return redirect(url_for('index'))

    return render_template('add.html', 
                         type=item_type, 
                         fields=fields,
                         model_types=MODEL_SHORT_CODES,
                         display_names=MODEL_DISPLAY_NAMES)

@app.route('/view/<item_type>')
def view_items(item_type):
    """View all items of a specific type"""
    sheet_name = get_sheet_name(item_type)
    df = database.get_data(sheet_name)
    items = df.to_dict('records') if not df.empty else []
    
    return render_template('view.html',
                         item_type=item_type,
                         sheet_name=sheet_name,
                         items=items,
                         model_types=MODEL_SHORT_CODES,
                         display_names=MODEL_DISPLAY_NAMES)

@app.route('/edit/<item_type>/<int:row_index>', methods=['GET', 'POST'])
def edit_item(item_type, row_index):
    """Edit an existing item"""
    sheet_name = get_sheet_name(item_type)
    df = database.get_data(sheet_name)
    
    if row_index >= len(df):
        flash('Item not found!', 'error')
        return redirect(url_for('index'))
    
    item = df.iloc[row_index].to_dict()
    fields = get_model_fields(item_type)

    if request.method == 'POST':
        for field in fields:
            if field in request.form:
                df.at[row_index, field] = request.form[field]
        
        database.save_data(sheet_name, df)
        flash(f'Successfully updated {sheet_name.rstrip("s")}!', 'success')
        return redirect(url_for('view_items', item_type=item_type))

    return render_template('edit.html', 
                         item_type=item_type, 
                         item=item,
                         row_index=row_index,
                         fields=fields,
                         model_types=MODEL_SHORT_CODES,
                         display_names=MODEL_DISPLAY_NAMES)

@app.route('/delete/<item_type>/<int:row_index>')
def delete_item(item_type, row_index):
    """Delete an item"""
    sheet_name = get_sheet_name(item_type)
    df = database.get_data(sheet_name)
    
    if row_index < len(df):
        df = df.drop(df.index[row_index]).reset_index(drop=True)
        database.save_data(sheet_name, df)
        flash(f'Successfully deleted item!', 'success')
    else:
        flash('Item not found!', 'error')
    
    return redirect(url_for('view_items', item_type=item_type))

@app.route('/backup')
def backup_data():
    """Download the Excel file as backup"""
    data_file = database.DATA_FILE
    if os.path.exists(data_file):
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        return send_file(
            os.path.abspath(data_file),
            as_attachment=True,
            download_name=f'portfolio_backup_{timestamp}.xlsx'
        )
    flash('No data file found to backup!', 'error')
    return redirect(url_for('index'))

@app.route('/import', methods=['GET', 'POST'])
def import_data():
    """Import data from an uploaded Excel file"""
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('No file uploaded!', 'error')
            return redirect(url_for('index'))
        
        file = request.files['file']
        if file.filename == '':
            flash('No file selected!', 'error')
            return redirect(url_for('index'))
        
        if file and file.filename.endswith('.xlsx'):
            # Save uploaded file
            file.save(database.DATA_FILE)
            flash('Data imported successfully!', 'success')
        else:
            flash('Please upload a valid Excel (.xlsx) file!', 'error')
        
        return redirect(url_for('index'))
    
    return render_template('import.html',
                         model_types=MODEL_SHORT_CODES,
                         display_names=MODEL_DISPLAY_NAMES)

@app.route('/networth')
def networth_tracker():
    """Net worth history tracking page"""
    summary, _ = calculate_portfolio_summary()
    
    # Get historical data
    history_df = database.get_data('Net Worth History')
    history = history_df.to_dict('records') if not history_df.empty else []
    
    return render_template('networth.html',
                         summary=summary,
                         history=history,
                         model_types=MODEL_SHORT_CODES,
                         display_names=MODEL_DISPLAY_NAMES)

@app.route('/networth/snapshot', methods=['POST'])
def save_networth_snapshot():
    """Save current net worth as a monthly snapshot"""
    summary, _ = calculate_portfolio_summary()
    
    # Create snapshot record
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
    
    # Save to history sheet
    df = database.get_data('Net Worth History')
    new_df = pd.DataFrame([snapshot])
    df = pd.concat([df, new_df], ignore_index=True)
    database.save_data('Net Worth History', df)
    
    flash('Net worth snapshot saved successfully!', 'success')
    return redirect(url_for('networth_tracker'))

@app.route('/networth/delete/<int:row_index>')
def delete_networth_record(row_index):
    """Delete a single net worth history record"""
    df = database.get_data('Net Worth History')
    
    if row_index < len(df):
        df = df.drop(df.index[row_index]).reset_index(drop=True)
        database.save_data('Net Worth History', df)
        flash('Record deleted successfully!', 'success')
    else:
        flash('Record not found!', 'error')
    
    return redirect(url_for('networth_tracker'))

@app.route('/networth/purge', methods=['POST'])
def purge_networth_history():
    """Delete all net worth history records"""
    database.save_data('Net Worth History', pd.DataFrame())
    flash('All history records purged successfully!', 'success')
    return redirect(url_for('networth_tracker'))

@app.route('/forecast')
def forecast():
    """Future value forecast page"""
    summary, all_data = calculate_portfolio_summary()
    
    # Build assets dictionary for forecasting
    assets = {}
    
    # Mutual Funds
    if summary['mutual_funds'] > 0:
        mf_df = database.get_data('Mutual Funds')
        avg_return = DEFAULT_RETURNS['mutual_fund_equity']
        if not mf_df.empty and 'expected_return' in mf_df.columns:
            try:
                avg_return = mf_df['expected_return'].astype(float).mean()
            except:
                pass
        assets['Mutual Funds'] = {'value': summary['mutual_funds'], 'expected_return': avg_return}
    
    # Stocks
    if summary['stocks'] > 0:
        stock_df = database.get_data('Stocks')
        avg_return = DEFAULT_RETURNS['stocks']
        if not stock_df.empty and 'expected_return' in stock_df.columns:
            try:
                avg_return = stock_df['expected_return'].astype(float).mean()
            except:
                pass
        assets['Stocks'] = {'value': summary['stocks'], 'expected_return': avg_return}
    
    # Real Estate
    if summary['real_estate'] > 0:
        re_df = database.get_data('Real Estate')
        avg_return = DEFAULT_RETURNS['real_estate']
        if not re_df.empty and 'appreciation_rate' in re_df.columns:
            try:
                avg_return = re_df['appreciation_rate'].astype(float).mean()
            except:
                pass
        assets['Real Estate'] = {'value': summary['real_estate'], 'expected_return': avg_return}
    
    # Gold
    if summary['gold'] > 0:
        gold_df = database.get_data('Gold')
        avg_return = DEFAULT_RETURNS['gold']
        if not gold_df.empty and 'expected_return' in gold_df.columns:
            try:
                avg_return = gold_df['expected_return'].astype(float).mean()
            except:
                pass
        assets['Gold'] = {'value': summary['gold'], 'expected_return': avg_return}
    
    # Silver
    if summary['silver'] > 0:
        silver_df = database.get_data('Silver')
        avg_return = DEFAULT_RETURNS['silver']
        if not silver_df.empty and 'expected_return' in silver_df.columns:
            try:
                avg_return = silver_df['expected_return'].astype(float).mean()
            except:
                pass
        assets['Silver'] = {'value': summary['silver'], 'expected_return': avg_return}
    
    # Bank Balance (use FD rate or savings rate)
    if summary['bank_balance'] > 0:
        assets['Bank Balance'] = {'value': summary['bank_balance'], 'expected_return': DEFAULT_RETURNS['savings']}
    
    # NPS
    if summary['nps'] > 0:
        nps_df = database.get_data('NPS Accounts')
        avg_return = DEFAULT_RETURNS['nps']
        if not nps_df.empty and 'expected_return' in nps_df.columns:
            try:
                avg_return = nps_df['expected_return'].astype(float).mean()
            except:
                pass
        assets['NPS'] = {'value': summary['nps'], 'expected_return': avg_return}
    
    # PPF
    if summary['ppf'] > 0:
        assets['PPF'] = {'value': summary['ppf'], 'expected_return': DEFAULT_RETURNS['ppf']}
    
    # EPF
    if summary['epf'] > 0:
        assets['EPF'] = {'value': summary['epf'], 'expected_return': DEFAULT_RETURNS['epf']}
    
    # Generate forecast
    forecast_years = int(request.args.get('years', 10))
    projections = api_services.generate_forecast(assets, forecast_years)
    
    return render_template('forecast.html',
                         summary=summary,
                         assets=assets,
                         projections=projections,
                         forecast_years=forecast_years,
                         default_returns=DEFAULT_RETURNS,
                         model_types=MODEL_SHORT_CODES,
                         display_names=MODEL_DISPLAY_NAMES)

@app.route('/api/update-mf-nav', methods=['POST'])
def update_mf_nav():
    """API endpoint to update mutual fund NAVs from MFAPI"""
    try:
        df = database.get_data('Mutual Funds')
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
        
        database.save_data('Mutual Funds', df)
        return jsonify({'success': True, 'message': f'Updated {updated_count} mutual fund NAVs'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/search-mf')
def search_mf():
    """API endpoint to search mutual funds"""
    query = request.args.get('q', '')
    if not query or len(query) < 3:
        return jsonify([])
    
    results = api_services.search_mutual_funds(query)
    return jsonify(results[:20])  # Return top 20 results

@app.route('/api/get-mf-nav/<scheme_code>')
def get_mf_nav(scheme_code):
    """API endpoint to get NAV for a specific mutual fund"""
    nav_data = api_services.get_mutual_fund_nav(scheme_code)
    if nav_data:
        return jsonify(nav_data)
    return jsonify({'error': 'Unable to fetch NAV'}), 404

@app.route('/api/metal-prices')
def get_metal_prices():
    """API endpoint to get current gold and silver prices"""
    gold_price = api_services.get_gold_price()
    silver_price = api_services.get_silver_price()
    return jsonify({
        'gold': gold_price,
        'silver': silver_price
    })

@app.route('/settings')
def settings():
    """Settings page for storage and app configuration"""
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
        # Get Firebase configuration
        firebase_config = {
            'service_account_path': request.form.get('firebase_service_account_path', ''),
            'user_id': request.form.get('firebase_user_id', 'default_user'),
        }
        
        # Handle file upload for service account
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

@app.route('/settings/export-excel')
def export_data_excel():
    """Export all data to Excel file"""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    export_path = os.path.join('data', f'wealthpulse_export_{timestamp}.xlsx')
    
    try:
        export_to_excel(export_path)
        return send_file(
            os.path.abspath(export_path),
            as_attachment=True,
            download_name=f'wealthpulse_export_{timestamp}.xlsx'
        )
    except Exception as e:
        flash(f'Export failed: {str(e)}', 'error')
        return redirect(url_for('settings'))

@app.route('/settings/import-excel', methods=['POST'])
def import_data_excel():
    """Import data from Excel file"""
    if 'file' not in request.files:
        flash('No file uploaded!', 'error')
        return redirect(url_for('settings'))
    
    file = request.files['file']
    if file.filename == '':
        flash('No file selected!', 'error')
        return redirect(url_for('settings'))
    
    if file and file.filename.endswith('.xlsx'):
        try:
            # Save temporarily
            temp_path = os.path.join('data', 'temp_import.xlsx')
            file.save(temp_path)
            
            # Import data
            import_from_excel(temp_path)
            
            # Clean up
            os.remove(temp_path)
            
            flash('Data imported successfully!', 'success')
        except Exception as e:
            flash(f'Import failed: {str(e)}', 'error')
    else:
        flash('Please upload a valid Excel (.xlsx) file!', 'error')
    
    return redirect(url_for('settings'))

@app.route('/settings/sync-to-firebase', methods=['POST'])
def sync_to_firebase():
    """Sync local Excel data to Firebase"""
    config = get_config()
    if config.get('storage_mode') != 'firebase':
        flash('Firebase is not configured!', 'error')
        return redirect(url_for('settings'))
    
    try:
        # Export current data to temp file
        temp_path = os.path.join('data', 'temp_sync.xlsx')
        export_to_excel(temp_path)
        
        # Import to Firebase
        import_from_excel(temp_path)
        
        # Clean up
        os.remove(temp_path)
        
        flash('Data synced to Firebase successfully!', 'success')
    except Exception as e:
        flash(f'Sync failed: {str(e)}', 'error')
    
    return redirect(url_for('settings'))


# Browser Storage API Endpoints
@app.route('/api/sync-data', methods=['POST'])
def sync_data_from_browser():
    """Receive data from browser localStorage and load into memory"""
    try:
        data = request.get_json()
        if data:
            load_browser_data(data)
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})


@app.route('/api/get-data')
def get_all_data_for_browser():
    """Export all data for browser localStorage"""
    try:
        data = export_browser_data()
        return jsonify({'success': True, 'data': data})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})


@app.route('/api/export-excel')
def export_excel_api():
    """Export all data as downloadable Excel file"""
    try:
        import io
        from openpyxl import Workbook
        
        output = io.BytesIO()
        
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            sheet_names = database.get_sheet_names()
            for sheet in sheet_names:
                df = database.get_data(sheet)
                if not df.empty:
                    df.to_excel(writer, sheet_name=sheet, index=False)
                else:
                    pd.DataFrame().to_excel(writer, sheet_name=sheet, index=False)
            
            if not sheet_names or len(sheet_names) == 0:
                pd.DataFrame().to_excel(writer, sheet_name='Summary', index=False)
        
        output.seek(0)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        return send_file(
            output,
            as_attachment=True,
            download_name=f'wealthily_backup_{timestamp}.xlsx',
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
    except Exception as e:
        flash(f'Export failed: {str(e)}', 'error')
        return redirect(url_for('settings'))


@app.route('/api/import-excel', methods=['POST'])
def import_excel_api():
    """Import data from Excel file"""
    if 'file' not in request.files:
        return jsonify({'success': False, 'message': 'No file uploaded'})
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'success': False, 'message': 'No file selected'})
    
    if file and file.filename.endswith('.xlsx'):
        try:
            wb = pd.ExcelFile(file)
            all_data = {}
            
            for sheet_name in wb.sheet_names:
                df = pd.read_excel(wb, sheet_name=sheet_name)
                database.save_data(sheet_name, df)
                
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
    
    return jsonify({'success': False, 'message': 'Please upload a valid Excel (.xlsx) file'})


if __name__ == '__main__':
    app.run(debug=True)
