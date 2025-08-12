-- ============================================================================
-- ÍNDICES CRÍTICOS PARA PRODUCCIÓN
-- ============================================================================
-- Este script debe ejecutarse después de crear las tablas
-- Ejecutar: psql -d bots_de_cobranza -f scripts/create_indexes.sql

-- Índices para tabla debtors
CREATE INDEX IF NOT EXISTS idx_debtors_state ON debtors(state);
CREATE INDEX IF NOT EXISTS idx_debtors_dni ON debtors(dni);
CREATE INDEX IF NOT EXISTS idx_debtors_phone ON debtors(phone);
CREATE INDEX IF NOT EXISTS idx_debtors_dataset_id ON debtors(debtor_dataset_id);
CREATE INDEX IF NOT EXISTS idx_debtors_user_id ON debtors(user_id);
CREATE INDEX IF NOT EXISTS idx_debtors_created_at ON debtors(created_at);

-- Índice compuesto para búsquedas frecuentes
CREATE INDEX IF NOT EXISTS idx_debtors_state_dataset ON debtors(state, debtor_dataset_id);
CREATE INDEX IF NOT EXISTS idx_debtors_user_state ON debtors(user_id, state);

-- Índices para tabla campaigns
CREATE INDEX IF NOT EXISTS idx_campaigns_user_id ON campaigns(user_id);
CREATE INDEX IF NOT EXISTS idx_campaigns_status ON campaigns(status);
CREATE INDEX IF NOT EXISTS idx_campaigns_created_at ON campaigns(created_at);

-- Índices para tabla strategies
CREATE INDEX IF NOT EXISTS idx_strategies_user_id ON strategies(user_id);
CREATE INDEX IF NOT EXISTS idx_strategies_campaign_id ON strategies(campaign_id);
CREATE INDEX IF NOT EXISTS idx_strategies_active ON strategies(active);

-- Índices para tabla debt_payments
CREATE INDEX IF NOT EXISTS idx_debt_payments_status ON debt_payments(status);
CREATE INDEX IF NOT EXISTS idx_debt_payments_debtor_id ON debt_payments(debtor_id);
CREATE INDEX IF NOT EXISTS idx_debt_payments_created_at ON debt_payments(created_at);
CREATE INDEX IF NOT EXISTS idx_debt_payments_amount ON debt_payments(amount);

-- Índices para tabla debtor_datasets
CREATE INDEX IF NOT EXISTS idx_debtor_datasets_user_id ON debtor_datasets(user_id);
CREATE INDEX IF NOT EXISTS idx_debtor_datasets_created_at ON debtor_datasets(created_at);

-- Índices para tabla users
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_created_at ON users(created_at);

-- Índices para auditoría y trazabilidad
CREATE INDEX IF NOT EXISTS idx_conversations_debtor_id ON conversations(debtor_id);
CREATE INDEX IF NOT EXISTS idx_conversations_timestamp ON conversations(created_at);
CREATE INDEX IF NOT EXISTS idx_conversations_user_id ON conversations(user_id);

-- Índices para performance de consultas complejas
CREATE INDEX IF NOT EXISTS idx_debtors_composite_search ON debtors(state, debtor_dataset_id, created_at);
CREATE INDEX IF NOT EXISTS idx_payments_composite ON debt_payments(status, created_at, amount);

-- Índices para foreign keys (si no existen automáticamente)
CREATE INDEX IF NOT EXISTS idx_debtors_campaign_id ON debtors(campaign_id);
CREATE INDEX IF NOT EXISTS idx_debtors_strategy_id ON debtors(strategy_id);

-- ============================================================================
-- ANÁLISIS DE PERFORMANCE
-- ============================================================================
-- Después de crear los índices, ejecutar:
-- ANALYZE debtors;
-- ANALYZE campaigns;
-- ANALYZE strategies;
-- ANALYZE debt_payments;
-- ANALYZE users;
-- ANALYZE debtor_datasets;

-- ============================================================================
-- VERIFICACIÓN DE ÍNDICES
-- ============================================================================
-- Para verificar que los índices se crearon correctamente:
-- SELECT schemaname, tablename, indexname, indexdef 
-- FROM pg_indexes 
-- WHERE tablename IN ('debtors', 'campaigns', 'strategies', 'debt_payments', 'users', 'debtor_datasets')
-- ORDER BY tablename, indexname; 