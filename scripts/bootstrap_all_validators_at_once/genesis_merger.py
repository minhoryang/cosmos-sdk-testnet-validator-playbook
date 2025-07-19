from heapq import merge
import os
import json
import glob


def merge_genesis(target_genesis_file="/workdir/config/genesis.json", gathered_genesis_directory="/workdir/gathered"):
    if not os.path.isfile(target_genesis_file):
        raise FileNotFoundError(f"Target genesis file '{target_genesis_file}' does not exist.")

    target_genesis_data = None
    with open(target_genesis_file, 'r') as f:
        target_genesis_data = json.load(f)

    supply = []
    supply.extend(target_genesis_data['app_state']['bank']['supply'])
    for genesis_file in glob.glob(os.path.join(gathered_genesis_directory, "*.json")):
        if not os.path.isfile(genesis_file):
            continue

        with open(genesis_file, 'r') as f:
            genesis_data = json.load(f)

        target_genesis_data['app_state']['auth']['accounts'].extend(genesis_data.get('app_state', {}).get('auth', {}).get('accounts', []))
        target_genesis_data['app_state']['bank']['balances'].extend(genesis_data.get('app_state', {}).get('bank', {}).get('balances', []))
        supply.extend(genesis_data.get('app_state', {}).get('bank', {}).get('supply', []))

    target_genesis_data['app_state']['bank']['supply'] = merge_supply(supply)
    with open(target_genesis_file, 'w') as f:
        json.dump(target_genesis_data, f, indent=2)

def merge_supply(supply):
    _ = {}
    for item in supply:
        denom = item['denom']
        amount = int(item['amount'])
        if denom in _:
            _[denom] += amount
        else:
            _[denom] = amount
    return [{"denom": denom, "amount": str(amount)} for denom, amount in _.items()]

if __name__ == "__main__":
    import sys
    argv = sys.argv[1:]  # Exclude the script name

    if len(argv) != 2:
        print("Usage: genesis_merger.py <genesis_file> <gathered_genesis_directory>")
        sys.exit(1)

    merge_genesis(argv[0], argv[1])
