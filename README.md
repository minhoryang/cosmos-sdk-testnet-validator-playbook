# Cosmos SDK Validator Playbook

An Ansible playbook for automated deployment and management of Cosmos SDK validator nodes. This tool simplifies the process of setting up multiple validator nodes for a private testnet or validator infrastructure.

## Prerequisites

### System Requirements

- **Control Machine**: macOS, Linux, or WSL2
- **Target Nodes**: Ubuntu LTS (18.04, 20.04, 22.04, or newer)
- **Python**: 3.12 or newer
- **Ansible**: Core version 2.12.0 or newer

### Network Requirements

- SSH access to all target nodes
- Port 26656 (P2P) open between validator nodes
- Port 26657 (RPC) accessible for status checks

## Installation

1. **Clone this repository:**
   ```bash
   git clone https://github.com/minhoryang/cosmos-sdk-testnet-validator-playbook
   cd cosmos_sdk_validator_playbook
   ```

2. **Install Python dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Verify Ansible installation:**
   ```bash
   ansible --version
   ```

## Configuration

### 1. Prepare Target Nodes

**On each target node:**
- Ensure Ubuntu LTS is installed
- Create a user with sudo privileges (typically `ubuntu`)
- Upload your SSH public key to `~/.ssh/authorized_keys`

**Example:**
```bash
# On your local machine
ssh-copy-id ubuntu@your-validator-node.com
```

### 2. Configure SSH Access

Update your local `~/.ssh/config` file for easier access:

```ssh-config
Host validator1
    HostName your-validator1.com
    User ubuntu
    IdentityFile ~/.ssh/your_private_key

Host validator2
    HostName your-validator2.com
    User ubuntu
    IdentityFile ~/.ssh/your_private_key
```

### 3. Update Inventory

Edit `inventory/hosts.yml` to include your validator nodes:

```yaml
---
validators:
  hosts:
    validator1:
      ansible_host: your-validator1.com
      ansible_user: ubuntu
    validator2:
      ansible_host: your-validator2.com
      ansible_user: ubuntu
    # Add more validators as needed
```

### 4. Verify Connectivity

Test the connection to all nodes:

```bash
ansible -i inventory validators -m ping
```

Expected output:
```
validator1 | SUCCESS => {
    "changed": false,
    "ping": "pong"
}
validator2 | SUCCESS => {
    "changed": false,
    "ping": "pong"
}
```

## Usage - `bootstrap_all_validators_at_once.yml` playbook

### Preparing Required Files

Before running the playbook, you need to prepare the necessary files:

#### 1. Download Gaia Binary

Download the appropriate `gaiad` binary for your target platform:

```bash
# For Linux AMD64 (most common for cloud servers)
wget https://github.com/cosmos/gaia/releases/download/v25.1.0/gaiad-v25.1.0-linux-amd64 \
     -O upload_files/bootstrap_all_validators_at_once/gaiad
```

#### 2. Prepare Configuration Patch (Optional)

If you need [custom configuration, place your diff file](./upload_files/bootstrap_all_validators_at_once/gaiad_config.sample.diff) at:
```
upload_files/bootstrap_all_validators_at_once/gaiad_config.sample.diff
```

### Running the Bootstrap Playbook

The main playbook sets up a complete validator network:

```bash
# Final connectivity check
ansible -i inventory validators -m ping

# Run the bootstrap playbook
ansible-playbook -i inventory playbooks/bootstrap_all_validators_at_once.yml
```

#### Required Variables

During execution, you'll be prompted for:

- **`config__chain_id`**: The chain identifier for your network (e.g., `my-testnet-1`)
- **`config__keyring_password`**: Password for the keyring (⚠️ **Store this securely!**)

Instead of being prompted interactively, you can provide these variables directly:

```bash
ansible-playbook -i inventory playbooks/bootstrap_all_validators_at_once.yml \
  -e config__chain_id="my-testnet-1" \
  -e config__keyring_password="your-secure-password"
```

#### What the Playbook Does

1. **Pre-flight Checks**: Verifies ports and directories
2. **Binary Deployment**: Copies `gaiad` binary to all nodes
3. **Network Configuration**: Sets up `/etc/hosts` entries
4. **Genesis Setup**: Initializes and configures genesis files
5. **Peer Discovery**: Automatically configures peer connections
6. **Service Setup**: Creates and starts systemd services

