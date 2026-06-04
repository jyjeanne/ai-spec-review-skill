# Refactoring Catalog

## Organization

Refactorings are grouped by the code smell they address. Each entry provides:
- The smell that triggers the refactoring
- What the refactoring does
- When to apply it
- When to avoid it
- A before/after code sketch

---

## Bloater Smells

### 1. Extract Method

**Smell:** Long Method — a method does multiple things, sections separated by comments.

**What:** Move a cohesive block of code into a new, well-named method. The original
method calls the new method.

**When to apply:** A code section can be described with a clear, concise name. The
section has few local variable dependencies.

**When to avoid:** The section has so many local variable dependencies that the new
method's parameter list would be as long as the original. Too many extracted methods
create "ravioli code" — hard to follow the flow.

```python
# Before
def process_order(order):
    # Validate order
    if not order.items:
        raise ValueError("Empty order")
    if order.total <= 0:
        raise ValueError("Invalid total")
    # Calculate discount
    discount = 0
    if order.customer.is_premium:
        discount = order.total * 0.10
    # Apply and save
    order.total -= discount
    db.save(order)

# After
def process_order(order):
    validate_order(order)
    discount = calculate_discount(order)
    order.total -= discount
    db.save(order)

def validate_order(order):
    if not order.items:
        raise ValueError("Empty order")
    if order.total <= 0:
        raise ValueError("Invalid total")

def calculate_discount(order):
    if order.customer.is_premium:
        return order.total * 0.10
    return 0
```

### 2. Extract Class

**Smell:** Large Class — too many responsibilities, fields cluster into groups.

**What:** Move a cohesive subset of fields and methods into a new class.

**When to apply:** Subsets of fields are used together in subsets of methods. The class
has responsibilities that change for different reasons.

**When to avoid:** The class is cohesive but just long — extraction would create tight
coupling between the original and extracted class.

### 3. Replace Method with Method Object

**Smell:** Long Method that cannot be simplified by Extract Method because it uses many
local variables that would need to become parameters.

**What:** Move the entire method into a new class. Local variables become instance
fields. The method's logic can then be split into smaller methods on the new class.

**When to apply:** Extract Method fails because of too many local variables.

**When to avoid:** The method is simple enough with Extract Method.

### 4. Introduce Parameter Object

**Smell:** Long Parameter List — 3+ parameters that travel together through multiple
methods, or Data Clumps.

**What:** Group related parameters into a value object and pass that instead.

**When to apply:** The same group of parameters appears in 3+ method signatures.

**When to avoid:** The parameters are not logically related — forcing them into an
object creates a meaningless container.

```python
# Before
def create_event(start_date, end_date, title, description, location):
    ...

def update_event(event_id, start_date, end_date, title, description, location):
    ...

def send_reminder(user, start_date, end_date, title):
    ...

# After
class DateRange:
    def __init__(self, start, end):
        if start > end:
            raise ValueError("Start must be before end")
        self.start = start
        self.end = end

class EventDetails:
    def __init__(self, title, description, location):
        self.title = title
        self.description = description
        self.location = location

def create_event(dates: DateRange, details: EventDetails):
    ...

def update_event(event_id, dates: DateRange, details: EventDetails):
    ...

def send_reminder(user, dates: DateRange, title: str):
    ...
```

### 5. Remove Middle Man

**Smell:** A class delegates all its work to another class — it's just a pass-through.

**What:** Have callers use the delegate directly.

**When to apply:** The middle-man class has no behavior of its own; every method just
delegates.

**When to avoid:** The middle-man provides important isolation (Adapter, Facade pattern).
The delegate will likely change and the middle-man absorbs that change.

---

## Object-Oriented Abuse Smells

### 6. Replace Conditional with Polymorphism

**Smell:** Switch statements or `if/elif/else` chains based on type code.

**What:** Create a base class/interface with a method for the varied behavior. Each
type code value becomes a subclass that implements the method.

