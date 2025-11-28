#!/usr/bin/env python3
"""
CLI интерфейс для управления грантовыми средствами через смарт-контракты
"""
import click
import os
import json
from datetime import datetime, timedelta
from dotenv import load_dotenv
from src.compiler import ContractCompiler
from src.deployer import ContractDeployer
from src.grant_manager import GrantManagerClient


load_dotenv()


@click.group()
def cli():
    """Инструмент для управления грантовыми средствами через смарт-контракты"""
    pass


@cli.command()
@click.option('--contract', default='GrantManager', help='Имя контракта для компиляции')
@click.option('--all', is_flag=True, help='Скомпилировать все контракты')
@click.option('--skip-install', is_flag=True, help='Пропустить автоматическую установку solc')
def compile(contract, all, skip_install):
    """Компиляция Solidity контрактов"""
    try:
        click.echo("Initializing compiler...")
        compiler = ContractCompiler(skip_install=skip_install)
        
        if all:
            click.echo("Compiling all contracts...")
            compiler.compile_all()
        else:
            click.echo(f"Compiling {contract}...")
            compiler.compile_contract(contract)
        
        click.echo("\n✓ Compilation completed!")
    except KeyboardInterrupt:
        click.echo("\n✗ Compilation cancelled by user", err=True)
        click.echo("\nTip: Install solc manually to avoid hanging:")
        click.echo("  macOS: brew install solidity")
        click.echo("  Linux: sudo apt-get install solc")
        raise click.Abort()
    except Exception as e:
        click.echo(f"\n✗ Error: {e}", err=True)
        raise click.Abort()


@cli.command()
@click.option('--min-approvals', default=1, help='Минимальное количество одобрений')
@click.option('--rpc-url', help='RPC URL (переопределяет .env)')
@click.option('--private-key', help='Приватный ключ (переопределяет .env)')
def deploy(min_approvals, rpc_url, private_key):
    """Развертывание контракта GrantManager"""
    try:
        deployer = ContractDeployer(rpc_url=rpc_url, private_key=private_key)
        result = deployer.deploy_grant_manager(min_approvals)
        
        click.echo("\n" + "="*50)
        click.echo("✓ Contract deployed successfully!")
        click.echo(f"Address: {result['address']}")
        click.echo(f"Transaction: {result['tx_hash']}")
        click.echo("="*50)
        
        # Сохранение адреса контракта
        config = {'contract_address': result['address']}
        with open('contract_config.json', 'w') as f:
            json.dump(config, f, indent=2)
        
        click.echo("\nContract address saved to contract_config.json")
        
    except Exception as e:
        click.echo(f"✗ Error: {e}", err=True)
        raise click.Abort()


@cli.command()
@click.option('--address', help='Адрес контракта (переопределяет contract_config.json)')
@click.option('--rpc-url', help='RPC URL (переопределяет .env)')
@click.option('--private-key', help='Приватный ключ (переопределяет .env)')
def balance(address, rpc_url, private_key):
    """Просмотр баланса контракта"""
    contract_address = address or _get_contract_address()
    
    try:
        client = GrantManagerClient(contract_address, rpc_url, private_key)
        balance = client.get_contract_balance()
        click.echo(f"Contract balance: {balance} ETH")
    except Exception as e:
        click.echo(f"✗ Error: {e}", err=True)


@cli.command()
@click.option('--amount', type=float, required=True, help='Сумма для пополнения в ETH')
@click.option('--address', help='Адрес контракта')
@click.option('--rpc-url', help='RPC URL')
@click.option('--private-key', help='Приватный ключ')
def deposit(amount, address, rpc_url, private_key):
    """Пополнение контракта средствами"""
    contract_address = address or _get_contract_address()
    
    try:
        client = GrantManagerClient(contract_address, rpc_url, private_key)
        result = client.deposit(amount)
        
        if result['status'] == 'success':
            click.echo(f"✓ Deposited {amount} ETH successfully!")
            click.echo(f"Transaction: {result['tx_hash']}")
        else:
            click.echo("✗ Deposit failed", err=True)
    except Exception as e:
        click.echo(f"✗ Error: {e}", err=True)


@cli.command()
@click.option('--recipient', required=True, help='Адрес получателя')
@click.option('--amount', type=float, required=True, help='Сумма гранта в ETH')
@click.option('--description', required=True, help='Описание гранта')
@click.option('--days', type=int, default=90, help='Срок выполнения в днях')
@click.option('--no-approval', is_flag=True, help='Не требовать одобрения')
@click.option('--address', help='Адрес контракта')
@click.option('--rpc-url', help='RPC URL')
@click.option('--private-key', help='Приватный ключ')
def create_grant(recipient, amount, description, days, no_approval, address, rpc_url, private_key):
    """Создание нового гранта"""
    contract_address = address or _get_contract_address()
    deadline = int((datetime.now() + timedelta(days=days)).timestamp())
    
    try:
        client = GrantManagerClient(contract_address, rpc_url, private_key)
        result = client.create_grant(
            recipient=recipient,
            amount=amount,
            description=description,
            deadline=deadline,
            requires_approval=not no_approval
        )
        
        if result['status'] == 'success':
            click.echo(f"✓ Grant created successfully!")
            click.echo(f"Grant ID: {result['grant_id']}")
            click.echo(f"Transaction: {result['tx_hash']}")
        else:
            click.echo("✗ Grant creation failed", err=True)
    except Exception as e:
        click.echo(f"✗ Error: {e}", err=True)