### Post-Deployment Verification

After successful deployment, verify your validators:

```bash
# Check service status
ansible -i inventory validators -a "systemctl status gaiad.service"

# Check node status
ansible -i inventory validators -a "./gaiad --home ./.gaiad status"

# Check connectivity
ansible -i inventory validators -a "curl -s http://localhost:26657/status | jq .result.node_info.network"
```

### Manual Verification Commands

You can also run these commands directly on each validator node:

```bash
# Service management
systemctl status gaiad.service
journalctl -u gaiad.service -f

# Node status and info
./gaiad status
curl http://localhost:26657/status | jq

# Stop/start service
sudo systemctl stop gaiad.service
sudo systemctl start gaiad.service
```

## Troubleshooting

### Common Issues and Solutions

#### 1. Connection Issues

**Problem**: `ansible -i inventory validators -m ping` fails
```
validator1 | UNREACHABLE! => {
    "changed": false,
    "msg": "Failed to connect to the host via ssh"
}
```

**Solutions**:
- Verify SSH connectivity: `ssh ubuntu@your-validator-node.com`
- Check SSH key authentication
- Ensure the `ansible_user` is correct in inventory
- Verify the node is accessible and running

#### 2. Port Already in Use

**Problem**: Playbook fails with "Port 26657 is already in use"

**Solutions**:
```bash
# Check what's using the port
sudo lsof -i :26657
sudo lsof -i :26656

# Stop existing gaiad service
sudo systemctl stop gaiad.service

# Kill any remaining processes
sudo pkill gaiad
```

#### 3. Directory Already Exists

**Problem**: "Gaiad configuration directory already exists"

**Solutions**:
```bash
# backup existing data
mv ~/.gaiad ~/.gaiad.backup.$(date +%Y%m%d_%H%M%S)

# Or Remove existing configuration (⚠️ This will delete all data!)
rm -rf ~/.gaiad
```

#### 4. Peer Connectivity Issues

**Problem**: Validators can't connect to each other

**Solutions**:
- Verify port 26656 is open between all validator nodes:
  ```bash
  # Test from validator1 to validator2
  nc validator2-ip 26656
  ```
- Check firewall rules:
  ```bash
  # Ubuntu UFW
  sudo ufw allow 26656
  sudo ufw allow 26657
  # ...
  ```
- Verify `/etc/hosts` entries are correct

#### 5. Service Won't Start

**Problem**: `systemctl status gaiad.service` shows failed state

**Solutions**:
```bash
# Check detailed logs
journalctl -u gaiad.service -n 50

# Common fixes:
# 1. Check binary permissions
chmod +x ~/gaiad

# 2. Verify home directory
ls -la ~/.gaiad/

# 3. Check configuration
~/gaiad --home ~/.gaiad config show
```

### Network Connectivity Checklist

Before running the playbook, ensure:

- [ ] SSH access works to all nodes
- [ ] DNS resolution works between nodes (or `/etc/hosts` is configured)
- [ ] No existing `gaiad` processes are running
- [ ] No existing `.gaiad` directories exist (or backed up)
- [ ] Port 26656 (P2P) is open between all validators

## Project Structure

```
cosmos_sdk_validator_playbook/
├── README.md                           # This documentation
├── requirements.txt                    # Python dependencies
├── inventory/
│   └── hosts.yml                      # Ansible inventory configuration
├── playbooks/
│   └── bootstrap_all_validators_at_once.yml  # Main bootstrap playbook
├── scripts/
│   └── bootstrap_all_validators_at_once/
│       ├── genesis_extract_peers.py   # Peer extraction utility
│       └── genesis_merger.py          # Genesis file merger
├── upload_files/
│   └── bootstrap_all_validators_at_once/
│       ├── gaiad                      # Gaia binary (download required)
│       └── gaiad_config.sample.diff   # Optional config patch
```

### Key Components

- **`inventory/hosts.yml`**: Defines your validator nodes and connection details
- **`playbooks/bootstrap_all_validators_at_once.yml`**: Main playbook that orchestrates the entire setup process
- **`scripts/`**: Python utilities for genesis file management and peer discovery
- **`upload_files/`**: Directory containing binaries and configuration files to be deployed
