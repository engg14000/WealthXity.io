from . import cli, database, models
import pandas as pd

def handle_add(args):
    """Handles the add command"""
    item_type = args.type
    sheet_name = f"{item_type.upper()}s"
    
    data = {k: v for k, v in vars(args).items() if k not in ['command', 'type'] and v is not None}
    
    df = database.get_data(sheet_name)
    
    # Create a new DataFrame from the new data
    new_df = pd.DataFrame([data])

    # Concatenate the old DataFrame with the new one
    df = pd.concat([df, new_df], ignore_index=True)
    
    database.save_data(sheet_name, df)
    print(f"Added {item_type.upper()} successfully.")

def handle_view(args):
    """Handles the view command"""
    item_type = args.type
    if item_type == 'all':
        sheet_names = database.get_sheet_names()
        if 'Summary' in sheet_names:
            sheet_names.remove('Summary') # Don't show summary
    else:
        sheet_names = [f"{item_type.upper()}s"]

    for sheet in sheet_names:
        df = database.get_data(sheet)
        if not df.empty:
            print(f"--- {sheet} ---")
            print(df.to_string())
            print()
        else:
            print(f"No data found for {sheet}")


def handle_update(args):
    """Handles the update command"""
    item_type = args.type
    sheet_name = f"{item_type.upper()}s"
    identifier = args.name

    df = database.get_data(sheet_name)
    if df.empty:
        print(f"No data found for {sheet_name}")
        return

    # For simplicity, we use the first column as the identifier
    identifier_col = df.columns[0]
    
    if identifier not in df[identifier_col].values:
        print(f"Error: Item '{identifier}' not found in {item_type.upper()}s.")
        return

    for key, value in vars(args).items():
        if key not in ['command', 'type', 'name'] and value is not None:
            df.loc[df[identifier_col] == identifier, key] = value
    
    database.save_data(sheet_name, df)
    print(f"Updated {item_type.upper()} '{identifier}' successfully.")

def handle_delete(args):
    """Handles the delete command"""
    item_type = args.type
    sheet_name = f"{item_type.upper()}s"
    identifier = args.name

    df = database.get_data(sheet_name)
    if df.empty:
        print(f"No data found for {sheet_name}")
        return
        
    # For simplicity, we use the first column as the identifier
    identifier_col = df.columns[0]

    if identifier not in df[identifier_col].values:
        print(f"Error: Item '{identifier}' not found in {item_type.upper()}s.")
        return

    df = df[df[identifier_col] != identifier]
    database.save_data(sheet_name, df)
    print(f"Deleted {item_type.upper()} '{identifier}' successfully.")

def main():
    """Main function"""
    parser = cli.get_parser()
    args = parser.parse_args()

    if args.command == 'add':
        handle_add(args)
    elif args.command == 'view':
        handle_view(args)
    elif args.command == 'update':
        handle_update(args)
    elif args.command == 'delete':
        handle_delete(args)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