**When to apply:** The same type-code switch appears in multiple places. New type codes
are expected.

**When to avoid:** The type code values are fixed (e.g., days of the week) and the
switch appears in only one place. Adding classes for a few simple variants is
over-engineering.

```python
# Before
def get_shipping_cost(order, carrier):
    if carrier == "fedex":
        return order.weight * 2.5 + 5
    elif carrier == "ups":
        return order.weight * 2.0 + 3
    elif carrier == "usps":
        return order.weight * 1.5 + 2

# After
class ShippingCalculator(ABC):
    @abstractmethod
    def calculate(self, order) -> float: ...

class FedExCalculator(ShippingCalculator):
    def calculate(self, order): return order.weight * 2.5 + 5

class UPSCalculator(ShippingCalculator):
    def calculate(self, order): return order.weight * 2.0 + 3

class USPSCalculator(ShippingCalculator):
    def calculate(self, order): return order.weight * 1.5 + 2
```

### 7. Replace Type Code with State/Strategy

**Smell:** Object behavior changes based on internal state represented by a type code.

**What:** Extract state-specific behavior into State/Strategy objects. The context
delegates to the current state object.

**When to apply:** The type code changes at runtime. Behavior varies meaningfully by state.

**When to avoid:** The type code never changes after construction. Use Replace Conditional
with Polymorphism instead.

### 8. Replace Inheritance with Delegation

**Smell:** A subclass uses only a fraction of the inherited interface, or inherits
behavior it doesn't need.

**What:** Replace inheritance with composition. The former subclass holds a reference
to the former superclass and delegates only the needed methods.

**When to apply:** The subclass violates Liskov Substitution Principle. The subclass
doesn't need most inherited methods.

**When to avoid:** The subclass truly "is-a" subtype and uses the full interface.

### 9. Collapse Hierarchy

**Smell:** A superclass and subclass are nearly identical — the subclass adds little
value.

**What:** Merge the subclass into the superclass (or vice versa) and delete the redundant class.

**When to apply:** The subclass overrides few methods and adds little behavior.

**When to avoid:** The subclass exists to implement an interface pattern (Strategy,
State). The subclass is part of a broader hierarchy.

---

## Change Preventer Smells

### 10. Extract Interface

**Smell:** Multiple classes share a subset of their interface but have no common type.
Clients want to treat them uniformly.

**What:** Create an interface (or abstract base class) with the shared method signatures.
Have the classes implement it.

**When to apply:** Clients need to work with different implementations through a common
contract. Adding a new implementation is likely.

**When to avoid:** Only one implementation exists and another is speculative. The shared
interface would have only one method.

### 11. Parameterize Method

**Smell:** Several methods do similar things with different values hardcoded in their
bodies.

**What:** Replace the similar methods with one method that takes a parameter.

**When to apply:** The methods differ only by constants or simple values, not logic.

**When to avoid:** The methods have different enough logic that parameterizing creates
a complex conditional internally.

### 12. Replace Parameter with Explicit Methods

**Smell:** A method has a boolean or enum parameter that switches between two entirely
different behaviors.

**What:** Split into separate methods — one for each behavior.

**When to apply:** The parameter divides the method into mostly non-overlapping code
paths. Callers always pass a constant value.

**When to avoid:** The parameter only affects a small part of the method's behavior.

```python
# Before
def save(user, send_welcome_email=False):
    db.save(user)
    if send_welcome_email:
        email_service.send_welcome(user.email)

# After
def save(user):
    db.save(user)

def save_and_send_welcome(user):
    db.save(user)
    email_service.send_welcome(user.email)
```

---

## Dispensable Smells

### 13. Remove Dead Code

**Smell:** Unreachable code, unused variables, methods that are never called.

**What:** Delete it.

