# Clean Code Principles

## Focus areas

- **SOLID principles** applied at class and module level
- **Function design**: size, parameters, single responsibility
- **Naming**: domain-intent names for variables, functions, classes
- **Comments**: what to comment, what never to comment
- **Functional patterns**: purity, immutability, error handling
- **Dependency injection**: constructor, method, property injection

---

## SOLID Principles

### S — Single Responsibility Principle

A class or module should have exactly one reason to change. Each component owns one
coherent set of behaviors and data.

**Signals of violation:**
- A class has methods that deal with unrelated concerns (e.g., validation + persistence + formatting)
- Changing one feature forces changes in unrelated parts of the class
- The class name contains "And" or "Manager" or "Processor"

**Example — violation:**

```python
class OrderManager:
    def calculate_total(self, order): ...    # pricing
    def validate_inventory(self, order): ... # inventory
    def charge_card(self, order): ...        # payment
    def send_email(self, order): ...         # notification
```

**Example — refactored:**

```python
class OrderPricing:
    def calculate_total(self, order): ...

class InventoryValidator:
    def validate(self, order): ...

class PaymentProcessor:
    def charge(self, order): ...

class OrderNotifier:
    def send_confirmation(self, order): ...
```

**Review prompt:** Does each component in the design own exactly one concern? If a requirement
change touches three unrelated pieces of behavior in the same class, SRP is violated.

---

### O — Open/Closed Principle

Components should be open for extension but closed for modification. Add new behavior by
adding code, not by modifying existing tested code.

**Signals of violation:**
- Every new feature variant requires an `if` branch added to an existing function
- Adding a new payment method requires modifying a 500-line `process_payment()` function
- Strategy/plugin interfaces are absent where variants clearly exist

**Example — violation:**

```python
def calculate_discount(order, customer_type):
    if customer_type == "regular":
        return order.total * 0.05
    elif customer_type == "premium":
        return order.total * 0.10
    elif customer_type == "vip":
        return order.total * 0.15
```

**Example — refactored:**

```python
class DiscountStrategy(ABC):
    @abstractmethod
    def calculate(self, order): ...

class RegularDiscount(DiscountStrategy):
    def calculate(self, order): return order.total * 0.05

class PremiumDiscount(DiscountStrategy):
    def calculate(self, order): return order.total * 0.10

class VIPDiscount(DiscountStrategy):
    def calculate(self, order): return order.total * 0.15
```

**Review prompt:** Where would a new variant force modification of existing code instead of
extending a defined interface? Flag those as OCP violations.

---

### L — Liskov Substitution Principle

Subtypes must be substitutable for their base types without altering correctness.
Every derived class must honor the contract of its base class.

**Signals of violation:**
- A subclass overrides a method and raises `NotImplementedError` or returns `null`
- A subclass weakens preconditions (accepts wider input) or strengthens postconditions (returns narrower output)
- Type-checking or `isinstance` chains that special-case specific subclasses
- A subclass changes the semantics of the inherited method

**Example — violation:**

```python
class Rectangle:
    def set_width(self, w): self.width = w
    def set_height(self, h): self.height = h

class Square(Rectangle):
    def set_width(self, w):
        self.width = w
        self.height = w  # violates LSP: Square.set_width has a side effect
```

**Review prompt:** Can every proposed subtype replace its base type in all contexts
without surprising downstream code? Flag cases where the spec implies inheritance
that could break behavior.

---

### I — Interface Segregation Principle

Clients should not depend on interfaces they do not use. Many small, focused
interfaces are better than one large, monolithic interface.

**Signals of violation:**
- A class implements an interface but throws `NotImplementedError` for most methods
- A single interface mixes persistence, business rules, and presentation concerns
- Interface has more than 5-7 methods with unrelated purposes

**Example — violation:**

```python
class UserRepository(ABC):
    @abstractmethod
    def save(self, user): ...
    @abstractmethod
    def find_by_id(self, id): ...
    @abstractmethod
    def export_to_csv(self, users): ...  # doesn't belong here
    @abstractmethod
    def send_email(self, user): ...      # doesn't belong here
```

**Refactored:**

```python
class UserRepository(ABC):
    @abstractmethod
    def save(self, user): ...
    @abstractmethod
    def find_by_id(self, id): ...

class UserExporter(ABC):
    @abstractmethod
    def export(self, users, format): ...

class UserNotifier(ABC):
    @abstractmethod
    def send(self, user, message): ...
```

**Review prompt:** Does any component depend on methods it never uses? Are interfaces
narrow enough that consumers only pay for what they need?

---

