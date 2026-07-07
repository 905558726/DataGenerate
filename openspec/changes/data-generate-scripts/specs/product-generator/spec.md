# Product Generator Specification

## ADDED Requirements

### Requirement: Pre-built product library
The system SHALL include a static JSON product library (`data/product_library.json`) containing realistically crafted Chinese e-commerce product entries across multiple categories, serving as the persistent data foundation for product generation.

#### Scenario: Product library is loadable
- **WHEN** `product_generator.py` starts
- **THEN** the system loads `data/product_library.json` and validates it contains at least 100 product entries across at least 5 distinct categories

#### Scenario: Product library entry structure
- **WHEN** a product library entry is read
- **THEN** it MUST contain: `name` (string), `brand` (string), `category` (string, top-level), `sub_category` (string), `price_min` (number, positive), `price_max` (number, >= price_min), `image_url` (string), `keywords` (array of strings)

### Requirement: Generate product data from library
The system SHALL load the product library and sample/extend from it to generate a specified number of product records, supplementing with simulated fields.

#### Scenario: Generate fewer products than library size
- **WHEN** the user runs `python product_generator.py --count 50` and the library has 300 entries
- **THEN** the system randomly samples 50 entries without replacement, adds simulated fields, and outputs to `output/products.json`

#### Scenario: Generate more products than library size
- **WHEN** the user runs `python product_generator.py --count 1000` and the library has 300 entries
- **THEN** the system uses all 300 library entries and generates 700 additional entries by creating variants (different specs/colors within each base entry's price range), ensuring all product_ids are unique

### Requirement: Product data structure
Each generated product record SHALL contain the following fields.

#### Scenario: Product record has all required fields
- **WHEN** a product record is generated
- **THEN** the record MUST contain: `product_id` (string, unique UUID-based), `name` (string, with optional variant suffix like "128GB版"), `brand` (string), `category` (string), `sub_category` (string), `price` (number, 2 decimal places, within price_min~price_max of the source entry), `stock` (integer, non-negative), `description` (string, at least 10 characters, assembled from brand+name+keywords), `image_url` (string), `keywords` (array of strings), `sales_volume` (integer, non-negative), `created_at` (string, ISO 8601 datetime), `is_variant` (boolean, true if generated as a variant of a library entry)

### Requirement: Variant generation when exceeding library size
When the requested count exceeds the library size, the system SHALL create variants of existing entries with differentiated names, prices, and product_ids.

#### Scenario: Variant has modified name and price
- **WHEN** a variant of "iPhone 15 Pro Max" is generated
- **THEN** its name MUST differ from the base entry (e.g., append "512GB版"), its price MUST be within the same price_min~price_max range but differ from the base by at least 1%, and the `is_variant` field MUST be true

### Requirement: Simulated field generation
The system SHALL generate realistic values for fields not present in the library (stock, sales_volume, description, created_at).

#### Scenario: Stock distribution is realistic
- **WHEN** product stock values are simulated
- **THEN** ~80% of products have stock 100-9999, ~15% have 1-99, ~5% have 0 (out of stock)

#### Scenario: Sales volume correlates with stock
- **WHEN** a product has higher sales volume (e.g., >10000)
- **THEN** its stock should tend to be higher (positive correlation, not strict)

#### Scenario: Description is assembled from available data
- **WHEN** a product description is generated
- **THEN** it MUST be a coherent Chinese sentence incorporating the brand, product name, sub_category, and at least one keyword, with at least 10 characters

### Requirement: Configurable generation parameters
The system SHALL support a YAML configuration file (with JSON fallback) for default parameters and command-line arguments for overrides.

#### Scenario: Read parameters from config file
- **WHEN** `config.yaml` specifies `product_count: 200` and the user runs `python product_generator.py` without `--count`
- **THEN** the system generates 200 product records

#### Scenario: Command-line argument overrides config file
- **WHEN** `config.yaml` specifies `product_count: 200` and the user runs `python product_generator.py --count 50`
- **THEN** the system generates 50 product records

#### Scenario: Custom library path
- **WHEN** the user runs `python product_generator.py --library custom_lib.json`
- **THEN** the system loads the product library from the specified path

### Requirement: Reproducible generation with seed
The system SHALL support a random seed parameter for reproducible generation.

#### Scenario: Same seed produces same data
- **WHEN** the user runs `python product_generator.py --count 10 --seed 42` twice
- **THEN** both runs produce identical product records

### Requirement: Dual output mode (file / kafka)
The system SHALL support two output modes selected automatically by the `--output` parameter format.

#### Scenario: File output mode (default)
- **WHEN** the user runs `python product_generator.py --output output/products.json`
- **THEN** the system generates product records and writes them as a JSON array file to the specified path

#### Scenario: Kafka output mode
- **WHEN** the user runs `python product_generator.py --output kafka://localhost:9092/products --count 100`
- **THEN** the system connects to Kafka broker at `localhost:9092`, sends each product record as a JSON message to topic `products` (key = product_id), and also writes a local backup file to the default file output path

#### Scenario: Kafka mode with custom file backup
- **WHEN** the user runs `python product_generator.py --output kafka://localhost:9092/products --file-backup output/backup_products.json --count 100`
- **THEN** the system pushes to Kafka topic `products` AND writes a JSON array backup file to `output/backup_products.json`

#### Scenario: Kafka not available
- **WHEN** the user specifies a kafka:// URI but the kafka-python library is not installed or the broker is unreachable
- **THEN** the system SHALL print a clear error message indicating the issue and exit with code 1

### Requirement: Deduplication
The system SHALL ensure all generated product records have unique product_ids.

#### Scenario: No duplicate product IDs
- **WHEN** a batch of product records is generated
- **THEN** all `product_id` values MUST be unique across the entire output