**When to apply:** Always. Dead code adds cognitive load, confuses readers, and may
hide bugs (someone might think it's live).

**When to avoid:** The code is a deliberate stub that will be implemented next sprint
(track with a ticket). The code documents an alternative approach preserved in an ADR
(delete the code, keep the ADR).

### 14. Inline Method

**Smell:** A method's body is as clear as its name. The method adds indirection without
clarity.

**What:** Replace calls to the method with the method's body, then delete the method.

**When to apply:** The method is trivial (1-2 lines) and its name doesn't add meaning
beyond the body.

**When to avoid:** The method provides an abstraction that may change. The method is
part of a public API.

### 15. Inline Class

**Smell:** A class does almost nothing — it's a thin wrapper with no meaningful behavior.

**What:** Move all features into the consuming class and delete the wrapper.

**When to apply:** The class has no behavior of its own and one consumer.

**When to avoid:** The class is an Adapter or Facade isolating a third-party dependency.
The class is the start of a value object that will grow.

### 16. Remove Subclass

**Smell:** A subclass adds no meaningful difference from its parent.

**What:** Merge the subclass's features into the parent, then use a field or parameter
to distinguish.

**When to apply:** The subclass overrides no methods and adds only a field.

**When to avoid:** The subclass is part of a strategy/state pattern with other meaningful
subclasses.

---

## Coupling Smells

### 17. Move Method

**Smell:** A method uses another class's data more than its own class's data (Feature Envy).

**What:** Move the method to the class whose data it uses most. Delegate from the original
if needed.

**When to apply:** The method accesses more fields/methods from another class than from
its own.

**When to avoid:** Moving the method would violate the target class's cohesion (it
doesn't belong there either).

### 18. Move Field

**Smell:** A field is used more by another class than by its owning class.

**What:** Move the field to the class that uses it most.

**When to apply:** Clear evidence from usage patterns (count field accesses from each class).

**When to avoid:** The field is part of the class's core identity.

### 19. Hide Delegate

**Smell:** A client calls `a.getB().getC().doSomething()` — exposing the chain of
delegates.

**What:** Create a method on `A` that delegates to `C` so that clients call
`a.doSomething()`.

**When to apply:** The delegate chain is long or likely to change. Clients shouldn't
know about the intermediate objects.

**When to avoid:** The intermediate objects are stable and the chain provides useful
flexibility.

### 20. Introduce Assertion

**Smell:** A section of code assumes something about the state (e.g., "this value can't
be null here") but never checks.

**What:** Add an explicit assertion that documents and enforces the assumption.

**When to apply:** The assumption is not obvious from context and would cause bugs if violated.

**When to avoid:** The assumption is already enforced by the type system (e.g.,
non-nullable types).

---

## Simplification Smells

### 21. Replace Nested Conditional with Guard Clauses

**Smell:** Deeply nested `if/else` where one condition means "bail out early".

**What:** Use early `return`, `continue`, or `raise` for the exceptional case so the
main logic stays at the top level.

**When to apply:** One branch of a conditional is the exceptional/error case.

**When to avoid:** Both branches are equally important to the logic flow.

```python
# Before
def get_pay(employee):
    if employee.is_active:
        if employee.has_bonus:
            return employee.salary + employee.bonus
        else:
            return employee.salary
    else:
        return 0

# After
def get_pay(employee):
    if not employee.is_active:
        return 0
    if employee.has_bonus:
        return employee.salary + employee.bonus
    return employee.salary
```

### 22. Decompose Conditional

**Smell:** Complex boolean expressions in `if` conditions that are hard to read.

**What:** Extract the condition into a named method or variable that explains the intent.

**When to apply:** The condition requires mental parsing to understand.

**When to avoid:** The condition is trivial (`if user is not None`).

```python
# Before
if user.registered_at > six_months_ago and user.purchase_count > 5 and not user.has_outstanding_balance:
    apply_loyalty_discount(order)

# After
if is_eligible_for_loyalty_discount(user):
    apply_loyalty_discount(order)

def is_eligible_for_loyalty_discount(user):
    return (
        user.registered_at > six_months_ago
        and user.purchase_count > 5
        and not user.has_outstanding_balance
    )
```

### 23. Replace Magic Number with Named Constant

**Smell:** Numeric or string literals that carry implicit meaning.

**What:** Replace with a named constant that explains the meaning and origin.

**When to apply:** The literal's meaning isn't obvious from context.

**When to avoid:** The literal is self-evident (`0` as initial counter, `1` as increment).

```python
# Before
if user.failed_login_attempts >= 5:
    lock_account(user)

# After
MAX_LOGIN_ATTEMPTS = 5  # Per security policy §3.2

if user.failed_login_attempts >= MAX_LOGIN_ATTEMPTS:
    lock_account(user)
```

### 24. Replace Array with Object

**Smell:** An array or tuple is used where each position has a different meaning.

**What:** Replace with a class or named tuple where each element has a named field.

**When to apply:** The array positions carry implicit meaning that developers must remember.

**When to avoid:** The array is a simple homogenous collection (list of names).

```python
# Before
customer = ["Alice", "alice@example.com", "premium", 1420]

# After
class Customer:
    def __init__(self, name: str, email: str, tier: str, loyalty_points: int):
        self.name = name
        self.email = email
        self.tier = tier
        self.loyalty_points = loyalty_points
```

### 25. Encapsulate Collection

**Smell:** A class exposes a mutable collection directly (`list`, `dict`).

**What:** Provide read-only access (return a copy or read-only view) and add methods
for modification (`add_item()`, `remove_item()`).

**When to apply:** The collection is a field on a class and callers can mutate it freely.

**When to avoid:** The collection is intentionally a shared data structure (e.g., a cache).

```python
# Before
class Order:
    def __init__(self):
        self.items = []

# After
class Order:
    def __init__(self):
        self._items = []

    @property
    def items(self):
        return tuple(self._items)  # immutable copy

    def add_item(self, item):
        self._items.append(item)

    def remove_item(self, item_id):
        self._items = [i for i in self._items if i.id != item_id]
```

---

## Smell → Refactoring Quick Reference

| Smell | Primary Refactoring | Alternative |
|-------|-------------------|-------------|
| Long Method (>20 lines) | Extract Method | Replace Method with Method Object |
| Large Class (>200 lines) | Extract Class | Extract Subclass |
| Long Parameter List (>3) | Introduce Parameter Object | Replace Parameter with Explicit Methods |
| Feature Envy | Move Method | Extract Method on target class |
| Divergent Change | Extract Class | — |
| Shotgun Surgery | Move Method | Inline Class |
| Duplicate Code | Extract Method | Pull Up Method (if in subclasses) |
| Switch/If on type code | Replace Conditional with Polymorphism | Replace Type Code with Strategy |
| Complex Boolean | Decompose Conditional | Introduce Assertion |
| Magic Number | Replace Magic Number with Named Constant | — |
| Nested Conditional | Replace with Guard Clauses | Decompose Conditional |
| Dead Code | Remove Dead Code | — |
| Commented-Out Code | Remove Dead Code | Document in ADR |
| Data Clumps | Introduce Parameter Object | Extract Class |
| Primitive Obsession | Replace Data Value with Object | Introduce Parameter Object |
| Mutable Collection Exposed | Encapsulate Collection | Replace with Immutable Object |
| Middle Man | Remove Middle Man | Inline Class |
| Lazy Class | Inline Class | Collapse Hierarchy |

## Review Questions

- Which smells are predicted by the specification's implied code structure?
- Will the data model use primitives where value objects would prevent invalid states?
- Are there type-code enums that will lead to switch statements scattered across the codebase?
- Are there mutable collections exposed through component boundaries?
- Is the plan to refactor when smells emerge, or is prevention designed into the architecture?