### D — Dependency Inversion Principle

High-level modules should not depend on low-level modules. Both should depend on
abstractions. Abstractions should not depend on details — details depend on abstractions.

**Signals of violation:**
- A business rule module imports from a specific database library directly
- Changing the database requires rewriting business logic
- Concrete classes are depended on throughout the codebase rather than interfaces

**Example — violation:**

```python
class OrderService:
    def __init__(self):
        self.db = PostgresConnection(host="...", port=5432)

    def place_order(self, order):
        self.db.execute("INSERT INTO orders ...")
```

**Example — refactored:**

```python
class OrderRepository(ABC):
    @abstractmethod
    def save(self, order): ...

class PostgresOrderRepository(OrderRepository):
    def save(self, order): ...

class OrderService:
    def __init__(self, repo: OrderRepository):
        self.repo = repo

    def place_order(self, order):
        self.repo.save(order)
```

**Review prompt:** If the database, messaging queue, or external API changed tomorrow,
would business logic remain untouched? Flag direct dependencies on infrastructure.

---

## Function Design Heuristics

### Size and parameters

- Functions should fit on one screen (~20 lines maximum)
- Maximum 3 parameters; beyond that, introduce a parameter object or config struct
- A function should do one thing: if you need "and" to describe it, split it
- Cyclomatic complexity should stay below 10 per function

### Single responsibility litmus test

To test if a function has one responsibility, describe its behavior in one sentence:

- "It validates email format" — good
- "It validates email, saves user, and sends welcome email" — bad; split into three

### Side effect discipline

- Functions that query data should not modify state (Command-Query Separation)
- Functions that modify state should not return data used for control flow
- Flag any function whose name starts with `get_` that also writes to a database

---

## Naming Conventions

### Variables

- **Booleans**: use `is_`, `has_`, `should_`, `can_` prefixes (`is_active`, `has_permission`)
- **Collections**: use plural nouns (`users`, `pending_orders`)
- **Numbers/durations**: include unit in name (`timeout_ms`, `max_retry_count`, `file_size_bytes`)
- **Avoid**: single-letter names except in loops; abbreviations; numbered suffixes (`data2`, `tmp`)

### Functions

- **Verb + noun** pattern: `calculate_total()`, `send_notification()`, `validate_email()`
- **Predicate functions** (returning bool): start with `is_`, `has_`, `can_`
- **Factory functions**: start with `create_` or `build_`
- **Avoid**: vague verbs like `process()`, `handle()`, `manage()`, `do_`

### Classes

- **Noun or noun phrase**: `OrderRepository`, `PaymentProcessor`, `EmailTemplate`
- **Avoid**: suffixes like `-Manager`, `-Handler`, `-Util`, `-Helper` (they hide SRP violations)
- **Interface/abstract class naming**: use clear role names (`DiscountStrategy`, not `IDiscount`)

### Good vs bad examples

| Poor name | Good name | Why |
|-----------|-----------|-----|
| `d` | `elapsed_days` | Domain meaning is clear |
| `process()` | `export_invoices()` | Specific action is clear |
| `data` | `customer_records` | What kind of data is explicit |
| `flag` | `has_valid_email` | Boolean intent is explicit |
| `Manager` | `OrderWorkflow` | Specific role, not a catch-all |

---

## Comments and Documentation

### What to comment

- **Why, not what**: explain the reasoning behind non-obvious decisions, not restate code
- **Algorithm rationale**: when a complex algorithm was chosen over a simpler one
- **Workarounds**: document why a hack exists and under what conditions it can be removed
- **Magic numbers**: explain the origin of a constant (`# OWASP recommends 600k iterations for PBKDF2`)
- **Public APIs**: every public function/class should have a docstring describing contract, params, returns, exceptions

### What NEVER to comment

- Obvious code: `# increment counter` above `counter += 1` adds noise, not value
- Code that should be a function: a block comment explaining a block of code means "extract a function"
- Commented-out code: use version control, not commented-out blocks
- Changelog in file headers: use git log, not manual changelogs in file headers

### Self-documenting code

Code should be readable without comments for _what_ it does. Comments should only explain
_why_ it does it that way.

**Poor (comment explains what):**

```python
# check if user is active
if user.status == "active" and user.last_login > cutoff:
```

**Good (comment explains why, code explains what):**

```python
# Accounts in grace period keep access for 30 days after expiry (SLA §4.2)
if user.is_active_within_grace_period(cutoff):
```

### Comment quality signals