@cli.command()
@click.option('--grant-id', type=int, required=True, help='ID гранта')
@click.option('--address', help='Адрес контракта')
@click.option('--rpc-url', help='RPC URL')
@click.option('--private-key', help='Приватный ключ')
def approve(grant_id, address, rpc_url, private_key):
    """Одобрение гранта"""
    contract_address = address or _get_contract_address()
    
    try:
        client = GrantManagerClient(contract_address, rpc_url, private_key)
        result = client.approve_grant(grant_id)
        
        if result['status'] == 'success':
            click.echo(f"✓ Grant {grant_id} approved successfully!")
            click.echo(f"Transaction: {result['tx_hash']}")
        else:
            click.echo("✗ Approval failed", err=True)
    except Exception as e:
        click.echo(f"✗ Error: {e}", err=True)


@cli.command()
@click.option('--grant-id', type=int, required=True, help='ID гранта')
@click.option('--amount', type=float, required=True, help='Сумма для выделения в ETH')
@click.option('--address', help='Адрес контракта')
@click.option('--rpc-url', help='RPC URL')
@click.option('--private-key', help='Приватный ключ')
def allocate(grant_id, amount, address, rpc_url, private_key):
    """Выделение средств для гранта"""
    contract_address = address or _get_contract_address()
    
    try:
        client = GrantManagerClient(contract_address, rpc_url, private_key)
        result = client.allocate_funds(grant_id, amount)
        
        if result['status'] == 'success':
            click.echo(f"✓ Allocated {amount} ETH to grant {grant_id}")
            click.echo(f"Transaction: {result['tx_hash']}")
        else:
            click.echo("✗ Allocation failed", err=True)
    except Exception as e:
        click.echo(f"✗ Error: {e}", err=True)


@cli.command()
@click.option('--grant-id', type=int, required=True, help='ID гранта')
@click.option('--amount', type=float, required=True, help='Сумма для выпуска в ETH')
@click.option('--address', help='Адрес контракта')
@click.option('--rpc-url', help='RPC URL')
@click.option('--private-key', help='Приватный ключ')
def release(grant_id, amount, address, rpc_url, private_key):
    """Выпуск средств получателю"""
    contract_address = address or _get_contract_address()
    
    try:
        client = GrantManagerClient(contract_address, rpc_url, private_key)
        result = client.release_funds(grant_id, amount)
        
        if result['status'] == 'success':
            click.echo(f"✓ Released {amount} ETH to grant {grant_id} recipient")
            click.echo(f"Transaction: {result['tx_hash']}")
        else:
            click.echo("✗ Release failed", err=True)
    except Exception as e:
        click.echo(f"✗ Error: {e}", err=True)


@cli.command()
@click.option('--grant-id', type=int, required=True, help='ID гранта')
@click.option('--address', help='Адрес контракта')
@click.option('--rpc-url', help='RPC URL')
def info(grant_id, address, rpc_url):
    """Просмотр информации о гранте"""
    contract_address = address or _get_contract_address()
    
    try:
        client = GrantManagerClient(contract_address, rpc_url, None)
        grant = client.get_grant(grant_id)
        
        click.echo("\n" + "="*50)
        click.echo(f"Grant ID: {grant['id']}")
        click.echo(f"Recipient: {grant['recipient']}")
        click.echo(f"Amount: {grant['amount']} ETH")
        click.echo(f"Allocated: {grant['allocated_amount']} ETH")
        click.echo(f"Released: {grant['released_amount']} ETH")
        click.echo(f"Status: {grant['status']}")
        click.echo(f"Description: {grant['description']}")
        click.echo(f"Created: {grant['created_at']}")
        click.echo(f"Deadline: {grant['deadline']}")
        click.echo(f"Requires Approval: {grant['requires_approval']}")
        click.echo(f"Approval Count: {grant['approval_count']}")
        click.echo("="*50)
    except Exception as e:
        click.echo(f"✗ Error: {e}", err=True)


@cli.command()
@click.option('--limit', type=int, default=10, help='Максимальное количество грантов')
@click.option('--address', help='Адрес контракта')
@click.option('--rpc-url', help='RPC URL')
def list(limit, address, rpc_url):
    """Список всех грантов"""
    contract_address = address or _get_contract_address()
    
    try:
        client = GrantManagerClient(contract_address, rpc_url, None)
        grants = client.list_grants(limit)
        
        if not grants:
            click.echo("No grants found")
            return
        
        click.echo(f"\nFound {len(grants)} grant(s):\n")
        for grant in grants:
            click.echo(f"Grant #{grant['id']}: {grant['description'][:50]}...")
            click.echo(f"  Recipient: {grant['recipient']}")
            click.echo(f"  Amount: {grant['amount']} ETH | Status: {grant['status']}")
            click.echo()
    except Exception as e:
        click.echo(f"✗ Error: {e}", err=True)


def _get_contract_address():
    """Получение адреса контракта из конфигурационного файла"""
    if os.path.exists('contract_config.json'):
        with open('contract_config.json', 'r') as f:
            config = json.load(f)
            return config.get('contract_address')
    else:
        click.echo("✗ Contract address not found. Please deploy a contract first or use --address", err=True)
        raise click.Abort()


if __name__ == '__main__':
    cli()

