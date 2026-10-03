# The Swift Language — Reference for `swift-language-expert`

**Scope:** The Swift *language* as of **Swift 6.2** (released 15 September 2025), with history back to 5.9. This document is for an agent that reviews and advises on **idiomatic Swift** — language, standard library, concurrency model, package manifest, testing, interop. UI frameworks (SwiftUI/UIKit) are out of scope and covered by other agents.

**Version labels:** Features are tagged with the Swift version that introduced them and the relevant Swift Evolution proposal (`SE-NNNN`). "Upcoming feature" means it ships behind a flag before becoming default in a later language mode.

**Language modes vs. compiler versions:** Swift decouples the *compiler version* (5.9, 5.10, 6.0, 6.1, 6.2) from the *language mode* (`-swift-version 4 | 4.2 | 5 | 6`). A Swift 6.2 compiler can still build code in language mode 5. **Language mode 6** is what turns on complete data-race checking as errors. Individual features can be opted into early with `-enable-upcoming-feature <Name>`.

---

## 1. Concurrency (the largest and most consequential area)

Swift concurrency is a *compile-time-checked*, cooperative model built on `async`/`await`, structured tasks, and actors. The defining goal of Swift 6 is **compile-time data-race safety** ("complete concurrency checking"). Swift 6.2 substantially softens the ergonomics of that model ("approachable concurrency").

### 1.1 `async`/`await` (Swift 5.5, SE-0296)

```swift
func fetchUser(id: Int) async throws -> User { ... }

let user = try await fetchUser(id: 42)
```

- `async` marks a function that can suspend; `await` marks each *potential suspension point* (a possible thread hop / interleaving).
- `await` is a visible marker that state may have changed across the call — reviewers should treat every `await` as a memory barrier for reasoning about invariants.
- Async functions do **not** guarantee they resume on the same thread (pre-6.2). Swift 6.2 changes this default (see 1.9).
- `async` properties (read-only) and `async` subscripts exist; `async` initializers do not (use a static async factory).

### 1.2 Structured concurrency (Swift 5.5, SE-0304)

The core idea: child tasks have a **bounded lifetime** tied to a lexical scope, and the scope cannot exit until all children complete or are cancelled. This gives automatic propagation of cancellation, errors, priority, and task-local values.

**`async let`** (SE-0317) — concurrent bindings; the child runs immediately, you `await` at the point of use:

```swift
async let a = fetchA()      // starts now
async let b = fetchB()      // starts now, concurrently
let (x, y) = try await (a, b)   // both awaited here
```
If the scope exits without awaiting an `async let`, the child is implicitly cancelled and awaited.

**Task groups** — dynamic fan-out where the number of children is data-dependent:

```swift
let results = try await withThrowingTaskGroup(of: Item.self) { group in
    for id in ids {
        group.addTask { try await fetchItem(id) }
    }
    var items: [Item] = []
    for try await item in group {   // AsyncSequence over child results
        items.append(item)
    }
    return items
}
```
Variants: `withTaskGroup` (non-throwing), `withThrowingTaskGroup`, `withDiscardingTaskGroup` / `withThrowingDiscardingTaskGroup` (SE-0381, Swift 5.9 — for groups whose children return `Void`, avoids unbounded memory growth).

**Unstructured tasks** — escape the current scope; the caller is responsible for their lifetime:

```swift
let handle = Task { await doWork() }          // inherits actor + priority + task-locals
let detached = Task.detached { await doWork() } // inherits NOTHING — usually a smell
let value = await handle.value                 // await result
handle.cancel()                                // request cancellation
```
`Task.detached` is a review flag: it drops actor isolation, priority, and task-local values. Prefer `Task { }` unless you specifically need isolation-free execution.

**Cancellation is cooperative.** Nothing is force-stopped. Tasks must check:
- `try Task.checkCancellation()` — throws `CancellationError`.
- `Task.isCancelled` — poll a Bool.
- `withTaskCancellationHandler(operation:onCancel:)` — run cleanup when cancelled (e.g., cancel a network request). A common bug: long loops or `URLSession` wrappers that never observe cancellation.

### 1.3 Actors (Swift 5.5, SE-0306)

An `actor` is a reference type that protects its mutable state by serializing access through an implicit executor. Cross-actor access is `async` (must `await`); same-actor access is synchronous.

```swift
actor Counter {
    private var value = 0
    func increment() { value += 1 }     // isolated, synchronous internally
    func current() -> Int { value }
}

let c = Counter()
await c.increment()                     // cross-actor hop -> await
```

- **Actor isolation** is the compiler's model of "what state a given piece of code is allowed to touch synchronously." Members of an actor are *actor-isolated* by default.
- **`nonisolated`** members can't touch mutable isolated state but need no `await` (used for `Sendable`-only computed properties, protocol conformances like `Hashable`, `id`).
- **Actor reentrancy**: while an actor `await`s, it can process *other* messages. State can change across an `await` inside an isolated method — the classic reentrancy bug ("check-then-act" across a suspension). Reviewers should scrutinize invariants held across `await` within actor methods.
- **Custom executors** (SE-0392, Swift 5.9): an actor can specify a `SerialExecutor` (e.g., pin to a dispatch queue) via `nonisolated var unownedExecutor`.

### 1.4 `Sendable` and `@Sendable` (Swift 5.5, SE-0302)

`Sendable` is a marker protocol asserting a value is safe to cross isolation boundaries (no unsynchronized shared mutable state).

