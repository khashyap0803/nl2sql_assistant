-- Database schema for NL2SQL Assistant
-- Run this in pgAdmin after creating the nl2sql_db database

-- Drop table if exists (for clean restart)
DROP TABLE IF EXISTS sales CASCADE;

-- Create sales table
CREATE TABLE sales (
    id SERIAL PRIMARY KEY,
    date DATE NOT NULL,
    amount DECIMAL(10,2) NOT NULL,
    product VARCHAR(100),
    region VARCHAR(50)
);

-- Create index for better query performance
CREATE INDEX idx_sales_date ON sales(date);
CREATE INDEX idx_sales_product ON sales(product);
CREATE INDEX idx_sales_region ON sales(region);

-- Insert sample data (100 rows)
INSERT INTO sales (date, amount, product, region) VALUES
('2025-08-01', 1000.00, 'Widget', 'North'),
('2025-08-02', 1500.50, 'Gadget', 'South'),
('2025-08-03', 2000.00, 'Widget', 'East'),
('2025-08-04', 1200.75, 'Gizmo', 'West'),
('2025-08-05', 1800.00, 'Tool', 'North'),
('2025-08-06', 2200.50, 'Device', 'South'),
('2025-08-07', 1600.00, 'Widget', 'East'),
('2025-08-08', 1900.25, 'Gadget', 'West'),
('2025-08-09', 2100.00, 'Gizmo', 'North'),
('2025-08-10', 1700.75, 'Tool', 'South'),
('2025-08-11', 2300.00, 'Device', 'East'),
('2025-08-12', 1400.50, 'Widget', 'West'),
('2025-08-13', 2500.00, 'Gadget', 'North'),
('2025-08-14', 1300.25, 'Gizmo', 'South'),
('2025-08-15', 2700.00, 'Tool', 'East');

-- Verify data
SELECT COUNT(*) as total_rows FROM sales;
SELECT product, COUNT(*) as count FROM sales GROUP BY product;

