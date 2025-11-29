-- Create enum types
DO $$ BEGIN
  CREATE TYPE userrole AS ENUM ('government', 'university', 'grantee');
EXCEPTION WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
  CREATE TYPE grantstate AS ENUM ('active', 'completed', 'cancelled');
EXCEPTION WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
  CREATE TYPE spendingrequeststatus AS ENUM ('pending_university_approval', 'pending_receipt', 'paid', 'rejected', 'blocked');
EXCEPTION WHEN duplicate_object THEN null;
END $$;

-- Create users table
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    email VARCHAR UNIQUE NOT NULL,
    password_hash VARCHAR NOT NULL,
    name VARCHAR NOT NULL,
    role userrole NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);

CREATE INDEX IF NOT EXISTS ix_users_email ON users(email);
CREATE INDEX IF NOT EXISTS ix_users_id ON users(id);
CREATE INDEX IF NOT EXISTS ix_users_role ON users(role);

-- Create grants table
CREATE TABLE IF NOT EXISTS grants (
    id SERIAL PRIMARY KEY,
    title VARCHAR NOT NULL,
    total_amount NUMERIC(18, 2) NOT NULL,
    amount_spent NUMERIC(18, 2) DEFAULT 0,
    university_id INTEGER NOT NULL REFERENCES users(id),
    state grantstate DEFAULT 'active',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);

CREATE INDEX IF NOT EXISTS ix_grants_id ON grants(id);
CREATE INDEX IF NOT EXISTS ix_grants_state ON grants(state);
CREATE INDEX IF NOT EXISTS ix_grants_title ON grants(title);
CREATE INDEX IF NOT EXISTS ix_grants_university_id ON grants(university_id);

-- Create spending_items table
CREATE TABLE IF NOT EXISTS spending_items (
    id SERIAL PRIMARY KEY,
    grant_id INTEGER NOT NULL REFERENCES grants(id),
    title VARCHAR NOT NULL,
    planned_amount NUMERIC(18, 2) NOT NULL,
    priority_index INTEGER NOT NULL
);

CREATE INDEX IF NOT EXISTS ix_spending_items_grant_id ON spending_items(grant_id);
CREATE INDEX IF NOT EXISTS ix_spending_items_id ON spending_items(id);
CREATE INDEX IF NOT EXISTS ix_spending_items_priority_index ON spending_items(priority_index);

-- Create spending_requests table
CREATE TABLE IF NOT EXISTS spending_requests (
    id SERIAL PRIMARY KEY,
    spending_item_id INTEGER NOT NULL REFERENCES spending_items(id),
    grantee_id INTEGER NOT NULL REFERENCES users(id),
    amount NUMERIC(18, 2) NOT NULL,
    status spendingrequeststatus DEFAULT 'pending_university_approval',
    aml_flags TEXT[],
    approved_by_university INTEGER REFERENCES users(id),
    paid_tx_hash VARCHAR,
    rejection_reason TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    updated_at TIMESTAMP WITH TIME ZONE
);

CREATE INDEX IF NOT EXISTS ix_spending_requests_grantee_id ON spending_requests(grantee_id);
CREATE INDEX IF NOT EXISTS ix_spending_requests_id ON spending_requests(id);
CREATE INDEX IF NOT EXISTS ix_spending_requests_paid_tx_hash ON spending_requests(paid_tx_hash);
CREATE INDEX IF NOT EXISTS ix_spending_requests_spending_item_id ON spending_requests(spending_item_id);
CREATE INDEX IF NOT EXISTS ix_spending_requests_status ON spending_requests(status);

-- Create transactions table
CREATE TABLE IF NOT EXISTS transactions (
    id SERIAL PRIMARY KEY,
    spending_request_id INTEGER REFERENCES spending_requests(id),
    source VARCHAR NOT NULL,
    destination VARCHAR NOT NULL,
    amount NUMERIC(18, 2) NOT NULL,
    currency VARCHAR,
    external_id VARCHAR,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);

CREATE INDEX IF NOT EXISTS ix_transactions_id ON transactions(id);
CREATE INDEX IF NOT EXISTS ix_transactions_spending_request_id ON transactions(spending_request_id);
CREATE INDEX IF NOT EXISTS ix_transactions_external_id ON transactions(external_id);

-- Create receipts table
CREATE TABLE IF NOT EXISTS receipts (
    id SERIAL PRIMARY KEY,
    spending_request_id INTEGER NOT NULL UNIQUE REFERENCES spending_requests(id),
    file_path VARCHAR NOT NULL,
    uploaded_by INTEGER NOT NULL REFERENCES users(id),
    verified BOOLEAN DEFAULT false,
    verified_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);

CREATE INDEX IF NOT EXISTS ix_receipts_id ON receipts(id);
CREATE INDEX IF NOT EXISTS ix_receipts_spending_request_id ON receipts(spending_request_id);
CREATE INDEX IF NOT EXISTS ix_receipts_verified ON receipts(verified);

-- Create smart_contract_operation_logs table
CREATE TABLE IF NOT EXISTS smart_contract_operation_logs (
    id SERIAL PRIMARY KEY,
    operation_type VARCHAR NOT NULL,
    payload JSONB NOT NULL,
    result TEXT,
    tx_hash VARCHAR,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT now()
);

CREATE INDEX IF NOT EXISTS ix_smart_contract_operation_logs_id ON smart_contract_operation_logs(id);
CREATE INDEX IF NOT EXISTS ix_smart_contract_operation_logs_operation_type ON smart_contract_operation_logs(operation_type);
CREATE INDEX IF NOT EXISTS ix_smart_contract_operation_logs_timestamp ON smart_contract_operation_logs(timestamp);
CREATE INDEX IF NOT EXISTS ix_smart_contract_operation_logs_tx_hash ON smart_contract_operation_logs(tx_hash);

