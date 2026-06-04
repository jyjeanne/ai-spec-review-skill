# Database Performance Review Heuristics

## Focus areas

- **Index strategy**: covering, partial, composite, index-only scans, unused index detection
- **Query optimization**: EXPLAIN interpretation, join algorithms, common anti-patterns
- **Connection pooling**: sizing, timeout, pooler tools
- **Schema design**: normalization vs denormalization, partitioning, materialized views
- **ORM pitfalls**: N+1, lazy loading in loops, mass updates, missing select_related

---

## Index Strategy

### Index types

| Type | What it does | When to use |
|------|-------------|-------------|
| **B-tree** (default) | Balanced tree, ordered. Supports `=`, `<`, `>`, `BETWEEN`, `LIKE 'prefix%'`, `ORDER BY` | General purpose. 95% of indexes should be B-tree |
| **Hash** | Hash table. Supports only `=` | Rare — only when you never need range queries |
| **GIN** | Inverted index. Supports array containment, full-text search, JSONB operators | Array column queries, full-text search, JSONB existence |
| **GiST** | Generalized search tree. Supports geometric data, full-text search | PostGIS, custom data types |
| **BRIN** | Block Range Index. Summarizes ranges of blocks | Very large tables with natural sort order (time-series). Tiny index, low maintenance |

### Composite index column order

The index is usable only for queries that filter on a **leftmost prefix** of the columns.

For a composite index on `(A, B, C)`:
- ✅ `WHERE A = ?` — uses index
- ✅ `WHERE A = ? AND B = ?` — uses index
- ✅ `WHERE A = ? AND B = ? AND C = ?` — uses index
- ❌ `WHERE B = ?` — does NOT use index (B is not a leftmost prefix)
- ❌ `WHERE C = ?` — does NOT use index

**Column ordering rules:**
1. Equality-filtered columns first (`status = 'active'`, `type = 'order'`)
2. Then range-filtered columns (`created_at > '2025-01-01'`, `price BETWEEN 10 AND 100`)
3. Then included columns that appear in SELECT but not in filters
4. Most selective columns first within equality columns (columns that filter out the
   most rows)

### Covering indexes

An index that contains all columns needed by a query. The query never touches the table —
it's satisfied entirely by the index (an "index-only scan").

```sql
-- Query only needs status and created_at
SELECT status, created_at FROM orders WHERE user_id = 123;

-- Covering index includes all needed columns
CREATE INDEX idx_orders_user_status_created ON orders (user_id, status, created_at);
```

**Caveat:** Covering indexes are wider (more columns → larger index → slower writes).
Only use when the query is frequent and performance-critical.

### Partial indexes

Index only a subset of rows. Smaller, faster writes, ideal for filtering a common condition.

```sql
-- Index only active orders (likely a small subset)
CREATE INDEX idx_active_orders ON orders (user_id) WHERE status = 'active';

-- This query uses the partial index
SELECT * FROM orders WHERE status = 'active' AND user_id = 123;
```

### Unused index detection

Unused indexes still incur write overhead (every INSERT/UPDATE/DELETE updates the index).
Remove them.

**PostgreSQL:**
```sql
SELECT schemaname, tablename, indexname, idx_scan, idx_tup_read, idx_tup_fetch
FROM pg_stat_user_indexes
WHERE idx_scan = 0
ORDER BY pg_relation_size(indexrelid) DESC;
```

**MySQL:**
```sql
SELECT * FROM sys.schema_unused_indexes;
```

---

## Query Optimization

### EXPLAIN / EXPLAIN ANALYZE

Always review query plans when diagnosing slow queries.

**Key signals in the plan:**

| Signal | Meaning | Action |
|--------|---------|--------|
| `Seq Scan` on a large table | No usable index exists | Create index |
| `Nested Loop` on large tables | One side is being scanned repeatedly | Hash join would be faster; check indexes |
| `Rows` estimate >> `actual rows` | Table statistics are stale | `ANALYZE table_name` |
| `Rows` estimate << `actual rows` | Statistics stale or complex condition | `ANALYZE` or restructure query |
| High startup cost | Sorting, hashing, or other setup | Consider if index could avoid sort |
| `Sort` on large dataset | No index supporting ORDER BY | Create index matching ORDER BY |
| Work_mem exceeded (disk-based sort) | `work_mem` too small for sort operations | Increase `work_mem` (per-operation, not global) |

