import json
import sys


def extract_peers(genesis_file):
    try:
        with open(genesis_file, 'r') as file:
            genesis_data = json.load(file)
    except FileNotFoundError:
        print(f"Error: The file {genesis_file} does not exist.")
        sys.exit(1)
    except json.JSONDecodeError:
        print(f"Error: The file {genesis_file} is not a valid JSON.")
        sys.exit(1)

    peers = []
    for tx in genesis_data['app_state']['genutil']['gen_txs']:
        peers.append(tx['body']['memo'])
    return peers

if __name__ == "__main__":
    argv = sys.argv[1:]  # Exclude the script name

    if len(argv) != 1:
        print("Usage: genesis_extract_peers.py <genesis_file>")
        sys.exit(1)

    peers = extract_peers(argv[0])
    print(','.join(peers))
