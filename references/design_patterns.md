# Design Patterns Reference

## Review rule

- Use patterns only when they simplify change, isolate complexity, or clarify responsibilities.
- Flag patterns that are implied by the problem but absent from the design when their absence
  creates risk.
- Flag patterns that are present but inappropriate — over-engineering a simple problem is
  as harmful as under-engineering a complex one.

---

## Creational Patterns

### Factory / Factory Method

**When to use:** Object creation has branching rules (different configs per environment,
different implementations per customer tier), or construction logic is duplicated across
multiple call sites.

**When NOT to use:** The object has a simple constructor with no branching; a factory adds
indirection without benefit for single-implementation objects.

**Risk signal if absent:** The same `if platform == "aws" ... else if platform == "gcp" ...`
switch appears in 5 different places.

**Risk signal if misapplied:** A factory that always returns the same concrete type with no
variation — the factory is ceremonial.

```python
# Without factory — scattered construction logic
def create_storage():
    if env == "prod":
        return S3Storage(bucket="prod-bucket", encryption="AES256")
    else:
        return LocalStorage(base_dir="/tmp")

# With factory — centralized, testable
class StorageFactory:
    @staticmethod
    def create(env: str) -> Storage:
        config = StorageConfig.for_environment(env)
        return config.build()
```

### Builder

**When to use:** Objects have many optional parameters, complex construction steps, or
require validation across multiple fields before the object is valid.

**When NOT to use:** Objects with 2-3 required fields — a constructor or factory function
is sufficient.

**Risk signal if absent:** Functions with 8+ parameters, half of which are `None` or defaults.

### Singleton

**When to use:** A resource that must be shared across the entire application (logging
facade, configuration registry, connection pool manager). Prefer dependency injection
of a single instance over a global-access singleton.

**When NOT to use:** As a convenient global variable — Singletons hide dependencies,
make testing difficult, and couple the entire codebase to a global state.

**Risk signal if misapplied:** Any class accessed via `ClassName.getInstance()` that could
instead be passed via constructor.

### Object Pool

**When to use:** Object creation is expensive (database connections, threads, large
buffers) and objects can be reused after resetting state.

**When NOT to use:** Objects are cheap to create (most application objects); pooling
adds complexity with no benefit.

---

## Structural Patterns

### Adapter

**When to use:** You need to integrate with a third-party library or legacy system whose
interface does not match your domain's expected interface. The adapter translates one
interface to another.

**When NOT to use:** The interfaces are close enough that a thin wrapper suffices; adapters
that just pass through every call unchanged.

**Risk signal if absent:** Third-party API types leak into domain logic — business rules
import from `stripe`, `twilio`, or `aws-sdk` directly.

```python
# Domain expects this interface
class PaymentGateway(ABC):
    @abstractmethod
    def charge(self, amount: Money, token: str) -> PaymentResult: ...

# Adapter translates Stripe's API to domain interface
class StripeAdapter(PaymentGateway):
    def __init__(self, stripe_client): self._stripe = stripe_client
    def charge(self, amount: Money, token: str) -> PaymentResult:
        stripe_result = self._stripe.PaymentIntent.create(
            amount=amount.cents, currency=amount.currency, source=token
        )
        return PaymentResult.from_stripe(stripe_result)
```

### Facade

**When to use:** A complex subsystem (multiple classes, complex interactions) needs a
simplified interface for common use cases. The facade hides subsystem complexity.

**When NOT to use:** The subsystem is already simple — a facade that mirrors the
subsystem interface one-to-one adds no value.

**Risk signal if absent:** Callers need to orchestrate 5+ subsystem objects for a
single operation.

### Decorator

**When to use:** You need to add behavior to objects dynamically without affecting
other instances of the same class. Common for: logging, metrics, caching, retry,
authorization checks.

**When NOT to use:** The behavior applies to all instances equally — put it in the
base class instead. Deep nesting of decorators (>3) makes debugging difficult.

