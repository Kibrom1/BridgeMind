-- Sample database seed data for BridgeMind
-- This creates the sample schema with customers, orders, and refunds

-- Create sample tables
CREATE TABLE IF NOT EXISTS customers(
  customer_id SERIAL PRIMARY KEY,
  name TEXT NOT NULL,
  email TEXT UNIQUE,
  country TEXT,
  created_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE IF NOT EXISTS orders(
  order_id SERIAL PRIMARY KEY,
  customer_id INT REFERENCES customers(customer_id),
  order_date DATE NOT NULL,
  status TEXT CHECK (status IN ('pending','shipped','refunded')),
  total_amount NUMERIC(10,2) NOT NULL
);

CREATE TABLE IF NOT EXISTS refunds(
  refund_id SERIAL PRIMARY KEY,
  order_id INT REFERENCES orders(order_id),
  reason TEXT,
  refund_date DATE NOT NULL,
  amount NUMERIC(10,2) NOT NULL
);

-- Insert sample customers (25 customers)
INSERT INTO customers (name, email, country) VALUES
('John Smith', 'john.smith@example.com', 'USA'),
('Emma Johnson', 'emma.johnson@example.com', 'UK'),
('Michael Brown', 'michael.brown@example.com', 'Canada'),
('Sarah Davis', 'sarah.davis@example.com', 'Australia'),
('David Wilson', 'david.wilson@example.com', 'USA'),
('Lisa Anderson', 'lisa.anderson@example.com', 'UK'),
('James Taylor', 'james.taylor@example.com', 'USA'),
('Mary Thomas', 'mary.thomas@example.com', 'Canada'),
('Robert Jackson', 'robert.jackson@example.com', 'UK'),
('Jennifer White', 'jennifer.white@example.com', 'USA'),
('William Harris', 'william.harris@example.com', 'Australia'),
('Linda Martin', 'linda.martin@example.com', 'USA'),
('Richard Thompson', 'richard.thompson@example.com', 'UK'),
('Patricia Garcia', 'patricia.garcia@example.com', 'USA'),
('Joseph Martinez', 'joseph.martinez@example.com', 'Canada'),
('Barbara Robinson', 'barbara.robinson@example.com', 'USA'),
('Thomas Clark', 'thomas.clark@example.com', 'UK'),
('Elizabeth Rodriguez', 'elizabeth.rodriguez@example.com', 'USA'),
('Charles Lewis', 'charles.lewis@example.com', 'Australia'),
('Jessica Walker', 'jessica.walker@example.com', 'USA'),
('Christopher Hall', 'christopher.hall@example.com', 'UK'),
('Susan Allen', 'susan.allen@example.com', 'Canada'),
('Daniel Young', 'daniel.young@example.com', 'USA'),
('Karen King', 'karen.king@example.com', 'UK'),
('Matthew Wright', 'matthew.wright@example.com', 'USA')
ON CONFLICT (email) DO NOTHING;

-- Insert sample orders (120 orders)
-- This is a simplified version - in production, generate more realistic data
INSERT INTO orders (customer_id, order_date, status, total_amount)
SELECT 
  c.customer_id,
  CURRENT_DATE - (random() * 365)::int,
  (ARRAY['pending', 'shipped', 'refunded'])[floor(random() * 3 + 1)::int],
  (random() * 1000 + 10)::numeric(10,2)
FROM customers c
CROSS JOIN generate_series(1, 5)  -- 5 orders per customer on average
LIMIT 120;

-- Insert sample refunds (12 refunds)
INSERT INTO refunds (order_id, reason, refund_date, amount)
SELECT 
  o.order_id,
  (ARRAY['Defective product', 'Wrong item', 'Customer request', 'Quality issue'])[floor(random() * 4 + 1)::int],
  o.order_date + (random() * 30)::int,
  o.total_amount * (0.5 + random() * 0.5)  -- 50-100% refund
FROM orders o
WHERE o.status = 'refunded'
LIMIT 12;