- **Implicitly `Sendable`:** value types whose members are all `Sendable`; actors; frozen enums with `Sendable` payloads; `@MainActor` (global-actor-isolated) types.
- **Never implicitly `Sendable`:** classes (unless `final` with only immutable `Sendable` stored properties, or `@MainActor`).
- **`@Sendable` closures:** closures that cross isolation boundaries must be `@Sendable` and may only capture `Sendable` values (by value).
- **`@unchecked Sendable`:** an escape hatch — you assert thread-safety the compiler can't verify (e.g., a class guarded by an internal lock). **Overuse is a top-tier review smell** (see §13). Every `@unchecked Sendable` should have a comment naming the synchronization mechanism.

```swift
struct Point: Sendable { var x, y: Double }          // implicit
final class Config: @unchecked Sendable {            // manual: guarded by lock
    private let lock = NSLock()
    private var _values: [String: String] = [:]
}
```

### 1.5 Global actors and `@MainActor` (Swift 5.5, SE-0316)

A **global actor** is a singleton actor you can attach to any declaration via an attribute. `@MainActor` is the built-in one, isolating code to the main thread/executor.

```swift
@MainActor final class ViewModel {   // whole type on the main actor
    var title = ""
}

@MainActor func updateUI() { ... }

func background() async {
    await MainActor.run { /* main-actor work */ }
}
```
- Define your own with `@globalActor`:
  ```swift
  @globalActor actor DatabaseActor { static let shared = DatabaseActor() }
  @DatabaseActor func query() { ... }
  ```
- A global-actor-isolated non-protocol type is implicitly `Sendable` (SE-0316).
- **`@MainActor` inference / usability** improved via SE-0434 (Swift 6.0): global-actor-isolated value types relax some `Sendable`/closure restrictions.

### 1.6 Region-based isolation and `sending` (Swift 6.0)

- **Region-based isolation (SE-0414):** the compiler tracks "isolation regions" of values that are provably not shared. A non-`Sendable` value can be passed across an isolation boundary if the compiler proves the sender no longer uses it ("transferring"). This dramatically reduces false positives.
- **`sending` (SE-0430):** an explicit parameter/result annotation meaning "ownership is transferred across the isolation boundary; the caller must give up the value." Enables passing non-`Sendable` values safely by proving they're not used afterward.
  ```swift
  func handoff(_ item: sending Item) async { await store.keep(item) }
  ```
- **`@isolated(any)` function types (SE-0431):** a function value that carries its own actor isolation, queryable at runtime — foundational for APIs like `Task` that must run a closure on its original actor.

### 1.7 Swift 6 strict concurrency / complete data-race checking

- **Language mode 6** makes all data-race-safety diagnostics **errors**. In language mode 5, they can be enabled incrementally as warnings via `-strict-concurrency=minimal | targeted | complete`.
- The compiler statically proves that mutable state is confined to a single isolation domain (an actor, a global actor, or a provably-unshared region). Violations that were runtime crashes/UB in GCD become **compile errors**.
- **Migration is incremental**: turn on `-strict-concurrency=complete` in language mode 5 first, fix warnings, then flip to language mode 6. Per-target in SwiftPM via `swiftSettings: [.enableExperimentalFeature(...)]` / `swiftLanguageMode(.v6)`.
- Enabling *specific* upcoming features early: e.g. `-enable-upcoming-feature StrictConcurrency`, `-enable-upcoming-feature InferSendableFromCaptures`.

### 1.8 Swift 6.2 "Approachable Concurrency" (the big 6.2 shift)

Swift 6.2's headline is making single-threaded code *not* fight the concurrency checker. Two opt-in "upcoming features" enabled by Xcode 26's new-project template:

- **Default actor isolation = `MainActor` (SE-0466):** compiler flag `-default-isolation MainActor` (SwiftPM: `defaultIsolation(MainActor)` / build setting `SWIFT_DEFAULT_ACTOR_ISOLATION = MainActor`). Every unannotated declaration in the module is inferred `@MainActor`. This removes the flood of false-positive data-race errors in ordinary UI/app code — you only opt *out* to background work. Best suited to app modules; library modules that must stay isolation-agnostic should generally **not** enable it.
- **`nonisolated(nonsending)` / run on caller's actor (SE-0461):** a `nonisolated async` function now runs **on the caller's actor** by default instead of hopping to the generic cooperative pool. This means `async` no longer implicitly means "concurrent." The old "always hop off" behavior is opted into explicitly with **`@concurrent`**:
  ```swift
  nonisolated func parse(_ d: Data) async -> Model { ... }   // runs on caller's actor (6.2)

  @concurrent func decodeImage(_ d: Data) async -> Image { ... } // deliberately off the actor
  ```
  Guidance: mark genuinely CPU-heavy work `@concurrent` *on purpose and visibly*; leave everything else to inherit the caller's context. `@concurrent` is only valid on `nonisolated` functions.
- Related 6.2 concurrency items: **isolated `deinit`** (SE-0371, matured), **`Observations`** async sequence for streaming observable state, **backpressure-friendly `AsyncStream`**, task naming for debugging, improved async stepping in LLDB.

**Net effect for reviewers:** In a 6.2 approachable-concurrency module, "make it compile" is often "add `@MainActor` at the boundary" or "mark the heavy function `@concurrent`," not "sprinkle `@unchecked Sendable`."

### 1.9 `AsyncSequence`, `AsyncStream`, continuations