```python
class RetryablePaymentGateway(PaymentGateway):
    def __init__(self, inner: PaymentGateway, max_retries: int = 3):
        self._inner = inner
        self._max_retries = max_retries

    def charge(self, amount: Money, token: str) -> PaymentResult:
        for attempt in range(self._max_retries):
            try:
                return self._inner.charge(amount, token)
            except TransientError:
                if attempt == self._max_retries - 1:
                    raise
                time.sleep(2 ** attempt)
```

### Proxy

**When to use:** You need to control access to an object (lazy loading, access control,
remote proxy for distributed objects, virtual proxy for expensive resources).

**When NOT to use:** Simple pass-through — use the real object directly. Proxies that
add no additional behavior are dead code.

### Composite

**When to use:** You have tree structures (menus, file systems, organizational charts,
UI component trees) where clients should treat individual objects and compositions uniformly.

**When NOT to use:** The hierarchy is shallow or fixed — a composite adds unnecessary
abstraction. Objects in the hierarchy don't share a common interface.

---

## Behavioral Patterns

### Strategy

**When to use:** Business behavior varies by rule set, channel, customer segment, or
region. You need to swap algorithms at runtime.

**When NOT to use:** Only one algorithm exists and is unlikely to change; the strategy
interface has a single implementation.

**Risk signal if absent:** Long `if/elif/else` chains or `switch` statements that select
behavior based on type codes or enums.

### Observer / Publish-Subscribe

**When to use:** One object's state change should trigger actions in multiple other
objects without tight coupling. Event-driven architectures.

**When NOT to use:** The "observer" is always the same single consumer — use a direct
call. Synchronous notification of observers can create cascading failures.

**Risk signal if absent:** Business logic that manually calls 5+ downstream services
after every state change.

### Chain of Responsibility

**When to use:** A request passes through a chain of handlers, each deciding whether to
process it or pass it along. Common for: middleware pipelines (auth → validation →
rate-limiting → handler), approval workflows, request preprocessing.

**When NOT to use:** The order of handlers is fixed and always the same — a pipeline
with explicit composition may be clearer. Handlers that never pass to the next.

```python
class Middleware(ABC):
    @abstractmethod
    def handle(self, request, next_handler): ...

class AuthMiddleware(Middleware):
    def handle(self, request, next_handler):
        if not request.is_authenticated:
            return Response(401)
        return next_handler(request)
```

### Command

**When to use:** You need to parameterize objects with actions, queue operations,
support undo/redo, or log operations for audit trails.

**When NOT to use:** The operation is a simple function call with no need for queuing,
logging, or undo. Overkill for CRUD operations.

### State

**When to use:** An object's behavior changes based on its internal state, and the number
of states is significant. State-specific behavior is encapsulated in state classes.

**When NOT to use:** Only 2-3 states with simple transitions — a state field + switch
is simpler. The states don't have meaningfully different behavior.

### Template Method

**When to use:** An algorithm's structure is fixed but some steps vary by subclass.
The base class defines the skeleton; subclasses fill in the details.

**When NOT to use:** The algorithm structure itself varies — use Strategy instead.
Subclasses need to change the skeleton, not just the steps.

---

## Resilience Patterns

### Circuit Breaker

**When to use:** A downstream service call can fail or hang; you want to fail fast after
a threshold of failures and periodically test recovery.

**When NOT to use:** Operations that never fail (pure computation). Wrapping every
external call without a bypass mechanism.

```python
class CircuitBreaker:
    def __init__(self, failure_threshold=5, recovery_timeout=60):
        self._failures = 0
        self._state = "closed"  # closed | open | half_open
        self._last_failure = None

    def call(self, fn):
        if self._state == "open":
            if (time.time() - self._last_failure) < self._recovery_timeout:
                raise CircuitBreakerOpenError()
            self._state = "half_open"
        try:
            result = fn()
            if self._state == "half_open":
                self._state = "closed"
                self._failures = 0
            return result
        except Exception:
            self._failures += 1
            self._last_failure = time.time()
            if self._failures >= self._failure_threshold:
                self._state = "open"
            raise
```

**Risk signal if absent:** Service A calls Service B synchronously on every request;
if B is down or slow, A's threads all block and A becomes unavailable.

### Bulkhead