### Join algorithms

| Algorithm | How it works | Best when |
|-----------|-------------|-----------|
| **Nested Loop** | For each row in outer, scan inner for matches | One side is very small AND inner side is indexed |
| **Hash Join** | Build hash table from one side, probe with other | Both sides are medium-large, unsorted |
| **Merge Join** | Sort both sides, then merge scan | Both sides pre-sorted by join key (e.g., indexed) |

### Common query anti-patterns

```sql
-- ❌ Function on indexed column prevents index use
SELECT * FROM users WHERE LOWER(email) = 'user@example.com';

-- ✅ Use functional index or normalize the column
CREATE INDEX idx_users_email_lower ON users (LOWER(email));
-- OR store email in normalized form and query that

-- ❌ Leading wildcard prevents index use
SELECT * FROM products WHERE name LIKE '%widget%';

-- ✅ Full-text search
CREATE INDEX idx_products_name_fts ON products USING GIN (to_tsvector('english', name));
SELECT * FROM products WHERE to_tsvector('english', name) @@ to_tsquery('widget');

-- ❌ Negation conditions typically can't use indexes efficiently
SELECT * FROM orders WHERE status != 'cancelled';

-- ✅ Use positive conditions or partial indexes
CREATE INDEX idx_active_orders ON orders (created_at) WHERE status != 'cancelled';

-- ❌ OR across different columns
SELECT * FROM users WHERE email = ? OR phone = ?;

-- ✅ UNION two indexed queries
SELECT * FROM users WHERE email = ? UNION SELECT * FROM users WHERE phone = ?;

-- ❌ LIMIT without ORDER BY — results are non-deterministic
SELECT * FROM events LIMIT 10;

-- ✅ Always use ORDER BY with LIMIT for predictable pagination
SELECT * FROM events ORDER BY created_at DESC LIMIT 10;
```

### Missing pagination

Every query that can return more than a few hundred rows must be paginated.

**Cursor-based pagination** (recommended for large datasets):
```sql
SELECT * FROM events
WHERE created_at < ?
ORDER BY created_at DESC
LIMIT 20;
```

Uses a cursor (last-seen value) instead of offset. Avoids the performance degradation
of `OFFSET` at large page numbers (database must scan and discard offset rows).

**Offset-based pagination** (acceptable for small datasets with stable row order):
```sql
SELECT * FROM events ORDER BY created_at DESC LIMIT 20 OFFSET 40;
```

---

## Connection Pooling

### Pool sizing

Starting formula: `connections = (core_count * 2) + effective_spindle_count`

But this is a starting point. The real answer depends on:
- What percentage of time each connection is active (querying) vs idle?
- How many concurrent requests must be served?
- What is the database's max connection limit?

**Too-small pool:** threads queue for connections → latency increases linearly with load
**Too-large pool:** too many active connections → database CPU contention, context switching,
throughput actually drops

PostgreSQL typically peaks in throughput around 100-200 active connections (depends
heavily on hardware and query patterns).

### Pooler tools

| Tool | Mode | Best for |
|------|------|----------|
| PgBouncer | Transaction pooling | Multiplexing many client connections to few database connections |
| PgBouncer | Session pooling | When you need session-level features (prepared statements, temp tables) |
| Pgpool-II | Connection pooling + load balancing + replication | PostgreSQL HA setups |
| RDS Proxy | Managed pooler | AWS RDS with Lambda (Lambda connection storms) |

### Connection timeout

Always set a connection acquisition timeout:
```python
# SQLAlchemy
engine = create_engine(url, pool_size=20, pool_timeout=30, max_overflow=10)
```

Threads fail fast (with an error) rather than queuing indefinitely when the pool is
exhausted.

---

## Schema Design for Performance

### Normalization tradeoffs

| Normalized | Denormalized |
|-----------|-------------|
| ✅ No data duplication | ❌ Data duplicated |
| ✅ Updates touch one place | ❌ Updates must update all copies |
| ✅ Data integrity by design | ❌ Integrity must be enforced in application |
| ❌ Joins needed for reads | ✅ Single-table reads |
| ❌ Read performance can suffer | ✅ Read performance is simpler |

