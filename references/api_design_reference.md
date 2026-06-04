# API Design Reference

## Focus areas

- **REST conventions**: resource naming, HTTP methods, status codes, pagination, filtering
- **GraphQL conventions**: type design, connections, mutations, errors, nullability
- **gRPC conventions**: service naming, proto design, streaming, error model
- **API versioning**: URL path, Accept header, query parameter — tradeoffs
- **Error responses**: standard envelope, HTTP Problem Details (RFC 7807)
- **Rate limiting**: strategies, response headers, status code

---

## REST Conventions

### Resource naming

```
GET    /users              # List users
POST   /users              # Create user
GET    /users/:id          # Retrieve user
PUT    /users/:id          # Replace user (full update)
PATCH  /users/:id          # Partial update
DELETE /users/:id          # Delete user
```

**Rules:**
- Plural nouns: `/users`, `/orders`, `/products` (not `/user`, `/getUsers`, `/createUser`)
- Hyphenated for multi-word: `/order-items`, `/payment-methods` (not `orderItems`, `order_items`)
- No verbs in URLs: use HTTP methods to express action (not `/createUser`, `/getUsers`)
- Sub-resources nested no more than 2 levels deep: `/users/:id/orders/:orderId/items`
  (deeper nesting → use top-level resource with filter)

### HTTP methods

| Method | Semantics | Idempotent | Safe |
|--------|-----------|-----------|------|
| GET | Retrieve representation | Yes | Yes |
| POST | Create new resource | No | No |
| PUT | Full replacement | Yes | No |
| PATCH | Partial update | Usually no | No |
| DELETE | Delete resource | Yes | No |
| HEAD | Retrieve headers only (no body) | Yes | Yes |
| OPTIONS | Discover allowed methods | Yes | Yes |

### Status codes

**Success:**
- `200 OK` — request succeeded (GET, PUT, PATCH)
- `201 Created` — resource created (POST). Include `Location` header with new resource URL
- `202 Accepted` — request accepted for async processing (not done yet)
- `204 No Content` — succeeded, no body to return (DELETE)

**Client errors:**
- `400 Bad Request` — malformed input (invalid JSON, missing required field)
- `401 Unauthorized` — missing or invalid authentication
- `403 Forbidden` — authenticated but not authorized
- `404 Not Found` — resource doesn't exist (or hide existence for security)
- `409 Conflict` — request conflicts with current state (optimistic locking failure, duplicate)
- `422 Unprocessable Entity` — valid syntax, semantic error (validation failure)
- `429 Too Many Requests` — rate limit exceeded

**Server errors:**
- `500 Internal Server Error` — unexpected server error (bug)
- `502 Bad Gateway` — upstream service returned invalid response
- `503 Service Unavailable` — temporarily unavailable (maintenance, overloaded)

### Pagination

**Cursor-based** (recommended):

```
GET /events?cursor=eyJpZCI6MTIzfQ&limit=20

Response:
{
  "data": [...],
  "pagination": {
    "next_cursor": "eyJpZCI6MTAzfQ",
    "has_more": true
  }
}
```

Cursor is an opaque token (often base64-encoded JSON with the last-seen value).
Client passes cursor; server returns items after that point. Stable even when
new items are inserted.

**Offset-based** (acceptable for small, stable datasets):

```
GET /users?offset=40&limit=20

Response:
{
  "data": [...],
  "pagination": {
    "offset": 40,
    "limit": 20,
    "total": 500
  }
}
```

Avoid offset pagination when:
- Table has >10,000 rows (performance degrades)
- Items are frequently inserted/deleted (items shift, causing duplicates/skips)

### Filtering, sorting, field selection

**Filtering:**
```
GET /users?status=active&role=admin&created_after=2025-01-01
```

**Sorting** (`-` prefix for descending):
```
GET /users?sort=-created_at,name
```

**Field selection** (sparse responses):
```
GET /users?fields=id,name,email
```

**Search:**
```
GET /users?q=alice
```

---

## GraphQL Conventions

### Type design

```graphql
# PascalCase for types
type User {
  # camelCase for fields
  id: ID!
  email: String!
  name: String!
  createdAt: DateTime!
  updatedAt: DateTime!
  # Nullable by default
  avatarUrl: String
  # Connections for lists
  orders(first: Int, after: String): OrderConnection!
}
```