**When to use:** Partition resources so that a failure in one area does not cascade to
others. Common: separate thread pools for different call types, connection pool isolation.

**When NOT to use:** The system has no shared resources that could be exhausted; total
isolation is unnecessary.

### Retry with Backoff

**When to use:** Transient failures (network blip, temporary overload) should be retried.
Use exponential backoff with jitter to avoid thundering herd.

**When NOT to use:** Non-idempotent operations (charge credit card) — retry may duplicate.
Non-transient failures (404 Not Found, 401 Unauthorized) should not be retried.

### Timeout

**When to use:** Every external call should have a deadline. No call should hang
indefinitely.

**When NOT to use:** There is no scenario where a missing timeout is acceptable — every
network call, database query, or external API call must have a timeout.

### Fallback

**When to use:** When a primary service is unavailable, degrade gracefully to a cached
result, default value, or simplified behavior.

**When NOT to use:** Fallback that returns incorrect data — a stale cache is better
than no response; wrong data is worse than an error.

---

## Data Patterns

### Repository

**When to use:** Persistence concerns need isolation from domain logic. The domain should
not know whether data comes from Postgres, a file, or an API.

**When NOT to use:** Simple CRUD with no domain logic — an ORM model is sufficient.
The repository mirrors the ORM interface method-for-method.

**Risk signal if absent:** Business logic calls `db.execute("SELECT ...")` or
`Model.objects.filter(...)` directly.

### CQRS (Command Query Responsibility Segregation)

**When to use:** Read and write workloads have different scaling, latency, or data shape
requirements. Reads are frequent and complex; writes are fewer but business-critical.

**When NOT to use:** Simple CRUD with similar read and write shapes. The overhead of
separate models and eventual consistency is not justified.

### Event Sourcing

**When to use:** You need a complete, auditable history of all state changes. The current
state is derived from an append-only event log. Full audit trail, temporal queries,
and event replay capability are required.

**When NOT to use:** Simple state persistence with no audit requirements. Eventual
consistency is unacceptable. The event log size is unbounded and costly.

### Saga

**When to use:** A distributed transaction spans multiple services; each step has a
compensating action to undo if a later step fails. Maintains eventual consistency.

**When NOT to use:** All operations are within a single database — use a local ACID
transaction.

### Outbox

**When to use:** You need to reliably publish messages/events as part of a database
transaction. The outbox table is written in the same transaction; a separate process
publishes from the outbox.

**When NOT to use:** Eventual consistency of event publishing is acceptable; message
loss is tolerable (rarely the case). Single-database, no messaging.

### Unit of Work

**When to use:** Multiple repository operations must be committed as a single transaction.
The Unit of Work tracks changes and coordinates the commit.

**When NOT to use:** Single-repository operations; ORMs that already provide session/
transaction management (SQLAlchemy session, Entity Framework DbContext).

---

## Architecture Patterns

### Hexagonal Architecture (Ports & Adapters)

**When to use:** The core domain must remain isolated from frameworks, UI, databases,
and external providers. The domain defines ports (interfaces); adapters implement them.

**When NOT to use:** Simple applications where the domain logic is minimal and isolation
overhead exceeds benefits. The framework IS the application (e.g., simple CMS).

**Risk signal if absent:** Domain logic imports from `flask`, `django`, `express`,
`react`, or database-specific libraries directly.

### Event-Driven Architecture

**When to use:** Workflows benefit from decoupling, asynchronous processing, or fan-out
reactions. Components communicate through events rather than direct calls.

**When NOT to use:** Simple request-response workflows with no need for decoupling.
The overhead of event infrastructure (broker, schema registry, dead letter queues)
is not justified.

**Risk signal if absent:** Synchronous chains of 4+ service calls creating fragile
coupling and poor resilience.

### CQRS with Event Sourcing

**When to use:** Combined, these provide separate optimized read models, a complete
event history, and the ability to rebuild any read model from events.

**When NOT to use:** Simple or moderate complexity systems — the combined complexity
is high and only justified for systems with significant scaling or audit requirements.

---

## Anti-Patterns Catalog

### God Object / God Service

