-- Fiverr Shareable Links Database Schema
-- Migration: Create core tables for link shortening system

-- Links table (core data)
CREATE TABLE IF NOT EXISTS links (
    id SERIAL PRIMARY KEY,
    seller_id VARCHAR(255) NOT NULL,
    original_url TEXT NOT NULL,
    short_code VARCHAR(10) UNIQUE NOT NULL,
    click_count INTEGER DEFAULT 0,
    credits_earned DECIMAL(10,2) DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(seller_id, original_url)
);

-- Clicks table (detailed tracking)
CREATE TABLE IF NOT EXISTS clicks (
    id SERIAL PRIMARY KEY,
    link_id INTEGER NOT NULL REFERENCES links(id) ON DELETE CASCADE,
    clicked_at TIMESTAMP DEFAULT NOW(),
    ip_address VARCHAR(45),
    user_agent TEXT,
    reward_status VARCHAR(20) DEFAULT 'pending'
);

-- Rewards table (audit trail)
CREATE TABLE IF NOT EXISTS rewards (
    id SERIAL PRIMARY KEY,
    seller_id VARCHAR(255) NOT NULL,
    link_id INTEGER NOT NULL REFERENCES links(id) ON DELETE CASCADE,
    click_id INTEGER REFERENCES clicks(id) ON DELETE SET NULL,
    amount DECIMAL(10,2) NOT NULL,
    status VARCHAR(20) DEFAULT 'pending',
    aws_transaction_id VARCHAR(255),
    created_at TIMESTAMP DEFAULT NOW(),
    completed_at TIMESTAMP
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_links_short_code ON links(short_code);
CREATE INDEX IF NOT EXISTS idx_links_seller_id ON links(seller_id);
CREATE INDEX IF NOT EXISTS idx_links_created_at ON links(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_clicks_link_id ON clicks(link_id);
CREATE INDEX IF NOT EXISTS idx_clicks_created_at ON clicks(clicked_at DESC);
CREATE INDEX IF NOT EXISTS idx_rewards_seller_id ON rewards(seller_id);
CREATE INDEX IF NOT EXISTS idx_rewards_status ON rewards(status);