### Connections (Relay spec)

For paginated list fields:

```graphql
type User {
  orders(first: Int!, after: String): OrderConnection!
}

type OrderConnection {
  edges: [OrderEdge!]!
  pageInfo: PageInfo!
  totalCount: Int!
}

type OrderEdge {
  node: Order!
  cursor: String!
}

type PageInfo {
  hasNextPage: Boolean!
  hasPreviousPage: Boolean!
  startCursor: String
  endCursor: String
}
```

### Mutations

```graphql
type Mutation {
  # Verb + noun naming
  # Single input argument (not multiple scalar args)
  createOrder(input: CreateOrderInput!): CreateOrderPayload!
  cancelOrder(input: CancelOrderInput!): CancelOrderPayload!
}

input CreateOrderInput {
  userId: ID!
  items: [OrderItemInput!]!
  shippingAddress: AddressInput!
}
```

### Error handling

GraphQL partial success: queries can return partial data + errors.

```json
{
  "data": {
    "user": {
      "name": "Alice",
      "email": null  // field errored
    }
  },
  "errors": [
    {
      "message": "Email field is not accessible",
      "path": ["user", "email"],
      "extensions": {
        "code": "FORBIDDEN"
      }
    }
  ]
}
```

### Nullability

Fields are nullable by default. Use `!` to mark as required.

**Rule of thumb:** Make fields nullable unless you are certain they will never be null
AND it would be a bug if they were. Adding `!` later is a breaking change. Removing
`!` is not.

### Depth and complexity limiting

GraphQL's flexibility is both a feature and a risk. A malicious query can request
deeply nested data:

```graphql
query Malicious {
  users {
    orders { user { orders { user { orders { ... } } } } }
  }
}
```

**Mitigations:**
- **Query depth limit**: reject queries deeper than N levels (typically 7-10)
- **Query complexity analysis**: assign costs to fields, reject queries exceeding total cost
- **Timeout**: all queries must complete within X seconds
- **Persisted queries**: server only executes pre-registered queries
- **Introspection disabled** in production

### Deprecation

```graphql
type User {
  fullName: String @deprecated(reason: "Use `name` instead")
  name: String!
}
```

Don't remove fields — deprecate them first, give consumers time to migrate, then remove.

---

## gRPC Conventions

### Service and RPC naming

```protobuf
// Service: PascalCase + Service suffix
service UserService {
  // Unary RPC: PascalCase verb + noun
  rpc GetUser(GetUserRequest) returns (GetUserResponse);

  // Server streaming
  rpc ListUsers(ListUsersRequest) returns (stream User);

  // Client streaming
  rpc CreateUsers(stream CreateUserRequest) returns (CreateUsersResponse);

  // Bidirectional streaming
  rpc Chat(stream ChatMessage) returns (stream ChatMessage);
}

message User {
  // snake_case field names
  string user_id = 1;
  string email = 2;
  string name = 3;
  google.protobuf.Timestamp created_at = 4;
}
```

### Backward compatibility

Proto backwards-compatibility rules (MUST follow to avoid breaking consumers):

- **Never** change field numbers
- **Never** remove a field (use `reserved` instead)
- **Never** change a field's type
- **Safe** to add new fields (use the next available field number)
- **Safe** to add new RPC methods
- **Safe** to add new enum values (but add them sensibly)

```protobuf
message User {
  reserved 3, 5, 7 to 10;  // old fields, never reuse these numbers
  reserved "old_field_name", "legacy_status";

  string user_id = 1;
  string email = 2;
  string name = 4;  // was field 3; now field 4 after reserving 3
}
```

### Error model

Use `google.rpc.Status` for rich errors:

```protobuf
import "google/rpc/status.proto";

// Return google.rpc.Status in error responses
// status.code: gRPC status code (int)
// status.message: human-readable description
// status.details: repeated google.protobuf.Any with structured error info
```

---

## API Versioning

### Strategy tradeoffs

