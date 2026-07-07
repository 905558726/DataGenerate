# Order Generator Specification

## ADDED Requirements

### Requirement: Generate order data based on existing products
The system SHALL read product data from a product JSON file and generate order records that reference those products.

#### Scenario: Generate orders with product references
- **WHEN** the user runs `python order_generator.py --products output/products.json --count 200`
- **THEN** the system reads the product file, generates 200 orders each containing at least one product line item, and writes to `output/orders.json`

#### Scenario: Generate orders to Kafka
- **WHEN** the user runs `python order_generator.py --products output/products.json --output kafka://localhost:9092/orders --count 200`
- **THEN** the system reads the product file, generates 200 orders, sends each as a JSON message to Kafka topic `orders`, and writes a local backup JSON file

#### Scenario: Error on missing product file
- **WHEN** the user runs `python order_generator.py --products nonexistent.json`
- **THEN** the system exits with an error message indicating the product file does not exist

### Requirement: Order data structure
Each order record SHALL contain the following fields with valid and realistic values.

#### Scenario: Order record has all required fields
- **WHEN** an order record is generated
- **THEN** the record MUST contain these fields:
  - `order_id` (string, unique, format like "ORD20240707123456001")
  - `items` (array of objects, each containing `product_id`, `product_name`, `price`, `quantity`, `subtotal`)
  - `buyer` (object with `name`, `phone`, `email`)
  - `shipping_address` (object with `province`, `city`, `district`, `detail`, `postal_code`, `recipient_name`, `recipient_phone`)
  - `order_status` (string, one of: "待付款", "已付款", "已发货", "已完成", "已取消")
  - `payment` (object with `method`, `amount`, `paid_at`)
  - `logistics` (object with `company`, `tracking_number`, `shipped_at`, `estimated_delivery`)
  - `order_amount` (number, equal to sum of all items' subtotal)
  - `discount` (number, non-negative, not exceeding order_amount)
  - `actual_amount` (number, equal to order_amount - discount)
  - `created_at` (string, ISO 8601 datetime)
  - `remark` (string or null, optional order note)

### Requirement: Order items reference real products
The system SHALL populate order items using product data from the input product file, ensuring referential integrity.

#### Scenario: Order item product_id exists in product data
- **WHEN** an order contains an item with a given `product_id`
- **THEN** that product_id MUST exist in the product data file loaded by the generator

#### Scenario: Order item stores price snapshot
- **WHEN** an order item references a product with price 99.00
- **THEN** the item's `price` field SHALL be the generated price from the order (which may differ slightly from the original product price to simulate real-world price fluctuations), and `subtotal` SHALL equal `price × quantity`

### Requirement: Reasonable order item quantities
The system SHALL generate per-item quantities within reasonable bounds.

#### Scenario: Item quantity is between 1 and 10
- **WHEN** an order item is generated
- **THEN** its `quantity` SHALL be an integer between 1 and 10 inclusive, with a weighted distribution favoring 1-3

### Requirement: Order status distribution
The system SHALL distribute order statuses with realistic proportions.

#### Scenario: Order status distribution reflects real-world patterns
- **WHEN** 1000 orders are generated
- **THEN** the status distribution SHALL approximately follow: "已完成" ~50%, "已发货" ~15%, "已付款" ~15%, "待付款" ~10%, "已取消" ~10%

### Requirement: Payment method selection
The system SHALL assign payment methods with realistic distribution and ensure the payment status is consistent with order status.

#### Scenario: Paid orders have payment info
- **WHEN** an order status is "已付款", "已发货", or "已完成"
- **THEN** the `payment.paid_at` field MUST be set to a valid datetime, and `payment.method` SHALL be one of: "微信支付", "支付宝", "银行卡", "信用卡"

#### Scenario: Unpaid orders have no payment timestamp
- **WHEN** an order status is "待付款"
- **THEN** the `payment.paid_at` field MUST be null, and `payment.method` SHALL still be set (indicating the chosen payment method)

### Requirement: Logistics consistency with order status
The system SHALL ensure logistics information is consistent with the order status.

#### Scenario: Shipped orders have logistics info
- **WHEN** an order status is "已发货" or "已完成"
- **THEN** the `logistics` object MUST contain valid `company`, `tracking_number`, and `shipped_at` fields

#### Scenario: Unshipped orders have no logistics details
- **WHEN** an order status is "待付款" or "已付款"
- **THEN** the `logistics.shipped_at` field MUST be null and `logistics.tracking_number` MUST be null

### Requirement: Chinese address generation
The system SHALL generate realistic Chinese shipping addresses with valid province-city-district combinations.

#### Scenario: Address uses real Chinese administrative divisions
- **WHEN** a shipping address is generated
- **THEN** the `province`, `city`, and `district` fields SHALL correspond to actual Chinese administrative divisions, and `postal_code` SHALL be a 6-digit string

### Requirement: Configurable generation parameters for orders
The system SHALL support the same configuration mechanism as the product generator (YAML config + CLI overrides + random seed).

#### Scenario: Order generator reads config file
- **WHEN** `config.yaml` specifies `order_count: 300` and the user runs `python order_generator.py` without `--count`
- **THEN** the system generates 300 order records

### Requirement: Orders span a realistic time range
The system SHALL distribute order creation times over a configurable period.

#### Scenario: Orders spread over recent 90 days by default
- **WHEN** orders are generated without specifying a date range
- **THEN** the `created_at` timestamps SHALL be distributed over the past 90 days from the current date