**Rule of thumb:** Normalize by default. Denormalize only when profiling shows that
specific join queries are the bottleneck AND denormalization improves them measurably.

### Partitioning

Split a large table into smaller physical tables that act as one logical table.

**By range** (most common):
```sql
CREATE TABLE events (
    id BIGSERIAL,
    created_at TIMESTAMPTZ NOT NULL,
    data JSONB
) PARTITION BY RANGE (created_at);

CREATE TABLE events_2025_01 PARTITION OF events
    FOR VALUES FROM ('2025-01-01') TO ('2025-02-01');
```

**Benefits:**
- Queries that filter on the partition key scan only relevant partitions (partition pruning)
- Dropping old partitions is instant (no DELETE overhead)
- Indexes per partition are smaller → faster

### Materialized views

Pre-computed query results stored as a table. Refresh on schedule.

```sql
CREATE MATERIALIZED VIEW daily_sales AS
SELECT date(created_at) AS day, SUM(total) AS revenue, COUNT(*) AS orders
FROM orders
GROUP BY date(created_at);

-- Refresh concurrently (without blocking reads)
CREATE UNIQUE INDEX ON daily_sales (day);
REFRESH MATERIALIZED VIEW CONCURRENTLY daily_sales;
```

**Tradeoff:** Data is stale between refreshes. Acceptable for dashboards and analytics;
unacceptable for real-time data.

---

## ORM Performance Anti-Patterns

### N+1 queries

The most common ORM performance problem.

```python
# ❌ N+1: 1 query for orders + N queries for each order's customer
orders = Order.objects.all()
for order in orders:
    print(order.customer.name)  # triggers query for each order

# ✅ Eager loading: 1 query for orders with customer JOIN
orders = Order.objects.select_related('customer').all()

# ✅ Prefetch for many-to-many / reverse FK: 2 queries
orders = Order.objects.prefetch_related('items').all()
```

**Detection:** Enable query logging in dev. If you see the same query pattern repeating
in a loop, it's N+1.

### Mass updates via ORM

```python
# ❌ Load all objects, modify, save — N+1 UPDATEs
for order in Order.objects.filter(status='pending'):
    order.status = 'cancelled'
    order.save()

# ✅ Single UPDATE query
Order.objects.filter(status='pending').update(status='cancelled')
```

### Fetching unnecessary columns

```python
# ❌ Fetch all columns
users = User.objects.all()

# ✅ Fetch only needed columns
users = User.objects.only('id', 'email').all()

# ❌ Fetch large text field when not needed
posts = Post.objects.all()  # includes body

# ✅ Defer large fields
posts = Post.objects.defer('body').all()
```

### Count on QuerySet

```python
# ❌ len() fetches all objects into memory
count = len(Order.objects.all())

# ✅ .count() does SELECT COUNT(*) and returns a number
count = Order.objects.count()
```

### Missing select_related for ForeignKey access

```python
# ❌ Each book.author access triggers a query
books = Book.objects.all()
for book in books:
    print(book.author.name)

# ✅ Join author in the initial query
books = Book.objects.select_related('author').all()
```

---

## Common Risks

- No indexes on columns used in WHERE, JOIN, ORDER BY in hot queries
- N+1 queries from ORM lazy loading in request-response loops
- Missing pagination on queries that can return unbounded results
- Connection pool too small for concurrency (or too large, causing DB contention)
- Schema normalized for write purity but causing 5-way JOINs on every read
- Materialized views refreshing during peak traffic (blocking reads)
- `OFFSET` pagination on large tables — performance degrades as users page deeper
- No query timeout configured — a runaway query holds a connection forever
- Function calls on indexed columns (`WHERE LOWER(email) = ?`) preventing index use

## Review questions

- Which queries will handle the highest throughput? Are they covered by appropriate indexes?
- Are there N+1 query patterns in the implied ORM usage?
- Is pagination cursor-based or offset-based? Will offset performance degrade at scale?
- What is the connection pool size and is it appropriate for expected concurrency?
- Are query timeouts configured? What happens when a query takes 30 seconds?
- Which tables are expected to grow fastest? Is a partitioning strategy defined?
- Are there unused indexes from earlier development phases that should be cleaned up?
- Is there a plan for database load testing at expected peak throughput?
