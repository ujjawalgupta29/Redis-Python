# Redis-Python

A Redis-compatible asynchronous in-memory key-value store implementation in Python. This project implements a subset of Redis commands with support for persistence, expiration, eviction, and command pipelining.

## Features

- **Asynchronous I/O**: Uses `kqueue` for high-performance async TCP server
- **RESP Protocol**: Full support for Redis Serialization Protocol
- **Command Pipelining**: Execute multiple commands in a single request
- **Key Expiration**: Automatic expiration with TTL support
- **Eviction**: Automatic key eviction when store limit is reached
- **Persistence**: AOF (Append Only File) support for data persistence
- **Type Encoding**: Efficient encoding for integers, raw strings, and embedded strings

## Architecture

The project is organized into modular components:

- **`server.py`**: Main async TCP server using kqueue
- **`CommandReader.py`**: RESP protocol parser
- **`CommandEvaluator.py`**: Command execution engine
- **`KeyValueStore.py`**: In-memory key-value storage
- **`ValueObject.py`**: Value wrapper with expiration and encoding info
- **`AutoExpire.py`**: Automatic key expiration handler
- **`Eviction.py`**: Eviction policy implementation
- **`AOF.py`**: Append Only File persistence
- **`Encoding.py`**: Type and encoding utilities

## Installation

No external dependencies required! This project uses only Python standard library.

```bash
# Clone the repository
git clone <repository-url>
cd Redis-Python

# Run the server
python server.py
```

The server will start on `localhost:7379`.

## Usage

### Starting the Server

```bash
python server.py
```

You should see:
```
Starting an asynchronous TCP server on localhost:7379
Server is running on port 7379
```

### Connecting with Redis CLI

You can use the standard `redis-cli` tool:

```bash
redis-cli -p 7379
```

Or use `nc` (netcat) for raw protocol interaction:

```bash
nc localhost 7379
```

## Supported Commands

### PING

Check if the server is responding.

**Syntax:**
```
PING [message]
```

**Examples:**
```bash
# Simple ping
PING
# Response: +PONG\r\n

# Ping with message
PING hello
# Response: $5\r\nhello\r\n
```

### SET

Set a key to hold a string value.

**Syntax:**
```
SET key value [EX seconds]
```

**Examples:**
```bash
# Set a key-value pair
SET mykey "Hello World"
# Response: +OK\r\n

# Set with expiration (10 seconds)
SET mykey "Hello World" EX 10
# Response: +OK\r\n
```

### GET

Get the value of a key.

**Syntax:**
```
GET key
```

**Examples:**
```bash
# Get a value
GET mykey
# Response: $11\r\nHello World\r\n

# Get non-existent key
GET nonexistent
# Response: $-1\r\n (nil)
```

### DEL

Delete one or more keys.

**Syntax:**
```
DEL key [key ...]
```

**Examples:**
```bash
# Delete a single key
DEL mykey
# Response: :1\r\n (1 key deleted)

# Delete multiple keys
DEL key1 key2 key3
# Response: :3\r\n (3 keys deleted)

# Delete non-existent key
DEL nonexistent
# Response: :0\r\n (0 keys deleted)
```

### EXPIRE

Set a timeout on a key.

**Syntax:**
```
EXPIRE key seconds
```

**Examples:**
```bash
# Set expiration on existing key
EXPIRE mykey 60
# Response: :1\r\n (success)

# Set expiration on non-existent key
EXPIRE nonexistent 60
# Response: :0\r\n (key doesn't exist)
```

### TTL

Get the time to live of a key in seconds.

**Syntax:**
```
TTL key
```

**Examples:**
```bash
# Get TTL of a key with expiration
TTL mykey
# Response: :45\r\n (45 seconds remaining)

# Get TTL of a key without expiration
TTL mykey
# Response: :-1\r\n (no expiration)

# Get TTL of non-existent key
TTL nonexistent
# Response: :-2\r\n (key doesn't exist)
```

### INCR

Increment the integer value of a key by one.

**Syntax:**
```
INCR key
```

**Examples:**
```bash
# Increment a new key (starts at 0)
INCR counter
# Response: :1\r\n

# Increment again
INCR counter
# Response: :2\r\n

# Error on non-integer value
SET mykey "hello"
INCR mykey
# Response: -ERR the operation is not permitted on this encoding\r\n
```

### BGREWRITEAOF

Rewrite the Append Only File in the background.

**Syntax:**
```
BGREWRITEAOF
```

**Examples:**
```bash
BGREWRITEAOF
# Response: + Background AOF rewrite finished successfully\r\n
# Creates a file: redis-<timestamp>.aof
```

## Command Pipelining

The server supports command pipelining, allowing you to send multiple commands in a single request:

**Example using printf and nc:**
```bash
printf '*1\r\n$4\r\nPING\r\n*3\r\n$3\r\nSET\r\n$1\r\nk\r\n$1\r\nv\r\n*2\r\n$3\r\nGET\r\n$1\r\nk\r\n' | nc localhost 7379
```

This sends three commands:
1. `PING` - Returns `+PONG\r\n`
2. `SET k v` - Sets key "k" to value "v", returns `+OK\r\n`
3. `GET k` - Gets value of "k", returns `$1\r\nv\r\n`

## RESP Protocol Format

The server uses Redis Serialization Protocol (RESP). Here's a quick reference:

