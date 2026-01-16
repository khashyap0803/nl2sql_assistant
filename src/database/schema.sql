DROP TABLE IF EXISTS sales CASCADE;

CREATE TABLE sales (
    id SERIAL PRIMARY KEY,
    date DATE NOT NULL,
    amount DECIMAL(10,2) NOT NULL,
    product VARCHAR(100),
    region VARCHAR(50),
    quantity INTEGER DEFAULT 1,
    customer_type VARCHAR(50) DEFAULT 'Regular'
);

CREATE INDEX idx_sales_date ON sales(date);
CREATE INDEX idx_sales_product ON sales(product);
CREATE INDEX idx_sales_region ON sales(region);
CREATE INDEX idx_sales_amount ON sales(amount);

INSERT INTO sales (date, amount, product, region, quantity, customer_type) VALUES
('2025-01-02', 1299.99, 'Laptop', 'North', 1, 'Business'),
('2025-01-03', 899.50, 'Desktop', 'South', 1, 'Regular'),
('2025-01-05', 349.99, 'Monitor', 'East', 2, 'Business'),
('2025-01-06', 129.99, 'Keyboard', 'West', 5, 'Regular'),
('2025-01-08', 79.99, 'Mouse', 'North', 10, 'Business'),
('2025-01-10', 199.99, 'Headphones', 'South', 3, 'Premium'),
('2025-01-11', 149.99, 'Webcam', 'East', 2, 'Regular'),
('2025-01-12', 549.99, 'Tablet', 'West', 1, 'Business'),
('2025-01-14', 999.99, 'Smartphone', 'North', 1, 'Premium'),
('2025-01-15', 89.99, 'Router', 'South', 4, 'Regular'),
('2025-01-17', 1499.99, 'Laptop', 'East', 1, 'Business'),
('2025-01-18', 749.99, 'Desktop', 'West', 1, 'Regular'),
('2025-01-20', 299.99, 'Monitor', 'North', 1, 'Premium'),
('2025-01-21', 159.99, 'Keyboard', 'South', 3, 'Business'),
('2025-01-23', 59.99, 'Mouse', 'East', 8, 'Regular'),
('2025-01-25', 249.99, 'Headphones', 'West', 2, 'Premium'),
('2025-01-26', 119.99, 'Webcam', 'North', 1, 'Regular'),
('2025-01-28', 649.99, 'Tablet', 'South', 1, 'Business'),
('2025-01-29', 1199.99, 'Smartphone', 'East', 1, 'Premium'),
('2025-01-31', 129.99, 'Router', 'West', 2, 'Regular'),
('2025-02-01', 1599.99, 'Laptop', 'North', 1, 'Premium'),
('2025-02-03', 999.99, 'Desktop', 'South', 1, 'Business'),
('2025-02-04', 449.99, 'Monitor', 'East', 1, 'Regular'),
('2025-02-06', 189.99, 'Keyboard', 'West', 2, 'Premium'),
('2025-02-07', 99.99, 'Mouse', 'North', 6, 'Regular'),
('2025-02-09', 299.99, 'Headphones', 'South', 1, 'Business'),
('2025-02-10', 179.99, 'Webcam', 'East', 2, 'Premium'),
('2025-02-12', 799.99, 'Tablet', 'West', 1, 'Regular'),
('2025-02-13', 1099.99, 'Smartphone', 'North', 1, 'Business'),
('2025-02-15', 149.99, 'Router', 'South', 3, 'Regular'),
('2025-02-16', 1899.99, 'Laptop', 'East', 1, 'Premium'),
('2025-02-18', 849.99, 'Desktop', 'West', 1, 'Business'),
('2025-02-19', 399.99, 'Monitor', 'North', 2, 'Regular'),
('2025-02-21', 139.99, 'Keyboard', 'South', 4, 'Business'),
('2025-02-22', 69.99, 'Mouse', 'East', 12, 'Regular'),
('2025-02-24', 349.99, 'Headphones', 'West', 1, 'Premium'),
('2025-02-25', 199.99, 'Webcam', 'North', 1, 'Business'),
('2025-02-27', 599.99, 'Tablet', 'South', 1, 'Regular'),
('2025-02-28', 899.99, 'Smartphone', 'East', 1, 'Premium'),
('2025-03-01', 109.99, 'Router', 'West', 5, 'Business'),
('2025-03-03', 1399.99, 'Laptop', 'North', 1, 'Regular'),
('2025-03-04', 1099.99, 'Desktop', 'South', 1, 'Premium'),
('2025-03-06', 549.99, 'Monitor', 'East', 1, 'Business'),
('2025-03-07', 169.99, 'Keyboard', 'West', 3, 'Regular'),
('2025-03-09', 89.99, 'Mouse', 'North', 7, 'Premium'),
('2025-03-10', 279.99, 'Headphones', 'South', 2, 'Business'),
('2025-03-12', 159.99, 'Webcam', 'East', 3, 'Regular'),
('2025-03-13', 699.99, 'Tablet', 'West', 1, 'Premium'),
('2025-03-15', 1299.99, 'Smartphone', 'North', 1, 'Business'),
('2025-03-16', 169.99, 'Router', 'South', 2, 'Regular'),
('2025-03-18', 2199.99, 'Laptop', 'East', 1, 'Premium'),
('2025-03-19', 1249.99, 'Desktop', 'West', 1, 'Business'),
('2025-03-21', 499.99, 'Monitor', 'North', 1, 'Regular'),
('2025-03-22', 199.99, 'Keyboard', 'South', 2, 'Premium'),
('2025-03-24', 109.99, 'Mouse', 'East', 5, 'Business'),
('2025-03-25', 399.99, 'Headphones', 'West', 1, 'Regular'),
('2025-03-27', 229.99, 'Webcam', 'North', 2, 'Premium'),
('2025-03-28', 849.99, 'Tablet', 'South', 1, 'Business'),
('2025-03-30', 1499.99, 'Smartphone', 'East', 1, 'Regular'),
('2025-03-31', 199.99, 'Router', 'West', 3, 'Premium');

SELECT COUNT(*) as total_rows FROM sales;
SELECT product, COUNT(*) as count, SUM(amount) as total_revenue FROM sales GROUP BY product ORDER BY total_revenue DESC;
SELECT region, COUNT(*) as count, SUM(amount) as total_revenue FROM sales GROUP BY region ORDER BY total_revenue DESC;