- **`AsyncSequence` / `AsyncIteratorProtocol`** (SE-0298): the async analogue of `Sequence`, consumed with `for await`:
  ```swift
  for await line in fileHandle.bytes.lines { print(line) }
  for try await item in throwingStream { ... }   // throwing variant
  ```
  SE-0421 (Swift 6.0) generalized effect polymorphism so `AsyncSequence` composition (map/filter) propagates `throws`/isolation cleanly.
- **`AsyncStream` / `AsyncThrowingStream`** (SE-0314): bridge callback/delegate/imperative producers into an `AsyncSequence`:
  ```swift
  let stream = AsyncStream<Int> { continuation in
      producer.onValue = { continuation.yield($0) }
      producer.onDone  = { continuation.finish() }
      continuation.onTermination = { _ in producer.stop() }
  }
  ```
- **Continuations** (SE-0300) bridge completion-handler APIs to `async`:
  ```swift
  let data = try await withCheckedThrowingContinuation { cont in
      legacyFetch { result in cont.resume(with: result) }
  }
  ```
  Rules: resume **exactly once**. `withCheckedContinuation` traps on misuse (double/never resume); `withUnsafeContinuation` skips the check for performance. Missing/duplicate resume is a classic bug (hang or crash).

### 1.10 Common data-race pitfalls (what the compiler now catches)

- Capturing non-`Sendable` state in a `Task`/`@Sendable` closure.
- Passing a mutable class instance across actors without `Sendable`.
- Mutating captured `var` from concurrent tasks.
- Reentrancy: assuming actor state is unchanged across an internal `await`.
- Global mutable `var` (now must be `let`, isolated to a global actor, or `nonisolated(unsafe)` — the latter is a review flag).
- `DispatchQueue`-based "thread confinement" the compiler can't see → forces `@unchecked Sendable`; prefer migrating to an actor.

---

## 2. Value semantics and types

### 2.1 Structs vs. classes vs. enums

| | `struct` | `class` | `enum` |
|---|---|---|---|
| Semantics | value (copied) | reference (shared) | value (copied) |
| Mutation | needs `mutating` on methods | in place | needs `mutating` |
| Inheritance | no | yes | no |
| Identity (`===`) | no | yes | no |
| Deinit | no | yes (`deinit`) | no |
| Default `Sendable` | if members are | no | if payload is |

**Idiomatic Swift prefers value types** (structs/enums) by default; reach for a class when you need identity, inheritance, deinit, or reference sharing (e.g., a shared mutable resource, Objective-C interop). "Reference type where a value type fits" is a common smell (§13).

### 2.2 Copy-on-write (COW)

Standard-library value types (`Array`, `Dictionary`, `Set`, `String`, `Data`) wrap a reference-typed buffer and copy it lazily only on mutation when `isKnownUniquelyReferenced` is false. So value semantics are preserved without eager deep copies. Custom COW types use `isKnownUniquelyReferenced(&storage)` to implement the same pattern.

### 2.3 `mutating` and `inout`

- `mutating func` — a struct/enum method that reassigns `self` or its stored properties.
- `inout` parameters — pass-by-value-result (copy in, mutate, copy back at return), *not* pass-by-reference; passed with `&`. Not usable with `async` reentrancy or escaping closures.

### 2.4 Noncopyable types `~Copyable` and ownership (Swift 5.9+, matured through 6.x)

- **`~Copyable` (SE-0390, Swift 5.9):** a struct/enum whose instances have **unique ownership** and cannot be implicitly copied — ideal for resources (file handles, locks, buffers) where duplication is a bug.
  ```swift
  struct FileDescriptor: ~Copyable {
      let fd: Int32
      consuming func close() { Darwin.close(fd) }   // consumes self; no further use
      deinit { Darwin.close(fd) }
  }
  ```