A single class or service that knows too much and does too much. Handles business logic,
persistence, validation, notifications, and formatting.

**Detection:** A class with 20+ public methods covering unrelated concerns. Name often
contains "Manager", "Processor", or "Service" without qualification.

**Fix:** Split along responsibility boundaries using SRP. Extract cohesive subsets into
dedicated classes.

### Leaky Abstraction

An abstraction that exposes implementation details that should be hidden. Callers need
to understand the underlying implementation to use the abstraction correctly.

**Detection:** Callers catch implementation-specific exceptions (`psycopg2.Error` in
domain code), configure implementation-specific settings, or pass through arguments
destined for the implementation.

**Fix:** Translate implementation-specific concepts at the adapter boundary. Create
domain exceptions that wrap implementation details.

### Golden Hammer

Applying a familiar pattern or technology to every problem regardless of fit. "We use
microservices for everything" or "we put everything in a blockchain."

**Detection:** The team uses the same architectural choice for components with vastly
different requirements. The pattern is used before the problem is understood.

**Fix:** Evaluate each problem independently. Maintain a decision journal: why was
this pattern chosen for this specific problem?

### Inappropriate Abstraction

An abstraction created at the wrong level or for the wrong reason. DRY applied
prematurely to code that is incidentally similar but semantically different.

**Detection:** An interface with one implementation. A parameter that switches between
entirely different code paths. "We'll make this generic in case we need it later."

**Fix:** Wait for three concrete use cases before abstracting (Rule of Three). Resist
premature generalization. Prefer duplication over wrong abstraction — the wrong
abstraction is costlier to undo than duplicated code.

### Premature Optimization

Optimizing before measuring. Introducing complexity (caching, custom data structures,
denormalization) without evidence of a performance problem.

**Detection:** Complex caching strategies in a spec with no performance targets.
Custom collection classes replacing standard library equivalents without benchmarks.

**Fix:** Define performance targets first. Measure. Optimize only what's proven slow.

### Cargo Cult Programming

Using patterns or code without understanding why they work or whether they apply.
Copying Stack Overflow solutions verbatim without adapting to context.

**Detection:** Patterns used without the problem they solve being present. Code that
no team member can explain the rationale for.

**Fix:** Every pattern, library, and architectural choice must have a documented
rationale. ADRs for significant decisions.

### Copy-Paste Programming

Duplicating code blocks instead of extracting shared logic. Each copy may diverge
slightly, creating subtle bugs.

**Detection:** The same 10+ lines of logic appear in 3+ places with minor variations.
Bug fixes must be applied to multiple locations.

**Fix:** Extract common logic. If variations exist, use Strategy or Template Method
to encapsulate the differences. Parameterize the shared code.

---

## Decision Guide

| Problem | Pattern |
|---------|---------|
| Same construction logic in 5+ places | Factory |
| 10 optional constructor parameters | Builder |
| Third-party API leaking into domain | Adapter |
| Complex subsystem, common use cases | Facade |
| Add behavior without modifying class | Decorator |
| Multiple algorithms, switch at runtime | Strategy |
| State change triggers many actions | Observer |
| Request preprocessing pipeline | Chain of Responsibility |
| Undo/redo or operation queuing | Command |
| Behavior changes with object state | State |
| Downstream service is unreliable | Circuit Breaker + Retry |
| Isolation from framework/database | Hexagonal Architecture |
| Read/write workloads differ radically | CQRS |
| Full audit trail of all changes | Event Sourcing |
| Distributed transaction across services | Saga |
| Reliable message publishing with DB tx | Outbox |

## Review questions

- Which pattern best isolates the volatile part of the design?
- Where is domain logic directly coupled to infrastructure (database, framework, transport)?
- Would introducing a pattern reduce complexity, or only add ceremony?
- Is every pattern in the design traceable to a specific problem it solves?
- Are there patterns applied without the problem they solve being present? (Cargo Cult)
- Where does the spec imply a pattern by problem structure but omit it?
- Are any anti-patterns (God Object, Leaky Abstraction, Inappropriate Abstraction) present?
- For every abstraction in the design: what is the second and third concrete use case?