- **Stale comments**: comment contradicts the code it describes — the comment lies
- **Redundant comments**: comment restates exactly what the code says
- **Journal comments**: `# 2021-03-15: changed to X` — use git blame
- **TODO comments**: must have an owner and a due date or ticket reference, or they accumulate

---

## Functional Programming Patterns

### Pure functions

A function is pure if: (a) given the same inputs, it always returns the same output, and
(b) it has no observable side effects (no I/O, no mutation of external state).

```python
# Impure — depends on external state, modifies it
def apply_discount(order):
    if datetime.now().weekday() == 6:  # depends on external time
        order.total *= 0.9             # mutates input
    db.save(order)                      # side effect

# Pure — all inputs explicit, no side effects, no mutation
def apply_discount(order: Order, discount_rate: float) -> Order:
    return replace(order, total=order.total * (1 - discount_rate))
```

**Benefits:** testable without setup, parallelizable, cacheable, easy to reason about.

**Review prompt:** Are the spec's business rules expressed as pure transformations?
Does the design mix business logic with I/O?

### Immutability

Prefer immutable data structures. Instead of mutating objects, create new ones with
updated fields. This eliminates whole classes of bugs (unexpected state changes from
distant code, threading issues).

```python
# Mutation — risk of side effects
user.email = new_email

# Immutable update
updated_user = user.with_email(new_email)
# or, in languages without copy methods:
updated_user = User(**{**user.__dict__, "email": new_email})
```

**Review prompt:** Where does the spec assume mutable shared state? Could
critical paths use immutable records or value objects?

### Error handling

- **Result / Either types** over exceptions for expected failures: return a `Result` object
  that is either `Success(value)` or `Failure(error)` — forces callers to handle both cases
- **Exceptions** for truly exceptional circumstances: programmer error, unrecoverable infrastructure failure
- **Fail-fast**: validate inputs at system boundaries and return errors immediately; do not
  propagate invalid state through the system
- **Never swallow exceptions silently**: every `catch` block must log, re-raise, or handle
  the error meaningfully — an empty `catch` is a bug

```python
# Expected failure — use Result
def find_user(id: str) -> Result[User, NotFoundError]:
    user = db.query(id)
    if user is None:
        return Failure(NotFoundError(f"User {id} not found"))
    return Success(user)

# Truly exceptional — use exception
def allocate_memory(size: int) -> Buffer:
    buf = os.malloc(size)
    if buf is None:
        raise OutOfMemoryError()
    return buf
```

---

## Dependency Injection Patterns

### Constructor injection (preferred)

Dependencies are passed through the constructor. This makes dependencies explicit and
enforces that the object cannot exist without them.

```python
class OrderService:
    def __init__(self, repo: OrderRepository, notifier: Notifier):
        self._repo = repo
        self._notifier = notifier
```

### Method injection

Dependencies are passed as method parameters. Use when the dependency varies per call
or is only needed for a single method.

```python
class OrderService:
    def place_order(self, order: Order, payment_gateway: PaymentGateway):
        ...
```

### Property injection

Dependencies are set via properties after construction. Avoid when possible — it allows
objects to exist in an incomplete state. Use only when the DI framework requires it or
when there's a sensible default.

```python
service = OrderService()
service.payment_gateway = StripeGateway()  # fragile — forgettable
```

### What to inject vs what to instantiate

| Inject as dependency | Instantiate directly |
|----------------------|---------------------|
| Database connections | Value objects (Email, Money) |
| External APIs | DTOs / data classes |
| File system access | Collections (list, dict) |
| Clock / time source | Simple configuration constants |
| Random number generators | Language primitives |
| Message queues | Error types |

---

## Common Risks

- Mixing business logic, persistence, and presentation in the same class
- Functions with hidden side effects (a getter that writes to the database)
- Comments that contradict code (stale comments are worse than no comments)
- Mutable shared state accessed from multiple places without clear ownership
- Deep inheritance hierarchies (3+ levels) that make behavior tracing difficult
- Names that require reading the implementation to understand (`process_data()`)
- Commented-out code blocks left as "just in case" archives
- Direct instantiation of infrastructure dependencies in business logic

## Review questions

- Is every function name a verb that describes exactly what it does?
- Would a new team member reading a class name understand its responsibility without opening the file?
- Does any function exceed 20 lines, 3 parameters, or cyclomatic complexity of 10?
- Are there commented-out code blocks that should be deleted?
- Do comments explain "why" rather than "what"?
- Are all dependencies injected rather than constructed inside business logic?
- Can business rules be tested without starting a database or external service?
- Are there boolean parameters that should be separate methods? (`save(user, True)` — what is True?)
- Does any abstract class or interface contain methods that some subclasses cannot implement?