- **Parameter ownership modifiers (SE-0377, Swift 5.9):** `borrowing` (temporary read access, value stays valid for caller) and `consuming` (takes ownership, caller can't use it afterward). Mutually exclusive with each other and `inout`.
- **`consume` operator (SE-0366):** `let y = consume x` ends `x`'s lifetime explicitly.
- **Noncopyable generics (SE-0427, Swift 6.0):** generics over possibly-noncopyable types via the `~Copyable` constraint; `<T: ~Copyable>` means "T might not be copyable." The stdlib gained `Optional`, `Result`, `UnsafePointer` etc. over noncopyable (SE-0437).
- **`borrowing`/`consuming` switch (SE-0432, Swift 6.0)** and **partial consumption (SE-0429)** refine pattern matching on noncopyable values.

These are systems-programming / performance features — most application code never needs them, but a reviewer should recognize them and check that `consuming`/`deinit` semantics for resources are correct.

### 2.5 Tuples

Lightweight, structural, value-type aggregates: `let pair = (1, "a")`, `pair.0`, named `(x: 1, y: 2)`. Tuples up to some arity are `Equatable`/`Comparable`/`Sendable` when elements are (SE-0283). Use structs once a tuple gains meaning or is passed around widely.

---

## 3. Error handling

### 3.1 `throws` / `try` / `do`-`catch`

```swift
enum NetworkError: Error { case offline, timeout }

func load() throws -> Data { ... }

do {
    let d = try load()
} catch NetworkError.offline {
    ...
} catch {                       // binds `error`
    log(error)
}
```
- `try` marks a throwing call; `try?` converts to `Optional` (nil on error); `try!` asserts no error (traps otherwise — a review flag, §13).
- Errors are just values conforming to the empty `Error` protocol.

### 3.2 `rethrows`

A function that throws only if a closure argument throws:
```swift
func map<T>(_ transform: (Element) throws -> T) rethrows -> [T]
```

### 3.3 Typed throws (Swift 6.0, SE-0413)

Declare the concrete error type a function throws:
```swift
func parse() throws(ParseError) -> AST { ... }

do {
    let ast = try parse()
} catch {                       // `error` is statically ParseError, not `any Error`
    switch error { ... }        // exhaustive
}
```
- `throws` == `throws(any Error)`; a non-throwing function == `throws(Never)`. This unifies all three under one model and enables generic code parameterized over the failure type.
- **Guidance:** typed throws is valuable for (a) exhaustive local error handling, (b) embedded/constrained contexts, and (c) generic error-propagating algorithms. For public library APIs, untyped `throws` is often still preferred because a typed error is a rigid part of your ABI/API contract. Don't reach for it reflexively.

### 3.4 `Result<Success, Failure>`

A value-based alternative to `throws`, useful for storing/deferring errors, completion handlers, and `async` bridging. Convert with `Result { try f() }` and `try result.get()`. In modern `async` code, prefer `throws`; `Result` shines when you must *store* an outcome.

### 3.5 `defer`

Runs a block on scope exit (in reverse order of declaration), regardless of how you leave (return/throw/break). Use for cleanup (unlock, close, restore state):
```swift
lock.lock(); defer { lock.unlock() }
```

### 3.6 Errors vs. optionals vs. `precondition`/`fatalError`

- **Optional (`nil`)** — expected absence with one obvious failure mode ("not found"); no explanation needed.
- **`throws`** — recoverable failure where the *caller* decides how to handle it and *why it failed matters*.
- **`precondition` / `assert`** — programmer-error contract checks. `assert` compiles out in release; `precondition` stays in release. Trap on violation.
- **`fatalError` / `preconditionFailure`** — unrecoverable programmer error / unreachable code. Returns `Never`. **`fatalError` on a reachable production path is a serious smell** (§13) — it's for genuinely impossible states, not for "I didn't handle this yet."

---

## 4. Optionals and safety

- **`Optional<Wrapped>`** (`Wrapped?`) models "value or nothing." It's an enum (`.some`/`.none`), not a null pointer.
- **Optional binding:**
  ```swift
  if let user { use(user) }               // shorthand (Swift 5.7, SE-0345): binds same-named
  guard let user else { return }           // early exit; `user` in scope afterward
  if let user = maybeUser { ... }          // classic form
  ```
- **Optional chaining:** `user?.profile?.name` short-circuits to `nil`.
- **Nil-coalescing:** `let name = user?.name ?? "Guest"`.
- **`switch` over optionals**, `map`/`flatMap` on `Optional`, and `Optional.some`/`.none` patterns.
- **Force unwrap `!` and `try!`:** crash if `nil`/error. Acceptable only where a `nil` is a genuine programmer error you *want* to trap (e.g., a hardcoded resource URL, `@IBOutlet`). High density of `!`/`try!` is the single most common Swift review flag. Prefer `guard let`, `??`, or throwing.
- **Implicitly unwrapped optionals (`T!`)** — legacy from Obj-C bridging; avoid in new API surface.
- **`Never`** — the uninhabited type; return type of functions that never return (`fatalError`), and the "no error" case for typed throws (`throws(Never)`). Conforms to `Error`, so it can be a generic error placeholder.

---

## 5. Generics and protocols

### 5.1 Protocol-oriented programming

Swift favors composing behavior from small protocols + protocol extensions (default implementations) over class inheritance. Value types conform to protocols; retroactive conformance (below) extends types you don't own.

### 5.2 Associated types and primary associated types

```swift
protocol Container {
    associatedtype Element
    var count: Int { get }
    subscript(_ i: Int) -> Element { get }
}
```
- **Primary associated types (SE-0346, Swift 5.7):** expose associated types as angle-bracket parameters for lightweight same-type constraints:
  ```swift
  protocol Collection<Element> { associatedtype Element ... }
  func sum(_ xs: some Collection<Int>) -> Int
  let items: any Collection<String>
  ```

### 5.3 Opaque types `some` vs. existentials `any`

- **`some P` (opaque, SE-0244 return / SE-0341 parameter, Swift 5.1 / 5.7):** one *specific, fixed but hidden* concrete type known to the compiler. Preserves type identity, enables static dispatch and associated-type inference, no boxing. `func makeShape() -> some Shape`.
- **`any P` (existential, SE-0335, Swift 5.6/5.7):** a *box* that can hold *any* conforming type, which can vary at runtime. Requires the explicit `any` spelling. Has dynamic dispatch + heap boxing cost. `var shapes: [any Shape]`.
- **Rule of thumb:** default to `some` (generics-lite, zero-cost) when the type is fixed at the call site; use `any` only when you genuinely need heterogeneity / to store mixed types. Bare protocol names as types are discouraged — write `any P` explicitly (an upcoming feature makes bare existentials an error: `ExistentialAny`).
- **Constrained existentials (SE-0353)** and **implicit opening of existentials (SE-0352, Swift 5.7)** let you call generic methods on `any P` values.

### 5.4 Generic constraints and `where`

```swift
func merge<C: Collection>(_ a: C, _ b: C) -> [C.Element]
    where C.Element: Comparable { ... }

extension Array where Element: Numeric { func total() -> Element { reduce(0, +) } }
```

### 5.5 Parameter packs / variadic generics (Swift 5.9, SE-0393; types SE-0398)

Abstract over an *arbitrary number of heterogeneous types*:
```swift
func zipAll<each T>(_ item: repeat each T) -> (repeat each T) {
    (repeat each item)
}
struct Tuple<each Element> { var elements: (repeat each Element) }   // SE-0398
```
`each T` is a type pack; `repeat` expands it. This is how variadic-arity generic APIs (e.g., SwiftUI's `TupleView`, `Regex` captures) are built without N hand-written overloads.

### 5.6 Conditional and retroactive conformance

- **Conditional conformance (SE-0143):** `extension Array: Equatable where Element: Equatable`.
- **Retroactive conformance:** conforming a type you don't own to a protocol you don't own. Allowed but risky (two modules could both do it). Swift 6 asks you to spell it `extension OtherType: @retroactive Proto` (SE-0364) to acknowledge the hazard.

---

## 6. Macros (Swift 5.9)

Compile-time source-to-source transforms, type-checked both before and after expansion, implemented as separate compiler-plugin executables built on **`swift-syntax`** (the `SwiftSyntaxMacros` module). Two families:

### 6.1 Freestanding macros (`#name`)
- **Expression macros (SE-0382):** `#foo(...)` produces an expression. Examples: `#warning`, `#url`, `#expect` (Swift Testing), the classic `#stringify`.
- **Freestanding declaration macros (SE-0397):** produce declarations, e.g. `#Preview { ... }`.

### 6.2 Attached macros (`@Name`, SE-0389)
Attach to a declaration and augment it via roles:
- `@attached(peer)` — add sibling declarations (e.g. a completion-handler twin of an async func).
- `@attached(accessor)` — add get/set (property-wrapper-like storage).
- `@attached(memberAttribute)` / `@attached(member)` — add members / annotate members.
- `@attached(extension)` (formerly conformance) — add protocol conformances + members.
- Real examples: **`@Observable`** (Observation framework — synthesizes change tracking), `@Model` (SwiftData), `@CodingKeys`-style helpers.

### 6.3 When to write one
Only when you have **repetitive boilerplate that can't be expressed with generics, protocol extensions, or property wrappers**, and the transform is mechanical. Macros are hard to debug, add a `swift-syntax` build dependency (compile-time cost), and complicate readability. For a reviewer: a macro should replace *real* duplicated code, come with tests (macros are unit-testable via `assertMacroExpansion`), and not hide surprising control flow.

---

## 7. Memory management (ARC)

- **ARC** (Automatic Reference Counting) manages **class** (and closure/actor) lifetimes deterministically via retain/release inserted at compile time — not a tracing GC. Value types are not reference-counted (though their COW buffers are).
- **Retain cycles:** two objects (or an object and a closure) strongly referencing each other never deallocate. The two tools:
  - **`weak`** — optional, auto-nils when the referent deallocates. Use when the referent can legitimately outlive/predecease you (delegates, parent↔child back-references).
  - **`unowned`** — non-optional, assumes the referent outlives self; **crashes (or UB) on access after dealloc**. Use only when the lifetime relationship is guaranteed.
- **Capture lists** break closure cycles:
  ```swift
  loader.onDone = { [weak self] in self?.finish() }
  Task { [weak self] in await self?.refresh() }
  ```
  In escaping/stored closures that reference `self`, `[weak self]` is the default idiom; forgetting it is the classic iOS leak. (In *structured* `async` code that doesn't outlive `self`, a capture may be fine — not every closure needs `[weak self]`.)
- **Value types avoid cycles entirely** — another reason to prefer structs/enums. A graph of value types cannot leak via reference cycles.
- `deinit` runs at deallocation (classes/actors only); use for releasing non-ARC resources.

---

## 8. Expressive features

- **Property wrappers (SE-0258, Swift 5.1):** `@propertyWrapper` types factor out accessor patterns (`wrappedValue`, optional `projectedValue` exposed as `$name`). Language-level (`@State`, `@Published` are framework uses). Write one when several properties share get/set logic (clamping, thread-safety, persistence).
- **Result builders (`@resultBuilder`, SE-0289, Swift 5.4):** transform a braced sequence of expressions into one value via `buildBlock`/`buildOptional`/`buildEither`/`buildArray`/`buildExpression`. The mechanism behind SwiftUI's `ViewBuilder`, `RegexBuilder`, and custom DSLs. A reviewer should recognize a result-builder closure isn't ordinary imperative code.
- **Key paths (`\Type.property`):** first-class, composable references to properties/subscripts. `\User.name`, used in `sort(by:)`, `map(\.id)`, `@dynamicMemberLookup`, Combine/SwiftUI bindings. Writable key paths, reference key paths.
- **`@dynamicMemberLookup` (SE-0195) / `@dynamicCallable` (SE-0216):** allow `x.anything` / `x(...)` to route through a subscript/method — for interop bridges and ergonomic wrappers. Use sparingly; they defeat autocomplete and type-checking of member names.
- **Pattern matching / `switch`:** value binding, `where` guards, tuple patterns, `case let`, optional patterns, range patterns, enum-with-payload matching. **Exhaustiveness** is enforced for enums (no `default` needed if all cases covered) — a key safety property; a `default` on a closed enum can hide the "new case not handled" review signal. `if case`/`guard case` for single-pattern matches. `for case let x? in optionals` filters nils.
- **Extensions:** add methods/computed properties/conformances/nested types to any type (including generics conditionally). Cannot add stored properties. Idiomatic organizing tool (one extension per protocol conformance).

---

## 9. Swift Package Manager (SwiftPM)

The manifest is **`Package.swift`**, itself Swift code evaluated in a sandbox; the first line pins the manifest API/tools version:

```swift
// swift-tools-version: 6.0
import PackageDescription

let package = Package(
    name: "MyLib",
    platforms: [.macOS(.v14), .iOS(.v17)],
    products: [
        .library(name: "MyLib", targets: ["MyLib"]),
        .executable(name: "mytool", targets: ["mytool"]),
    ],
    dependencies: [
        .package(url: "https://github.com/apple/swift-argument-parser", from: "1.3.0"),
        .package(path: "../LocalUtils"),        // local package for modularization
    ],
    targets: [
        .target(
            name: "MyLib",
            dependencies: [.product(name: "ArgumentParser", package: "swift-argument-parser")],
            resources: [.process("Resources"), .copy("data.json")],
            swiftSettings: [.swiftLanguageMode(.v6), .defaultIsolation(MainActor)]
        ),
        .testTarget(name: "MyLibTests", dependencies: ["MyLib"]),
        .plugin(name: "MyPlugin", capability: .buildTool()),
    ]
)
```

- **Concepts:** *targets* (build units — `.target`, `.executableTarget`, `.testTarget`, `.macro`, `.plugin`, `.systemLibrary`, `.binaryTarget`), *products* (`.library`, `.executable`, `.plugin` — what dependents import), *dependencies* (git URL + version range, or `path:` for local).
- **Versioning:** semantic-version requirements — `from:`, `.upToNextMajor(from:)`, `.upToNextMinor(from:)`, `exact:`, `branch:`, `revision:`. Resolution is recorded in `Package.resolved`.
- **Resources (SE-0271):** `.process` (platform-optimized) vs `.copy` (verbatim); access via `Bundle.module`.
- **Plugins (SE-0303/SE-0325, Swift 5.6/5.7):** *build-tool plugins* (code generation in the build graph) and *command plugins* (`swift package <verb>` — linting, formatting, docs).
- **Per-target settings:** `swiftSettings`/`cSettings`/`cxxSettings`/`linkerSettings`, including `.enableUpcomingFeature`, `.enableExperimentalFeature`, `.unsafeFlags`, `.interoperabilityMode(.Cxx)`.
- **Local packages** are the idiomatic way to modularize an app: split features into path-referenced packages for build isolation, faster incremental builds, and enforced dependency boundaries.

---

## 10. API Design Guidelines (swift.org, authoritative)

The guidelines are the canonical standard a Swift reviewer cites. Core principles:

**Fundamentals**
- **Clarity at the point of use** is the most important goal — APIs are declared once but *used* many times. Optimize the call site.
- **Clarity is more important than brevity.** Don't abbreviate to save characters.
- **Write a doc comment for every declaration.** If it's hard to describe simply, reconsider the API.

**Promote clear usage**
- Include words that avoid ambiguity: `remove(at: index)` not `remove(index)`.
- Omit needless words — especially those merely repeating type info: `remove(_:)` not `removeElement(_:)`.
- Name variables/parameters/associated types by **role**, not type (`supplier`, not `widgetFactory`).
- Compensate for weak type info (e.g., `Any`, `NSObject`) with a noun describing the role.

**Strive for fluent usage**
- Method/function names should read as grammatical English phrases at the call site: `x.insert(y, at: z)`, `x.subViews(havingColor: y)`.
- Begin factory methods with `make`: `x.makeIterator()`.
- **Side-effect naming:** mutating verbs get imperative names (`x.sort()`, `x.append(y)`); their nonmutating counterparts read as nouns/`-ed`/`-ing` (`z = x.sorted()`, `y.union(z)`). Noun-based mutating pairs use `form`: `y.formUnion(z)`.
- Boolean methods/properties read as assertions about the receiver: `x.isEmpty`, `line1.intersects(line2)`.
- Protocols describing *what something is* are nouns (`Collection`); those describing a *capability* use `-able`/`-ible` (`Equatable`, `ProgressReporting`).

**Conventions**
- `UpperCamelCase` for types/protocols; `lowerCamelCase` for everything else. Acronyms are uniformly cased (`utf8`, not `uTF8`; `ASCII` all caps when leading a type).
- **Argument labels:** omit when arguments can't be usefully distinguished (`min(x, y)`); omit the first label in full-width value-preserving conversions (`Int64(someUInt32)`); use labels that form a grammatical phrase with the base name; prefer prepositional phrases (`moveTo(x:y:)` → `move(to:)`). Default parameters simplify long signatures.
- Avoid overloading solely on return type. Prefer methods/properties over free functions. Take advantage of defaulted parameters.

**Documentation comments**
- Begin with a single summary sentence in the imperative for methods ("Returns…", "Inserts…"), fragment for properties. Use Swift-flavored Markdown, `- Parameter`/`- Parameters`, `- Returns`, `- Throws`, and callouts (`- Note:`, `- Warning:`, `- Precondition:`).

---

## 11. Testing (language-level): Swift Testing vs. XCTest

**Swift Testing** (shipped with Swift 6 / Xcode 16, WWDC 2024; enhanced in 6.2) is the modern, macro-driven, open-source framework. It coexists with and is gradually replacing **XCTest**.

```swift
import Testing

@Test func addsCorrectly() {
    #expect(add(2, 3) == 5)                       // soft check: records, continues
}

@Test("Parses ISO date", .tags(.parsing))
func parsing() throws {
    let d = try #require(parseDate("2025-09-15")) // hard check: unwraps or fails+stops
    #expect(d.year == 2025)
}

@Suite("Math", .serialized)
struct MathTests {
    @Test(arguments: [0, 1, 2, 3])                // parameterized: one child test per arg
    func isEvenDoubled(_ n: Int) {
        #expect((n * 2) % 2 == 0)
    }

    @Test(arguments: zip([1,2], [2,4]))           // multi-arg via zip
    func doubles(_ input: Int, _ expected: Int) {
        #expect(input * 2 == expected)
    }
}
```

- **Macros:** `@Test` (any function, sync or `async`, `throws`; no `test` prefix needed), `@Suite` (a grouping type), `#expect` (records failure, keeps going, captures sub-expression values on failure), `#require` (throws `ExpectationFailedError` and stops the test — for preconditions and unwrapping optionals).
- **Traits:** `.tags(...)`, `.enabled(if:)`, `.disabled("reason")`, `.bug(url)`, `.timeLimit(...)`, `.serialized` (opt out of parallelism). Traits replace XCTest's naming conventions / overrides.
- **Parameterized tests** (`@Test(arguments:)`) produce one parent + one child per input, run in parallel — far better than a `for` loop inside one test (isolated failures, individual re-runs).
- **Parallel by default** (in-process, across tests) — tests must be independent; shared mutable global state becomes a real hazard. Swift Testing integrates with Swift concurrency (`async` tests, actor isolation) natively.
- **Error checking:** `#expect(throws: MyError.self) { try f() }` / `#expect(throws: MyError.timeout)`.
- **What stays in XCTest:** UI automation (`XCUIApplication`/XCUITest) and performance measurement (`XCTMetric`/`measure`). New unit tests should generally use Swift Testing; the two frameworks run side by side in the same target for incremental migration.

---

## 12. Interoperability

### 12.1 Objective-C
- **Automatic bridging** both directions within a module/framework; Foundation value bridging (`String`↔`NSString`, `Array`↔`NSArray`, etc.).
- **`@objc`** exposes a Swift declaration to the Obj-C runtime; **`@objc(customName)`** renames; **`@objcMembers`** exposes a whole class. Required for selector-based APIs (`#selector`), KVO/KVC, dynamic dispatch (`dynamic`).
- **`@_cdecl`**, `NS_SWIFT_NAME`, nullability audit macros (`NS_ASSUME_NONNULL_BEGIN`) shape how Obj-C imports into Swift. Swift `Error`↔`NSError` bridging via `NSError` domain/code.
- Bridging header exposes Obj-C to Swift in a mixed app target.

### 12.2 C
- Import C libraries directly via a **module map** / `.systemLibrary` target or a bridging header. C types map to Swift (`Int32`, `UnsafePointer<T>`, `OpaquePointer`, function pointers via `@convention(c)` closures). `withUnsafePointer`, `withUnsafeBytes` for buffer access. `CInt`, `CChar`, etc. typealiases.

### 12.3 C++ interop (Swift 5.9+, bidirectional)
- **Opt-in** per target: `swiftSettings: [.interoperabilityMode(.Cxx)]` in SwiftPM (or `-cxx-interoperability-mode=default`). Off by default because it changes name lookup.
- **Swift→C++:** call C++ functions, use C++ types, methods, templates, `std::string`/`std::vector` (mapped to Swift with iteration support), owned/reference-semantics annotations (`SWIFT_SHARED_REFERENCE`, `SWIFT_IMMORTAL_REFERENCE`).
- **C++→Swift:** the compiler generates a C++ header exposing Swift APIs to C++ callers.
- Maturity is documented at swift.org/documentation/cxx-interop/status (some C++ features — exceptions, certain templates, virtual inheritance — are unsupported or constrained). C++ `move`-only types map toward Swift `~Copyable`.
- Reviewer note: enabling C++ interop is a build-wide decision with compile-time and API-surface implications; scope it to the targets that need it.

---

## 13. Idioms, anti-patterns, and language "debt"

**Idiomatic Swift a reviewer should reward**
- Value types by default; classes only for identity/inheritance/shared mutable state.
- `guard let`/`guard` for early exits and flat control flow; minimal nesting.
- Protocol + protocol-extension composition over class hierarchies.
- `some` over `any` unless heterogeneity is required; explicit `any`.
- Exhaustive `switch` on closed enums (no defensive `default`).
- Errors typed by domain; `throws` for recoverable, optionals for simple absence.
- Small, focused functions and extensions grouped by conformance.
- Clear API naming per the official guidelines (fluent call sites, right argument labels).
- Concurrency isolation modeled with actors / `@MainActor`, not manual queues.

**Anti-patterns / smells to flag**
- **Force-unwrap `!` and `try!` density** — each is a potential crash; flag clusters and any on non-invariant paths. Prefer `guard let`/`??`/`throws`.
- **`fatalError`/`preconditionFailure` on reachable production paths** — fine for truly-impossible states and `required init?(coder:)`-style stubs, not for unhandled cases or "TODO."
- **Massive functions / massive types** — long methods, "god" view models/managers; extract and use extensions.
- **`@unchecked Sendable` overuse** — every one asserts a safety property the compiler can't check; demand a comment naming the lock/queue and prefer migrating to an actor.
- **Silencing concurrency diagnostics** — `nonisolated(unsafe)`, `@preconcurrency` imports left permanently, `-strict-concurrency` downgraded, `@Sendable` closures wrapping unsynchronized state, `Task { @MainActor in ... }` sprinkled to paper over isolation instead of modeling it. In Swift 6.2, prefer default `MainActor` isolation + explicit `@concurrent` over ad-hoc suppression.
- **Reference types where value types fit** — a `class` with only value data and no identity/sharing need; forces manual `Sendable`/cycle management.
- **Stringly-typed code** — magic strings for keys/identifiers/states; prefer enums, `RawRepresentable`, key paths, and typed IDs.
- **`Task.detached` by default** — silently drops isolation/priority/task-locals; usually should be `Task { }`.
- **Retain cycles** — stored/escaping closures capturing `self` strongly without `[weak self]`; delegate references not `weak`.
- **Ignoring cancellation** — long-running tasks that never check `Task.isCancelled` / `checkCancellation()`.
- **Bare existentials & implicit Obj-C dynamism** — un-`any`'d protocol types; unnecessary `@objc dynamic`.
- **Blocking the main actor** — synchronous heavy work or `DispatchSemaphore.wait()` on `@MainActor`; move to `@concurrent`/an actor.

**Swift 6 / concurrency migration guidance**
1. Build with the 6.x compiler in **language mode 5** first — no behavior change, but you can adopt features incrementally.
2. Turn on `-strict-concurrency=complete` (warnings) and adopt upcoming features per-target (`InferSendableFromCaptures`, `RegionBasedIsolation`, etc.).
3. Fix warnings by *modeling* isolation: put UI/state on `@MainActor`, wrap shared mutable state in `actor`s, add `Sendable` conformances, use `sending` for handoffs — rather than reaching for `@unchecked`/`nonisolated(unsafe)`.
4. Flip to **language mode 6** target by target once warnings are clean.
5. On Swift 6.2, consider **approachable concurrency** (`defaultIsolation(MainActor)` + `@concurrent` for heavy work) for app modules to cut boilerplate; keep isolation-agnostic libraries explicit.
6. Use `@preconcurrency import` as a *temporary* bridge for not-yet-annotated dependencies, and Xcode/Swift migration tooling to apply mechanical edits.

---

## Sources

### Official (swift.org / Apple)
- Swift 6.2 released — https://www.swift.org/blog/swift-6.2-released/
- Announcing Swift 6 — https://www.swift.org/blog/announcing-swift-6/
- Swift 6 concurrency migration guide — https://www.swift.org/migration/documentation/migrationguide/
- Swift concurrency documentation — https://www.swift.org/documentation/concurrency/
- API Design Guidelines — https://www.swift.org/documentation/api-design-guidelines/
- Mixing Swift and C++ — https://www.swift.org/documentation/cxx-interop/ ; status — https://www.swift.org/documentation/cxx-interop/status/
- What's New in Swift (Apple Developer) — https://developer.apple.com/swift/whats-new/
- The Swift Programming Language (book) — https://docs.swift.org/swift-book/
- Swift Evolution proposals (github.com/swiftlang/swift-evolution/proposals): SE-0296 async/await, SE-0298 AsyncSequence, SE-0300 continuations, SE-0302 Sendable, SE-0304 structured concurrency, SE-0306 actors, SE-0314 AsyncStream, SE-0316 global actors, SE-0317 async let, SE-0335 existential any, SE-0341 opaque parameters, SE-0346 primary associated types, SE-0352 implicit open existentials, SE-0353 constrained existentials, SE-0364 retroactive conformance, SE-0366 consume operator, SE-0377 ownership modifiers, SE-0381 discarding task groups, SE-0382 expression macros, SE-0389 attached macros, SE-0390 noncopyable structs/enums, SE-0392 custom executors, SE-0393 parameter packs, SE-0397 freestanding declaration macros, SE-0398 variadic types, SE-0411 isolated default values, SE-0413 typed throws, SE-0414 region-based isolation, SE-0420 actor isolation inheritance, SE-0421 AsyncSequence effect polymorphism, SE-0427 noncopyable generics, SE-0429 partial consumption, SE-0430 `sending`, SE-0431 `@isolated(any)`, SE-0432 noncopyable switch, SE-0434 global-actor-isolated type usability, SE-0437 noncopyable stdlib primitives, SE-0461 nonisolated async on caller's actor + `@concurrent`, SE-0466 default actor isolation.
- Swift Testing (github.com/swiftlang/swift-testing) and Apple developer docs.

### Community (secondary — corroboration / examples)
- Matt Massicotte's concurrency series — https://www.massicotte.org/ (SE-0430, SE-0420, SE-0411, SE-0434, concurrency glossary)
- Donny Wals, "Exploring concurrency changes in Swift 6.2" — https://www.donnywals.com/exploring-concurrency-changes-in-swift-6-2/
- Antoine van der Lee (SwiftLee): approachable concurrency, existential any, parameter packs — https://www.avanderlee.com/
- Hacking with Swift — What's new in Swift 5.9 / 6.0 / 6.2, macros, variadic generics — https://www.hackingwithswift.com/
- QuickBird Studios, "Swift Macros" — https://quickbirdstudios.com/blog/swift-macros/
- Michael Tsai, "Swift 6.2: Approachable Concurrency" — https://mjtsai.com/blog/2025/11/03/swift-6-2-approachable-concurrency/

*Version-sensitive items are labeled inline. Where a secondary source is cited for a version/SE fact, it was cross-checked against the official swift.org release blog or the swift-evolution proposal.*
