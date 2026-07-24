# Kotlin Language Reference — for `language-kotlin-expert`

> Scope: **the Kotlin language + coroutines/stdlib**, Kotlin 2.x (2025–2026). NOT Android
> framework (Jetpack/Compose/Room/lifecycle are other agents' territory). Everything here
> is JVM-first but calls out Multiplatform/Native where the language semantics differ.
>
> Version conventions used below: **Stable** = no opt-in; **Beta/Preview/Experimental** =
> needs a `-X…` compiler flag or `@OptIn`; version numbers indicate *first availability*.
> Kotlin follows an incremental release train: **2.0 (May 2024), 2.1 (Nov 2024), 2.2 (mid-2025)**.

---

## 0. Kotlin 2.x snapshot (read this first — most version-sensitive section)

### K2 compiler
- **K2 is Stable and the default since Kotlin 2.0** for *all* backends: JVM, Native, Wasm, JS.
  This is the headline of 2.0 — a full front-end rewrite, unified across platforms, enabling
  faster language-feature delivery. Validated on ~10M LOC / 80k projects before release.
- **Smart-cast improvements** shipped with K2: smart casts now survive across local `val`
  captured booleans (`val isCat = animal is Cat; if (isCat) animal.purr()`), through `||`
  (smart-cast to common supertype), inside `inline` function lambdas (via implicit
  `callsInPlace` contract), for function-typed properties, and in `catch`/`finally`.
- JVM: lambdas now compile via `invokedynamic` by default (smaller bytecode). Opt out with
  `-Xlambdas=class` or `@JvmSerializableLambda` for a serializable lambda.

### Feature availability matrix (a reviewer's cheat-sheet)

| Feature | First appeared | Status now (≥2.2) | Opt-in flag |
|---|---|---|---|
| **Guard conditions in `when`** (`is X if cond ->`) | 2.1 (preview) | **Stable in 2.2** | none in 2.2 (`-Xwhen-guards` in 2.1) |
| **Non-local `break`/`continue`** in inline lambdas | 2.1 (preview) | **Stable in 2.2** | none in 2.2 (`-Xnon-local-break-continue` in 2.1) |
| **Multi-dollar interpolation** (`$$"""…"""`) | 2.1 (preview) | **Stable in 2.2** | none in 2.2 (`-Xmulti-dollar-interpolation` in 2.1) |
| **Context parameters** (`context(x: T)`) | 2.2 (preview) | **Preview** — replaces the older *context receivers* | `-Xcontext-parameters` |
| **Context-sensitive resolution** (drop enum/sealed qualifier in `when`) | 2.2 (preview) | **Preview** | `-Xcontext-sensitive-resolution` |
| **Nested type aliases** (`typealias` inside a class) | 2.2 (Beta) | **Beta** | `-Xnested-type-aliases` |
| **`@all:` annotation use-site meta-target** | 2.2 (preview) | **Preview** | `-Xannotation-target-all` |
| **`@JvmExposeBoxed`** (expose value-class boxed form to Java) | 2.2 | **Experimental** | annotation |
| **Sealed `when` exhaustiveness without `else`** | 2.1 | **Stable** | none |
| **`@SubclassOptInRequired`** | 2.1 | **Stable** | none |
| **Value classes `@JvmInline`** | 1.5 | **Stable** | none |
| **Sealed interfaces** | 1.5 | **Stable** | none |
| **`expect`/`actual` (KMP)** | — | **Stable** in 2.x | none |

**Guard conditions** — extra `if` clause on a `when` branch that already has a subject:
```kotlin
when (animal) {
    is Animal.Dog            -> feedDog()
    is Animal.Cat if !animal.mouseHunter -> feedCat()  // guard
    else                     -> println("unknown")
}
```

**Non-local `break`/`continue`** — `break`/`continue` now work inside a lambda passed to an
`inline` function, targeting the enclosing loop:
```kotlin
for (element in elements) {
    val v = element.nullableMethod() ?: run { log.warn("skip"); continue }  // now legal
    if (v == 0) return true
}
```

**Context parameters** (2.2 preview — KEEP-259; **supersedes context receivers**, which are
being removed). Declare implicit dependencies resolved from the call-site context:
```kotlin
context(users: UserService)          // named context parameter
fun outputMessage(message: String) { users.log("Log: $message") }

context(_: UserService)              // `_` = needed for resolution, not referenced by name
fun logWelcome() = outputMessage("Welcome!")
```
> Reviewer note: context receivers (`context(UserService)` without a name) are **deprecated** —
> if you see them, flag migration to context parameters. Both are still non-Stable; don't
> require them in production code without an explicit opt-in decision.

**Explicit backing fields** (`field` keyword for a separate backing-field type, e.g. a
`private val` `MutableStateFlow` exposed as a public `StateFlow`) remains an experimental
KEEP proposal — verify status against the target Kotlin version before relying on it. The
common idiom today is still the two-property pattern (`_state`/`state`).

**Multi-dollar interpolation** — choose how many `$` trigger interpolation, so literal `$`
(e.g. JSON schema keys, shell templates) needn't be escaped:
```kotlin
val schema = $$"""{ "$schema": "…", "title": "$${name}" }"""  // single $ literal, $$ interpolates
```

---

## 1. Null safety

Kotlin encodes nullability in the type system; NPEs become compile-time errors.

- **Non-null `T` vs nullable `T?`.** `var a: String = "x"; a = null` → compile error.
  `var b: String? = null` is fine.
- **Safe call `?.`** — returns `null` instead of throwing: `a?.length`. Chains short-circuit:
  `bob?.department?.head?.name`.
- **Elvis `?:`** — fallback / early exit: `val l = b?.length ?: 0`. Idiomatically pairs with
  `throw`/`return`: `val name = node.name ?: throw IllegalArgumentException("name expected")`.
- **Not-null assertion `!!`** — `b!!.length` throws `NullPointerException` if null. **Treat
  every `!!` as a code smell**: it's an explicit "trust me" that defeats the type system.
  Prefer `?.`, `?:`, `requireNotNull(x)`, or restructuring so the type is non-null.
- **Safe cast `as?`** — returns `null` on failure instead of `ClassCastException`:
  `val n: Int? = x as? Int`.
- **Smart casts** — after `if (x != null)` or `x is Foo`, `x` is used as the narrowed type
  (K2 widened where this holds; see §0). Smart casts do **not** apply to `var` properties that
  could change between check and use, or to properties with custom getters — hence local-`val`
  capture or `?.let`.
- **`filterNotNull()`** collapses `List<T?>` → `List<T>`.
- **Platform types** (`T!`) — values coming from Java without nullability info. The compiler
  relaxes null checks on them, so an NPE can surface at the boundary. Mitigate by honoring
  JSpecify / `@Nullable` / `@NotNull` annotations (K2 enforces JSpecify strictly by default
  as of 2.1) and by immediately assigning to a declared `T` or `T?`.

### Scope functions (`let` / `run` / `also` / `apply` / `with`)
| Function | Receiver in block | Returns | Typical use |
|---|---|---|---|
| `let`   | `it`   | lambda result | null-guarded transform: `x?.let { … }` |
| `run`   | `this` | lambda result | compute a value using the receiver's members |
| `also`  | `it`   | the receiver   | side effects (logging, validation) in a chain |
| `apply` | `this` | the receiver   | object configuration: `Foo().apply { a = 1; b = 2 }` |
| `with`  | `this` | lambda result | group calls on an object (not an extension) |

> Anti-pattern: nesting/chaining scope functions until the receiver of a given `this`/`it`
> is ambiguous. Prefer one scope function per expression; name the lambda param when nested.

---

## 2. Coroutines & structured concurrency *(largest area)*

Coroutines = suspendable computations. Library: **`kotlinx.coroutines`** (JetBrains, separate
from stdlib; `suspend` keyword itself is a language feature).

### `suspend` functions
- A `suspend fun` can call other suspend functions and *suspend* (release the thread) at
  suspension points without blocking. It can only be called from another suspend function or
  a coroutine builder.
- Suspension is cooperative — a suspend function that never hits a suspension point (e.g. a
  tight CPU loop or a blocking JDBC call) blocks its thread just like normal code.

### Structured concurrency
Every coroutine belongs to a **`CoroutineScope`**; a scope won't complete until all its
children complete. This makes leaks and forgotten work structurally impossible.
- **`coroutineScope { }`** — suspending scope builder. If *any* child fails, it cancels all
  siblings and rethrows. Waits for all children.
- **`supervisorScope { }`** — like `coroutineScope` but failure is **unidirectional**: a
  child's failure does not cancel siblings or the scope. Children installed directly in it use
  their own `CoroutineExceptionHandler` (like roots).
- **`withContext(ctx) { }`** — switch dispatcher/context for a block, suspending until done;
  the idiomatic way to run blocking IO or CPU work off the current dispatcher.

### Builders
- **`launch { }`** → returns `Job`; fire-and-forget; propagates exceptions as *uncaught*.
- **`async { }`** → returns `Deferred<T>`; `await()` to get the result; exception is deferred
  and thrown at `await()`.
- **`runBlocking { }`** — bridges blocking and suspend worlds (tests, `main`); do NOT use inside
  suspend code.

### `Job`, `CoroutineContext`, `Dispatchers`
- **`CoroutineContext`** is an indexed set of elements: `Job`, `CoroutineDispatcher`,
  `CoroutineName`, `CoroutineExceptionHandler`. Combine with `+`.
- **`Job`** — lifecycle handle (`isActive`, `isCancelled`, `isCompleted`); `cancel()`, `join()`,
  parent/child hierarchy. `SupervisorJob()` gives unidirectional failure.
- **Dispatchers**: `Default` (CPU-bound, threads = cores), `IO` (blocking IO, elastic pool,
  shares threads with Default; use `.limitedParallelism(n)` to cap), `Main` (UI thread; needs a
  platform module), `Unconfined` (starts in caller thread, resumes wherever — advanced/testing).

### Cancellation (cooperative)
- Cancellation throws **`CancellationException`** at the next suspension point. Code must be
  *cooperative*: check `isActive`, call `ensureActive()`, or `yield()` in long CPU loops;
  suspend functions from the library already cooperate.
- **Never swallow `CancellationException`.** `try { … } catch (e: Exception) { }` around suspend
  code will eat cancellation and break structured concurrency. Rethrow it, or catch specific
  exceptions only. (A common correct guard: `catch (e: CancellationException) { throw e }`
  before handling other exceptions.)
- Clean up in `finally`; use `withContext(NonCancellable)` if you must suspend during cleanup.

### Exception handling
- `launch` → exception propagates up to the parent and (at the root) to the
  **`CoroutineExceptionHandler`** or the platform default handler. `async` → exception held in
  the `Deferred`, surfaced at `await()`.
- **`CoroutineExceptionHandler` only fires for root coroutines** (roots of a scope /
  `GlobalScope` / direct children of `supervisorScope`). Installing it on a child coroutine has
  no effect — children delegate to their parent. You **cannot recover** in the handler; the
  coroutine has already failed. It's a last-resort logger, not a `try/catch`.
- **First exception wins**; further exceptions from siblings attach as *suppressed*.
- `CancellationException` is transparent — ignored by handlers, does not cancel the parent.
  A non-`CancellationException` from a child *does* cancel its parent (regular `Job`), and this
  cannot be overridden — that's what `SupervisorJob`/`supervisorScope` exist to change.

### Common pitfalls (reviewer checklist)
- **`GlobalScope`** — unstructured, lives for the whole process, leaks. Flag almost every use;
  prefer an injected scope or `coroutineScope`/`supervisorScope`.
- **Blocking a dispatcher** — `Thread.sleep`, blocking JDBC/file IO, or heavy CPU on
  `Dispatchers.Default`/`Main` without `withContext(Dispatchers.IO)`.
- **Swallowed cancellation** — see above.
- **`async` you never `await`** — the exception silently disappears.
- **Launching without a parent scope**, or capturing a scope that outlives the work.

---

## 3. Flow (`kotlinx.coroutines.flow`)

**`Flow<T>`** = a cold, asynchronous stream of values built on coroutines.

### Cold flows
- A `flow { }` builder's block does **not** run until a terminal operator collects it, and it
  re-runs from scratch for each collector. Builders: `flow { emit(x) }`, `flowOf(a, b)`,
  `iterable.asFlow()`.
- `emit()` is a suspend call; emissions are sequential and honor backpressure automatically.

### Operators
- **Intermediate (cold, lazy):** `map`, `filter`, `transform` (emit 0..N per input), `take`,
  `onEach`, `distinctUntilChanged`, `flatMapConcat` (sequential), `flatMapMerge` (concurrent),
  `flatMapLatest` (cancel previous inner on new value). `zip`, `combine` for merging streams.
- **Terminal (suspend):** `collect`, `toList`/`toSet`, `first`, `single`, `reduce`, `fold`,
  `count`. `launchIn(scope)` collects in a scope without a `collect { }` body (pairs with
  `onEach`).

### Context, backpressure, completion
- **`flowOn(ctx)`** — changes the context of *upstream* operators only (context-preserving);
  the correct way to move producer work to `Dispatchers.IO`. Never call `withContext` inside a
  `flow { }` to emit — that violates context preservation and throws.
- **Backpressure:** `buffer(n)` (decouple producer/consumer), `conflate()` (keep only latest),
  `collectLatest { }` (cancel the collector body when a new value arrives).
- **Completion:** `onCompletion { cause -> }` runs on success or failure (`cause == null` on
  success).

### Exceptions
- **Exception transparency** is the core rule: a flow must never emit from within a
  `try/catch` that catches its own downstream exceptions. Handle upstream failures declaratively.
- **`catch { }`** handles exceptions from *upstream only* (not from the collector); can emit a
  fallback. **`retry(n) { predicate }`** / `retryWhen` restart the upstream on failure.

### Hot flows: `StateFlow` vs `SharedFlow`
- **`StateFlow<T>`** — hot, always has a current `value`, conflated, emits latest to new
  collectors. State holder / observable value. `MutableStateFlow(initial)`. Equality-based
  de-dup (won't re-emit an equal value).
- **`SharedFlow<T>`** — hot, configurable `replay` and buffer, no initial value; for events.
  `MutableSharedFlow(replay, extraBufferCapacity, onBufferOverflow)`.
- **`stateIn(scope, started, initial)`** / **`shareIn(scope, started, replay)`** convert a cold
  flow into a hot one shared across collectors. `started`: `SharingStarted.Eagerly`,
  `.Lazily`, or `.WhileSubscribed(stopTimeoutMillis)` (the common choice — stops upstream when
  no collectors, avoiding leaks).
- Idiom: private `MutableStateFlow` backing a public read-only `StateFlow`
  (`private val _s = MutableStateFlow(…); val s: StateFlow<T> = _s.asStateFlow()`).

### Testing flows
- `kotlinx-coroutines-test`: `runTest { }`, virtual time, `TestDispatcher`/`StandardTestDispatcher`,
  `Dispatchers.setMain(...)`.
- **Turbine** (community — Cash App / Square, *not* JetBrains) is the de-facto library for
  asserting on flow emissions: `flow.test { assertEquals(1, awaitItem()); awaitComplete() }`.

---

## 4. Type system & classes

- **`data class`** — auto `equals`/`hashCode`/`toString`/`componentN`/**`copy`**. Only
  primary-constructor `val`/`var` participate. Enables **destructuring** (`val (a, b) = point`)
  and non-destructive copy (`user.copy(name = "x")`). Reviewer note: don't put mutable `var`s or
  non-value semantics in data classes carelessly.
- **`sealed class` / `sealed interface`** (interfaces Stable since 1.5) — closed hierarchy known
  at compile time; enables **exhaustive `when`** with no `else` (as an *expression*; 2.1 removed
  redundant `else` even in some statement positions). The single most important tool for modeling
  closed sets of states/results — flag `enum`+`when`-with-`else` or class hierarchies that should
  be sealed.
- **Value classes** `@JvmInline value class Meters(val v: Double)` (Stable since 1.5) — zero-cost
  wrapper, inlined at runtime where possible (boxed when used as a generic/nullable/interface).
  Great for type-safe primitives (`UserId`, `Email`). 2.2 adds `@JvmExposeBoxed` for Java interop.
- **`enum class`** — finite set; can have members, implement interfaces, `entries` (Stable, via
  `enumEntries<T>()` since 2.0 — replaces `values()`).
- **`object`** (singleton) and **`companion object`** (per-class static-like holder; can
  implement interfaces, be named, host factory functions and `@JvmStatic` members).
- **Nested vs inner:** nested classes are static-like by default; **`inner`** captures the outer
  instance (`this@Outer`).
- **`open`/`final`/`abstract`** — classes and members are **`final` by default**; must mark
  `open` to allow overriding. `visibility`: `public` (default), `internal` (module), `protected`,
  `private`.
- **Delegation `by`:**
  - *Class delegation*: `class C(b: Base) : Base by b` — implement an interface by forwarding to
    a member (composition over inheritance, no boilerplate).
  - *Delegated properties*: `val x by lazy { … }` (thread-safe once by default),
    `var y by Delegates.observable(init) { _, old, new -> }`, `var z by map` (map-backed),
    `Delegates.vetoable`, and custom `getValue`/`setValue` operators.

---

## 5. Functions & functional style

- **Top-level functions** (no class needed), **extension functions** (`fun String.shout() =
  uppercase()` — resolved statically, not virtual), **infix** (`infix fun`), **operator**
  (`operator fun plus`).
- **Higher-order functions & lambdas** — function types `(A) -> B`, `A.(B) -> C` (receiver),
  `it` for single param, **trailing-lambda** syntax (`list.map { it * 2 }`), named &
  **default arguments** (reduces overloads).
- **`inline` functions** — inline the lambda at the call site (no `Function` object allocation;
  enables non-local returns and `reified`). Modifiers: **`noinline`** (don't inline a specific
  lambda param), **`crossinline`** (inlined but forbids non-local return, e.g. when passed to
  another execution context). Don't `inline` large functions — bytecode bloat.
- **`reified` type parameters** — only in `inline` functions; makes `T` available at runtime:
  `inline fun <reified T> Gson.fromJson(json: String): T = fromJson(json, T::class.java)`.
- Function references: `::foo`, `String::length`, bound `instance::method`.

---

## 6. Generics

- **Declaration-site variance:** `out T` (covariant, producer — `Source<out T>`), `in T`
  (contravariant, consumer — `Comparable<in T>`). Compare to Java wildcards but declared once.
- **Use-site variance (type projection):** `Array<out Any>`, `Array<in String>` at the use site
  when the class itself is invariant.
- **Star projection** `Foo<*>` — unknown type argument; read as `out Any?`, can't safely write.
- **Upper bounds:** `<T : Comparable<T>>`; multiple bounds via **`where`**:
  `fun <T> f(t: T) where T : CharSequence, T : Comparable<T>`.
- **Reified generics** — see §5; the escape hatch from JVM type erasure (only in `inline` fns).

---

## 7. Idioms & stdlib

- **Collections:** `map`/`filter`/`fold`/`reduce`/`groupBy`/`associate`/`associateBy`/
  `flatMap`/`partition`/`sumOf`/`maxByOrNull`. Eager on `List`; use **`asSequence()`** for lazy,
  short-circuiting pipelines over large data (avoids intermediate lists).
- **Preconditions:** `require(cond) { msg }` (arg check → `IllegalArgumentException`),
  `check(cond) { msg }` (state → `IllegalStateException`), `error(msg)` (→
  `IllegalStateException`), `requireNotNull`/`checkNotNull` (smart-cast to non-null).
- **`Result<T>`** — `runCatching { }`, `getOrNull`, `getOrElse`, `map`/`fold`, `onSuccess`/
  `onFailure`. (Note: `Result` as a *return type* / parameter had historical restrictions;
  fine for local flow control.)
- **Ranges:** `1..10`, `1..<10` (`until`), `10 downTo 1`, `step`, `'a'..'z'`; work in `for` and
  `in` checks.
- **String templates:** `"Hello $name, ${user.age} yrs"`; raw strings `"""…"""` with
  `.trimIndent()`.
- **`when` / `if` as expressions** (return a value); **`Pair`/`Triple`** (`to` infix builds a
  Pair) and destructuring (`val (k, v) = entry`).

---

## 8. KSP — Kotlin Symbol Processing

- **What:** JetBrains/Google annotation-processing API that reads the **Kotlin AST directly**
  and *generates* code (it can read but not modify existing source). Used by Room, Moshi, Dagger/
  Hilt, Koin, etc.
- **vs kapt:** kapt generates Java stubs then runs `javac` annotation processors — slow. KSP
  works on Kotlin symbols directly, **~2× faster**, no stubs, Kotlin-native model.
- **KSP2:** default since KSP `2.0.0` — a faster reimplementation with a cleaner API and better
  standalone/CLI support. **KSP1 is deprecated from Kotlin 2.2** and cannot support new language
  features — advise migrating. **kapt is legacy**; migrate to KSP where processors support it
  (K2 kapt exists — `kapt.use.k2=true` — but is a bridge, not the destination).
- **Writing a processor:** implement `SymbolProcessor` + `SymbolProcessorProvider`, register via
  `resolver.getSymbolsWithAnnotation(...)`, visit with `KSVisitor`, emit via `CodeGenerator`.
  Consuming = add the processor with the `ksp(...)` Gradle configuration. (Build-system depth is
  another agent's concern.)

---

## 9. Java interop

- **Calling Java from Kotlin** — mostly transparent; getters/setters become properties; Java
  types without nullability info become **platform types `T!`** (relaxed null checking — the
  main interop hazard; annotate with JSpecify/`@Nullable`/`@NotNull`, which K2 enforces).
- **SAM conversion** — pass a lambda where Java expects a single-abstract-method interface:
  `executor.execute { … }`. (Kotlin interfaces need `fun interface` to get SAM conversion.)
- **Calling Kotlin from Java — the annotation toolkit:**
  - `@JvmStatic` — emit a real static method (on companion/object members).
  - `@JvmOverloads` — generate overloads for default parameters so Java can call them.
  - `@JvmField` — expose a field directly (no getter/setter).
  - `@JvmName("…")` — rename the JVM symbol (resolve clashes, e.g. same erasure).
  - `@Throws(IOException::class)` — declare checked exceptions for Java callers (Kotlin has no
    checked exceptions).
  - `@file:JvmName` / `@JvmMultifileClass` — control the generated file-facade class name.
- **Checked exceptions:** Kotlin doesn't have them — a Kotlin function can throw anything;
  use `@Throws` at the Java boundary.

---

## 10. Kotlin Multiplatform (KMP) — basics

- **Purpose:** share business logic (networking, serialization, domain, validation) across
  platforms while keeping native UI per platform. Not "write once run anywhere" for UI (that's
  Compose Multiplatform, a separate concern).
- **Source sets:** `commonMain` (platform-agnostic code + common APIs) plus platform source sets
  (`jvmMain`, `androidMain`, `iosMain`, `jsMain`, `nativeMain`, `wasmJsMain`).
- **Targets:** JVM, Android, iOS/macOS/watchOS/tvOS (Kotlin/Native), JS, Native (Linux/Windows),
  **Wasm** (`wasmJs`/`wasmWasi`, evolving).
- **`expect`/`actual`** — declare an API in common (`expect fun platformName(): String`) and
  provide a per-platform implementation (`actual fun platformName() = "JVM"`). Works for
  functions, classes, properties, typealiases. In 2.0+, `actual` may be *more* permissive in
  visibility than `expect`, and common/platform source resolution is strictly separated (common
  code cannot accidentally resolve to a platform overload).
- KMP itself is **Stable**; individual targets/libraries vary (Wasm younger than JVM/iOS).

---

## 11. Idioms, anti-patterns & "language debt" — reviewer's checklist

A `language-kotlin-expert` should scan for and flag:

1. **`!!` density** — each is a latent NPE and a defeated type system. Replace with `?.`/`?:`/
   `requireNotNull`/restructuring.
2. **`GlobalScope`** — unstructured concurrency; leaks. Demand a real scope.
3. **Blocking calls on a coroutine dispatcher** — `Thread.sleep`, blocking IO/JDBC, heavy CPU on
   `Default`/`Main` without `withContext(Dispatchers.IO/Default)`.
4. **Swallowing `CancellationException`** — broad `catch (Exception)` in suspend code; must
   rethrow cancellation.
5. **Overusing platform types** — not annotating Java boundaries; nullable data flowing in
   unchecked.
6. **`lateinit` misuse** — using it for values that could be nullable or should be `val`;
   `lateinit` on primitives is illegal and it throws `UninitializedPropertyAccessException` if
   read early. Prefer constructor injection or `by lazy`.
7. **Stringly-typed code** — passing `String`/`Int` where a value class, enum, or sealed type
   would encode the domain.
8. **Not using sealed classes for closed hierarchies** — `when` with an `else` that "shouldn't
   happen", or `enum` + external state, instead of a sealed hierarchy giving compile-time
   exhaustiveness.
9. **Nullable-everywhere** — `T?` fields that are really always set; push nullability to the edges.
10. **Scope-function abuse** — nested/chained `let`/`apply`/`run`/`also` where `this`/`it` is
    ambiguous; `apply` used where a plain constructor call would do.
11. **Mutable shared state across coroutines** without synchronization (`Mutex`, confinement,
    `StateFlow`).
12. **Eager collection chains over large data** where a `Sequence` avoids intermediate allocations.
13. **`data class` misuse** — mutable `var`s, or entities where identity ≠ structural equality.
14. **`async` without `await`**, or launching work in a scope that outlives its owner.

---

## Sources

### Official (kotlinlang.org / JetBrains)
- What's new in Kotlin 2.2 — https://kotlinlang.org/docs/whatsnew22.html
- What's new in Kotlin 2.1 — https://kotlinlang.org/docs/whatsnew21.html
- What's new in Kotlin 2.0 — https://kotlinlang.org/docs/whatsnew20.html
- Null safety — https://kotlinlang.org/docs/null-safety.html
- Coroutine exception handling — https://kotlinlang.org/docs/exception-handling.html
- Asynchronous Flow — https://kotlinlang.org/docs/coroutines-flow.html
- KSP FAQ / overview — https://kotlinlang.org/docs/ksp-faq.html , https://kotlinlang.org/docs/ksp-overview.html
- (Reference, not re-fetched this pass but authoritative for their topics) Coroutines guide —
  https://kotlinlang.org/docs/coroutines-guide.html ; Scope functions —
  https://kotlinlang.org/docs/scope-functions.html ; Sealed classes —
  https://kotlinlang.org/docs/sealed-classes.html ; Inline value classes —
  https://kotlinlang.org/docs/inline-classes.html ; Generics —
  https://kotlinlang.org/docs/generics.html ; Java interop —
  https://kotlinlang.org/docs/java-to-kotlin-interop.html ; KMP —
  https://kotlinlang.org/docs/multiplatform.html
- `kotlinx.coroutines` API docs — https://kotlinlang.org/api/kotlinx.coroutines/

### Community (verify independently; NOT JetBrains)
- Turbine (Cash App / Square) — Flow testing library — https://github.com/cashapp/turbine
- Android Developers "Migrate from kapt to KSP" (Google, Android-focused) —
  https://developer.android.com/build/migrate-to-ksp

> Version-sensitivity flags carried inline throughout §0. Recheck any Preview/Beta/Experimental
> feature (context parameters, context-sensitive resolution, nested type aliases, `@all:`,
> `@JvmExposeBoxed`, explicit backing fields) against the *exact* Kotlin version in the target
> project before advising it as production-ready.