| Strategy | How it works | Pros | Cons |
|----------|-------------|------|------|
| **URL path** | `/v1/users`, `/v2/users` | Simplest; easy routing, testing, caching | URL changes; "not RESTful" (resource identity changes) |
| **Accept header** | `Accept: application/vnd.api.v1+json` | Resource URL stable; RESTful | Harder to test in browser; complex caching; clients must set headers |
| **Query parameter** | `/users?version=1` | Simple; browser-testable | Not RESTful; easy to forget |
| **Custom header** | `X-API-Version: 1` | Resource URL stable; explicit | Non-standard; harder to discover |

**Recommendation:** URL path for public APIs (simplicity trumps purity). Custom header
for internal APIs where tooling supports it.

### When to bump the version

**Major version bump** (v1 → v2):
- Removing or renaming a field/endpoint
- Changing a field's type
- Changing authentication requirements
- Changing error response format

**Non-breaking changes** (no version bump needed):
- Adding a new endpoint
- Adding a new optional field to response
- Adding a new optional parameter
- Changing rate limiting (more permissive)
- Adding a new enum value

---

## Error Responses

### Standard error envelope

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Human-readable description",
    "details": [
      {
        "field": "email",
        "message": "Must be a valid email address",
        "code": "INVALID_FORMAT"
      }
    ]
  }
}
```

### HTTP Problem Details (RFC 7807)

```json
{
  "type": "https://api.example.com/errors/validation-error",
  "title": "Validation Error",
  "status": 422,
  "detail": "The request body contains invalid fields",
  "instance": "/users/123",
  "errors": [
    {
      "field": "email",
      "message": "Must be a valid email address"
    }
  ]
}
```

### Error code conventions

Use consistent, machine-readable error codes across the entire API:

- `AUTHENTICATION_REQUIRED`
- `PERMISSION_DENIED`
- `RESOURCE_NOT_FOUND`
- `VALIDATION_ERROR`
- `CONFLICT`
- `RATE_LIMIT_EXCEEDED`
- `INTERNAL_ERROR`
- `SERVICE_UNAVAILABLE`

---

## Rate Limiting

### Strategies

| Strategy | How it works | Best for |
|----------|-------------|----------|
| **Token bucket** | Bucket fills at constant rate; each request consumes a token. Allows bursts up to bucket size | General API — allows bursts, protects average rate |
| **Sliding window** | Count requests in the last N seconds. Precise but memory-intensive | Tight rate enforcement |
| **Fixed window** | Count requests in the current period (e.g., this minute). Simple, but allows 2x at boundary | Simple use cases |
| **Leaky bucket** | Queue-based; requests processed at constant rate. Smooths traffic | Queue-based processing |

### Response headers

Standard `RateLimit-*` headers:

```
RateLimit-Limit: 1000
RateLimit-Remaining: 823
RateLimit-Reset: 1718123456
RateLimit-Policy: 1000;w=3600
```

When rate limit exceeded:
```
HTTP 429 Too Many Requests
Retry-After: 60
```

### What to rate limit

- Authentication endpoints (login, signup, password reset, 2FA) — prevent brute force
- Email/SMS sending — prevent spam and cost overruns
- Expensive endpoints (export, report generation, bulk operations)
- All endpoints (moderate limit) — protect infrastructure

---

## Common Risks

- Inconsistent error response format across endpoints
- No pagination on list endpoints that can return unbounded results
- Using `POST /createUser` and `GET /getUsers` instead of `POST /users` and `GET /users`
- GraphQL introspection enabled in production (exposes entire schema to attackers)
- GraphQL no depth limiting (vulnerable to deeply nested queries that crash the server)
- gRPC without `reserved` fields — field numbers reused accidentally, breaking consumers
- No rate limiting on authentication or expensive endpoints
- Versioning strategy not defined — "we'll figure it out for v2" means no plan for breaking changes

## Review questions

- Is the API resource naming consistent with REST/GraphQL/gRPC conventions?
- Are HTTP status codes used correctly and consistently?
- Is pagination cursor-based for large datasets? What is the default page size?
- Are error responses consistently structured across all endpoints?
- For GraphQL: is depth limiting configured? Is introspection disabled in production?
- For gRPC: are removed fields properly `reserved`? Is the error model defined?
- Is the API versioning strategy defined? How will breaking changes be communicated?
- Are rate limits defined for authentication, email/SMS, and expensive endpoints?