- **Simple String**: `+OK\r\n`
- **Error**: `-ERR message\r\n`
- **Integer**: `:123\r\n`
- **Bulk String**: `$5\r\nhello\r\n` (length + data)
- **Array**: `*2\r\n$3\r\nGET\r\n$1\r\nk\r\n` (count + elements)

## Internal Features

### Automatic Expiration

The server runs a background cron job that automatically deletes expired keys. The cron job:
- Runs every second (`cronFreq = 1`)
- Processes up to 10 expired keys per cycle (`expireLimit = 10`)
- Continues processing if more than 25% of keys are expired (`expireFrac = 0.25`)

### Eviction Policy

When the store exceeds its limit (default: 100 keys), the eviction policy automatically removes keys to maintain performance. The eviction strategy:

- **Trigger**: Eviction activates when the store size exceeds the configured limit (100 keys)
- **Target**: Evicts keys down to 60% of the limit (60 keys) to provide headroom for new inserts
- **Method**: Removes keys sequentially until the target size is reached
- **Configurable**: The limit and eviction ratio can be adjusted in `KeyValueStore.py` and `Eviction.py`

This ensures the store maintains a stable size range (60-100 keys) and prevents memory issues during high-load scenarios.

### Type Encoding

The server uses efficient encoding for different value types:
- **INT**: Integer values stored as integers
- **EMBSTR**: Strings ≤ 44 characters (embedded string)
- **RAW**: Strings > 44 characters (raw string)

### AOF Persistence

The `BGREWRITEAOF` command creates a snapshot of the current store in RESP format, saved as `redis-<timestamp>.aof`.

## Monitoring with Prometheus

The project includes Prometheus monitoring support to track Redis server metrics in real-time. This is particularly useful for observing eviction behavior, key counts, and performance under load.

### Setup

1. **Install Redis Exporter**: Download and install the [redis_exporter](https://github.com/oliver006/redis_exporter) tool.

2. **Start Redis Exporter**: Run the exporter pointing to your Redis-Python server:
   ```bash
   ./redis_exporter -redis.addr redis://localhost:7379
   ```
   The exporter will expose metrics on `localhost:9121` by default.

3. **Start Prometheus**: Use the provided `prometheus.yml` configuration file:
   ```bash
   prometheus --config.file=./prometheus.yml --web.enable-admin-api
   ```
   Prometheus will start on `localhost:9090` by default.

### Configuration

The `prometheus.yml` file is pre-configured with:
- **Scrape interval**: 1 second (for real-time monitoring)
- **Target**: `localhost:9121` (redis_exporter endpoint)
- **Job name**: `redis_exporter`

### Accessing Metrics

1. **Prometheus UI**: Open your browser and navigate to:
   ```
   http://localhost:9090
   ```

2. **Query Interface**: Access the graph query interface at:
   ```
   http://localhost:9090/query?g0.expr=&g0.show_tree=0&g0.tab=graph&g0.range_input=1h&g0.res_type=auto&g0.res_density=medium&g0.display_mode=lines&g0.show_exemplars=0
   ```

3. **Example Queries**:
   - `redis_connected_clients` - Number of connected clients
   - `redis_keyspace_keys` - Total number of keys
   - `redis_commands_processed_total` - Total commands processed

### Testing with Bulk Load

You can use the provided `bulkFire.py` script to generate load and observe eviction behavior:

```bash
# In one terminal, start the server
python server.py

# In another terminal, run bulkFire to generate load
python utility/bulkFire.py

# Monitor the metrics in Prometheus UI
```

The bulkFire script creates 10 concurrent threads, each sending SET commands every 0.5 seconds, which helps visualize the eviction policy in action.

### Example Graph

A sample Prometheus graph showing key count behavior during bulk load testing is available in the `testing/` folder:

![Prometheus Bulk Testing Graph](testing/PrometheusBulkTesting.png)

This graph demonstrates the eviction policy working correctly, with keys oscillating between the target range (60-100 keys) as eviction triggers when the limit is exceeded.

## Limitations

- Store limit is hardcoded to 100 keys (configurable in `KeyValueStore.py`)
- Eviction policy evicts to 60% of limit (configurable in `Eviction.py`)
- Limited command set (8 commands)
- AOF rewrite is synchronous (not truly background)
- No RDB persistence
- No replication support
- No authentication/authorization

## Example Session

```bash
# Start server
python server.py

# In another terminal, connect with redis-cli
redis-cli -p 7379

# Or use nc for raw protocol
nc localhost 7379

# Then type commands:
*3\r\n$3\r\nSET\r\n$4\r\nname\r\n$5\r\nAlice\r\n
+OK\r\n

*2\r\n$3\r\nGET\r\n$4\r\nname\r\n
$5\r\nAlice\r\n

*3\r\n$5\r\nEXPIRE\r\n$4\r\nname\r\n$2\r\n30\r\n
:1\r\n

*2\r\n$3\r\nTTL\r\n$4\r\nname\r\n
:28\r\n
```

## Development

The codebase follows a modular architecture:

1. **CommandReader**: Parses incoming RESP protocol commands
2. **CommandEvaluator**: Routes commands to appropriate handlers
3. **KeyValueStore**: Manages in-memory storage with expiration checks
4. **AutoExpire**: Background task for cleaning expired keys
5. **Eviction**: Handles eviction when store is full
6. **AOF**: Manages persistence to disk

## License

See [LICENSE](LICENSE) file for details.
