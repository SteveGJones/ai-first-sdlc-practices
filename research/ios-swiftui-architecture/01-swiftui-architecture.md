# Modern iOS App Architecture in SwiftUI (2025 / iOS 26)

Reference knowledge base for the `swiftui-architect` agent. Scope is **app
architecture** — state, patterns, navigation, persistence, concurrency, DI,
interop, testing, anti-patterns. Visual design / HIG is explicitly out of scope
(separate agent).

Version baseline: **iOS 26 / Xcode 26 / Swift 6.2** (WWDC 2025), with the
iOS 17 (Observation), iOS 16 (NavigationStack), iOS 17/18 (SwiftData) lineage
called out per-API because most production apps still support back-deployment.
Sources are listed at the end; Apple docs at developer.apple.com are the primary
authority, community patterns (TCA, Factory, swift-dependencies) are labelled as
such.

---

## 1. State Management — the Observation framework

### 1.1 The core shift: `@Observable` replaced `ObservableObject`

Apple's **Observation** framework (module `Observation`, **iOS 17 / macOS 14 /
Swift 5.9+**) introduced the `@Observable` macro, which is now the recommended
way to make reference-type model data observable by SwiftUI. It **supersedes the
Combine-based `ObservableObject` / `@Published` / `@StateObject` /
`@ObservedObject` / `@EnvironmentObject` stack** for new code.

```swift
import Observation

@Observable
final class LibraryModel {
    var books: [Book] = []       // observable automatically — no @Published
    var isLoading = false
    private var cache: [UUID: Book] = [:]  // still tracked; hide with access control
}
```

What the macro does under the hood: it synthesizes conformance to the
`Observable` protocol and rewrites stored properties to route through
`ObservationRegistrar`, calling `access(_:keyPath:)` on read and
`withMutation(keyPath:)` on write. SwiftUI wraps view `body` evaluation in
`withObservationTracking(_:onChange:)`, so a view re-renders **only when a
property it actually read during `body` changes** — property-level granularity,
not object-level.

### 1.2 Why it's better than `ObservableObject`

- **No `@Published`.** Every stored property is observable by default.
- **Precise invalidation.** `ObservableObject` fires `objectWillChange` for *any*
  `@Published` mutation, re-rendering every observing view. `@Observable` tracks
  per-keyPath, so unrelated views don't redraw. This is the biggest performance win.
- **No Combine dependency**; works with computed properties, nested objects, and
  collections; tracks properties accessed through arrays/optionals.
- **Less ceremony** — a plain class + one macro.

### 1.3 Property wrappers — when to use each (with `@Observable`)

| Wrapper | Purpose | Owns lifetime? | Typical use |
|---|---|---|---|
| `@State` | View-local source of truth. **Also how you own an `@Observable` reference type** (replaces `@StateObject`). | Yes | Value-type view state (`Bool`, `Int`, structs); creating/owning an `@Observable` model instance for a view subtree. |
| `@Binding` | Two-way reference to state owned elsewhere. | No | Child needs read/write to a parent's value. |
| `@Bindable` | Get `Binding`s to the properties of an `@Observable` object you already have. | No | Passing `$model.name` into a `TextField`/`Toggle`; binding `NavigationStack(path:)`. |
| `@Environment` | Read an `@Observable` object (or a value) injected into the environment. | No | App/feature-wide shared model; `@Environment(AppModel.self)`. |

Key mental-model change from the legacy world:

- **`@StateObject` → `@State`.** With `@Observable`, you *own* a model with plain
  `@State`: `@State private var model = LibraryModel()`. SwiftUI keeps it alive
  across `body` re-evaluations exactly like `@StateObject` did.
- **`@ObservedObject` → nothing / plain property.** A model passed in from a parent
  is just `let model: LibraryModel`. Observation still tracks it.
- **`@EnvironmentObject` → `@Environment(Type.self)`**, injected with
  `.environment(model)` (no key path needed).
- **`@Bindable`** is the new piece with no legacy equivalent — it exists purely to
  vend `Binding`s from an `@Observable` object to UI controls.

```swift
struct ProfileView: View {
    @Environment(AppModel.self) private var app        // read shared model
    @Bindable var user: User                           // vend bindings from it

    var body: some View {
        @Bindable var app = app                        // local @Bindable to bind env object
        TextField("Name", text: $user.name)            // needs @Bindable
        Toggle("Notifications", isOn: $app.notificationsOn)
    }
}
```

Note the idiom `@Bindable var app = app` *inside* `body` — you cannot mark an
`@Environment` property `@Bindable` directly, so you shadow it locally when you
need bindings out of an environment object.

### 1.4 `@Observable` is NOT a drop-in replacement (important nuances)

- You **cannot** use `@StateObject`/`@ObservedObject`/`@EnvironmentObject` with an
  `@Observable` class — compile-time mismatch. Migration is per-type, but the view
  wrappers must move together with the model.
- Observation tracks only properties **read during `body`**. If a view never reads
  a property, changes to it won't refresh that view (usually desirable).
- **`Binding`/computed edge cases:** a view that only holds a `Binding` into an
  object won't necessarily re-render on unrelated changes — different from the
  broad `objectWillChange` behaviour some code relied on.
- Back-deployment: `@Observable` needs iOS 17+. Apps supporting iOS 16 and earlier
  keep `ObservableObject`, or use the Point-Free `swift-perception` backport.

### 1.5 iOS 26 additions

- **`@Observable` in UIKit:** iOS 26 brings automatic Observation tracking to
  UIKit (`UIView`/`UIViewController` update methods re-run on tracked changes),
  unifying the model layer across both frameworks.
- **Single source of truth** remains the governing principle: each piece of state
  has exactly one owner; everything else gets a `Binding` or a read-only reference.
  Data flows **down** (environment / init / bindings) and events flow **up**.

---

## 2. Architectural Patterns

### 2.1 "Vanilla SwiftUI" / MV (Model–View)

Apple's own sample code (e.g. *Food Truck*, *Backyard Birds*, the SwiftData
samples) uses a **Model–View** approach: `@Observable` model objects injected via
`@Environment`, views reading them directly, no per-screen ViewModel layer. The
view *is* the "view model" — SwiftUI's property wrappers already provide binding
and lifecycle. This is the lowest-ceremony option and what Apple demonstrates.

- **Strengths:** minimal boilerplate; leverages the framework as designed; great
  for small–medium apps; previews trivially.
- **Weaknesses:** logic can leak into views ("massive view") without discipline;
  no obvious seam for unit testing view logic; shared mutable state needs care.

### 2.2 MVVM in SwiftUI — and the "do we still need ViewModels?" debate

MVVM in SwiftUI means an `@Observable` **ViewModel** class that owns view state
and async work; the view holds it via `@State` (owning) or reads via
`@Environment`, and renders from it.

```swift
@Observable
final class BookListViewModel {
    private(set) var books: [Book] = []
    var query = ""
    private let service: BookService
    init(service: BookService) { self.service = service }
    func load() async { books = await service.fetch(matching: query) }
}
```

The debate (well-worn in the community, e.g. Azam Sharp vs. traditional MVVM
advocates):

- **Pro-ViewModel:** clean seam for unit tests; keeps side effects/async out of
  the view; familiar to the whole team; pairs naturally with initializer-based DI.
- **Anti-ViewModel ("MV" camp):** with `@Observable`, the view already binds to a
  model reactively, so a per-view ViewModel is often redundant ceremony that
  duplicates model state and fights SwiftUI's data flow. Apple's samples don't use
  ViewModels. A common middle ground: **not every view needs a ViewModel** — pure
  presentational views (Text/Image) never do; introduce a ViewModel only where a
  screen has real logic/async to isolate, and prefer domain model objects over
  screen-shaped VMs.

Practical guidance for the agent: default to **MV with `@Observable` domain
models**; add a ViewModel *only* when a screen has non-trivial orchestration,
form state, or a testing seam you actually need. Don't reflexively pair every View
with a ViewModel.

### 2.3 The Composable Architecture (TCA) — Point-Free (community, not Apple)

TCA (`pointfreeco/swift-composable-architecture`) is a **unidirectional**,
Elm/Redux-inspired architecture. Core pieces:

- **State** — a value type (`struct`) describing a feature's full state.
- **Action** — an enum of every event (user actions, effect results).
- **Reducer** — the `@Reducer` macro on a type with a `body` returning
  `Reduce`/composed reducers; a pure `(inout State, Action) -> Effect<Action>`
  that mutates state and returns effects.
- **Effect** — side-effect description; async work via `.run { send in ... }`.
- **Store** — runtime that holds state and feeds actions to the reducer;
  SwiftUI reads it (modern TCA uses `@ObservableState` on the state, integrating
  with the Observation framework so views observe precisely).
- **Dependencies** — TCA ships with `swift-dependencies` for controlled effects.
- **`TestStore`** — exhaustive, assert-every-state-change testing.

```swift
@Reducer
struct Counter {
    @ObservableState struct State { var count = 0 }
    enum Action { case increment, factButton, factResponse(String) }
    @Dependency(\.numberFact) var numberFact
    var body: some ReducerOf<Self> {
        Reduce { state, action in
            switch action {
            case .increment: state.count += 1; return .none
            case .factButton:
                return .run { [count = state.count] send in
                    await send(.factResponse(try numberFact.fetch(count)))
                }
            case let .factResponse(fact): /* ... */ return .none
            }
        }
    }
}
```

- **Strengths:** deterministic, exhaustively testable state machines; reducer
  composition scales to large apps; first-class dependency control; consistent
  navigation/effect story; great for complex, stateful, side-effect-heavy features.
- **Tradeoffs:** significant boilerplate and learning curve (Redux/functional
  concepts); it's a large third-party dependency you must track across Swift/iOS
  releases; overkill for simple apps; performance requires care in very large
  stores. Worth it "only when state determinism is a product requirement."

**When each fits (agent heuristic):**

- Small/medium app, standard CRUD + navigation → **MV with `@Observable`**.
- Screen with meaningful logic/testing needs → **MV + a targeted ViewModel**.
- Large app, complex interdependent state, strong testability/determinism mandate,
  team bought into the paradigm → **TCA** (or another explicit unidirectional
  architecture such as MVVM-C with coordinators).

---

## 3. Navigation

### 3.1 `NavigationStack` (iOS 16+) replaced `NavigationView`

`NavigationView` is **deprecated**. Modern navigation is `NavigationStack` (single
column, push/pop) and `NavigationSplitView` (2–3 column, iPad/Mac). The defining
change is **value-based, data-driven navigation**: you push *values*, and a
`navigationDestination(for:)` modifier maps a value type to a destination view.

```swift
NavigationStack {
    List(books) { book in
        NavigationLink(book.title, value: book)      // pushes a VALUE
    }
    .navigationDestination(for: Book.self) { book in  // maps type -> view
        BookDetailView(book: book)
    }
}
```

### 3.2 `NavigationPath` and programmatic / deep-link navigation

Bind the stack to a path to control it programmatically:

```swift
@State private var path = NavigationPath()   // type-erased, heterogeneous
NavigationStack(path: $path) { … }
// push:  path.append(book)
// pop:   path.removeLast()
// root:  path = NavigationPath()
```

- Use a **typed array** (`@State var path: [Route]` where `Route: Hashable`) when
  the stack is homogeneous — easier to inspect/test and to encode.
- Use **`NavigationPath`** when the stack mixes value types.
- **Deep links:** parse the incoming `URL` (`.onOpenURL`) or
  `NavigationPath.CodableRepresentation` (persist/restore) into path mutations —
  because navigation is just data, deep linking is "append the right values."
- A common scalable pattern (community): a **Router/Coordinator** `@Observable`
  object holding the `path`, injected via `@Environment`, exposing intent methods
  (`router.showDetail(book)`), keeping navigation logic out of views (MVVM-C).

### 3.3 `NavigationSplitView`

Two- or three-column adaptive layout (sidebar / content / detail). Drives
selection via bindings; collapses to a stack on compact width. Preferred for
iPad/Mac and multi-pane iPhone-to-iPad universal apps.

### 3.4 Common pitfalls migrating from `NavigationView`

- **Old-style `NavigationLink(destination:)` inside `NavigationStack`** works but
  is discouraged — it can't be driven programmatically and breaks the value model.
  Prefer `NavigationLink(value:)` + `navigationDestination(for:)`.
- **`navigationDestination` placement:** must be inside the `NavigationStack`'s
  view hierarchy (attached to a view *within* the stack, not conditionally hidden).
  A destination inside a `List` cell or a lazily-rendered branch may not register
  → "tapping does nothing." Put it on a stable container.
- **Duplicate/ambiguous destinations:** multiple `navigationDestination(for:)` for
  the same type in one stack → last one wins / undefined; register each type once.
- **`NavigationPath` + `@Observable` router:** a known iOS 17 wrinkle — bind the
  stack to `$router.path` via a local `@Bindable`; ensure the path property is
  observed correctly.
- **State restoration:** persist the path (`Codable` path) rather than a screen enum.
- Nested `NavigationView`s (old habit) → double bars; use one `NavigationStack`
  per navigation context.

---

## 4. Persistence & Data

### 4.1 SwiftData — the modern default (iOS 17+)

**SwiftData** (`import SwiftData`, iOS 17/macOS 14) is Apple's Swift-native
persistence framework, built on Core Data's store but with a macro-driven,
value-friendly API. It provides persistence, schema modeling, migration, object
graph management, and optional CloudKit sync.

```swift
@Model
final class Trip {
    var name: String
    var startDate: Date
    @Attribute(.unique) var id: UUID
    @Relationship(deleteRule: .cascade, inverse: \Accommodation.trip)
    var accommodations: [Accommodation] = []
    init(name: String, startDate: Date, id: UUID = .init()) { … }
}
```

Core building blocks:

- **`@Model` macro** — turns a class into a persistent model; stored properties
  become persisted attributes; the class is also `Observable`, so SwiftData models
  integrate with SwiftUI observation directly.
- **`ModelContainer`** — the persistent backing store; created once and injected
  with `.modelContainer(for: Trip.self)` on the app/scene.
- **`ModelContext`** — the unit-of-work for inserts/deletes/saves; read from
  `@Environment(\.modelContext)`. Autosaves by default on the main context.
- **`@Query`** — property wrapper that fetches and **auto-updates** the view when
  the store changes: `@Query(sort: \Trip.startDate) var trips: [Trip]`. Supports
  `filter:` (`#Predicate`), `sort:`, `order:`, and dynamic queries.
- **`@Attribute`** — options like `.unique`, `.externalStorage`, `.transformable`,
  original-name for renames.
- **`@Relationship`** — delete rules (`.cascade`, `.nullify`, `.deny`), inverses,
  min/max counts; relationships inferred when possible.

### 4.2 Migrations

- **Lightweight** migrations happen automatically for additive/compatible changes.
- **Complex** migrations use **`VersionedSchema`** (a snapshot of the model set at a
  version) + **`SchemaMigrationPlan`** with ordered **`MigrationStage`s**
  (`.lightweight` or `.custom` with `willMigrate`/`didMigrate` closures). The plan
  is passed to the `ModelContainer` so it migrates through every intermediate
  version, preserving user data. (iOS 17 = schema v2.x; iOS 18 added
  `#Index`/`#Unique` macros and property preservation on delete; iOS 26 added
  **class inheritance** in models.)

### 4.3 SwiftData + CloudKit sync

SwiftData syncs to a private CloudKit database when the container is configured
with a CloudKit entitlement (`cloudKitDatabase`). **Constraints imposed by
CloudKit** (agent must warn about these):

- All properties must be **optional or have default values**.
- **No `.unique`** attributes (uniqueness constraints unsupported over CloudKit).
- Relationships must be **optional**, and **`.deny` delete rules are not allowed**.
- Use `initializeCloudKitSchema` (dev/one-time) to push the schema to CloudKit.
- Known rough edges reported through iOS 18 betas around relationships + CloudKit;
  test sync thoroughly.

### 4.4 Core Data interop and when to still use Core Data

- SwiftData and Core Data can **coexist on the same store** (shared persistent
  store / `NSPersistentContainer` + SwiftData `ModelContainer`) for incremental
  migration.
- **Still choose Core Data** when you need: features SwiftData lacks or exposes
  awkwardly (fine-grained `NSFetchedResultsController`, complex fetch/aggregation,
  child contexts, custom store types, abstract entities historically), heavy
  batch operations, mature/edge-case migrations, or must support iOS < 17.
- For most **new** apps on iOS 17+ → **SwiftData**; drop to the underlying Core
  Data API only for the gaps.

### 4.5 Lighter-weight storage

- **`@AppStorage`** — property wrapper over `UserDefaults` for small user settings/
  flags; reactive in SwiftUI. **`@SceneStorage`** for per-scene UI state
  restoration. Not for large or sensitive data.
- **`UserDefaults`** directly for non-UI settings.
- **File system** (`FileManager`, `URL` in Application Support/Documents/Caches) for
  documents, blobs, caches; combine with `Codable`. Consider
  `DocumentGroup`/`FileDocument` for document-based apps.
- **Keychain** for secrets/tokens (never `UserDefaults`/`@AppStorage`).

---

## 5. Concurrency at the UI Boundary

### 5.1 Structured concurrency in views

- **`.task { }`** — the primary async entry point in a view; runs when the view
  appears and is **automatically cancelled when the view disappears**. Use
  `.task(id:)` to restart when an input changes. Prefer it over `.onAppear { Task {…} }`
  because of lifecycle-bound cancellation.
- **`async`/`await`** freely inside `.task`, button actions (`Button { Task { await … } }`),
  and refreshable (`.refreshable { await vm.reload() }`).
- **`AsyncStream` / `AsyncSequence`** — bridge callbacks/notifications into
  `for await` loops consumed in `.task`; ideal for continuous updates
  (locations, sockets). Cancellation of the task tears down the loop.

### 5.2 `@MainActor` and actors for models

- SwiftUI's `View` protocol is `@MainActor`; view `body` and most SwiftUI updates
  run on the main actor. UI mutation must be on `@MainActor`.
- Mark UI-facing `@Observable` models **`@MainActor`** so their mutable state is
  main-actor-isolated and safe to bind to views. Do expensive/IO work off the main
  actor with `await` calls into **`actor`** types or `nonisolated`/`Task.detached`
  work, then hop back (implicitly, by being on a `@MainActor` model method).
- Use dedicated **`actor`** types for shared mutable non-UI state (caches, network
  coordinators) to get data-race-free isolation.

### 5.3 Cancellation

- Cooperative: check `Task.isCancelled` / call `try Task.checkCancellation()` in
  long loops; `.task` cancels automatically on disappear; `.task(id:)` cancels+restarts.
- `async` APIs (`URLSession.data`, `Task.sleep`) throw `CancellationError` on cancel.

### 5.4 Swift 6 strict concurrency & `Sendable` (architecture implications)

- **Swift 6 language mode** enforces **complete data-race checking** at compile
  time. Types crossing concurrency boundaries must be **`Sendable`** (value types
  auto-infer it; reference types need `final` + immutable/`@unchecked`/actor
  isolation). This pushes architecture toward: value-type models, actor-isolated
  shared state, and `@MainActor` UI models.
- **Swift 6.2 (Xcode 26)** softened onboarding with **default main-actor
  isolation** — a module-level mode where code is `@MainActor` by default, so
  single-threaded app code "just works" and you opt *into* concurrency with
  `nonisolated`/actors. This is the recommended posture for most app targets:
  keep UI + models on the main actor, isolate only the genuinely concurrent parts.
  `@concurrent` / `nonisolated` mark the escape hatches.
- Practical guidance: annotate ViewModels/models `@MainActor`; make DTOs and value
  models `Sendable`; wrap shared mutable services in `actor`s; expect the compiler
  to force `Sendable`/isolation decisions — treat them as architecture, not noise.

---

## 6. Dependency Injection & Modularization

### 6.1 DI approaches (Apple-native first)

- **Environment-based DI** — inject `@Observable` services with
  `.environment(service)` and read with `@Environment(Service.self)`; or define a
  custom `EnvironmentKey`/`@Entry` value. Idiomatic and Apple-blessed, but tied to
  the view lifecycle and awkward for non-view (ViewModel/service) layers and unit
  tests in isolation.
- **Initializer injection** — pass dependencies into ViewModels/services via `init`.
  Most explicit, most testable, framework-agnostic. Downside: "prop drilling"
  through intermediate layers, which factories/containers exist to relieve.

### 6.2 Community DI libraries (labelled non-Apple)

- **swift-dependencies** (Point-Free) — DI inspired by SwiftUI's Environment,
  powered by task-local values. You register dependencies via `DependencyKey`
  (with `liveValue`/`testValue`/`previewValue`) and read them with
  `@Dependency(\.apiClient)`. Excels at controlling "uncontrollable" dependencies
  (Date, UUID, clocks, network) and overriding them in tests/previews
  (`withDependencies { … }`). Core to TCA but usable standalone.
- **Factory** (hmlongco) — lightweight container-based DI; compile-time-safe,
  supports scopes, parameters, contexts, SwiftUI previews, and test overrides.
  Popular non-TCA choice.
- Others: Swinject (runtime container, older), Resolver (deprecated in favor of Factory).

Agent heuristic: **Environment or initializer injection** for most apps; reach for
**swift-dependencies** (especially with TCA) or **Factory** when you have many
cross-cutting services and want centralized, test/preview-overridable wiring.

### 6.3 SwiftPM modularization

- Break the app into **local Swift packages** (SwiftPM) with **feature modules**
  (one product per feature) plus shared **`Core`/`DesignSystem`/`Models`/
  `Networking`** modules. The app target becomes a thin composition root.
- Benefits: enforced boundaries (only `public` API leaks), **faster incremental
  builds**, isolated **SwiftUI previews** per module, and per-module test targets.
- Keep dependencies acyclic; interfaces (protocols) in a lightweight module,
  implementations behind them, injected at the composition root — enables mocking.
- This is the standard scaling structure; TCA's reducer composition and
  swift-dependencies both align well with per-feature packages.

---

## 7. UIKit Interop

- **`UIViewRepresentable`** — wrap a `UIView` for use in SwiftUI. Implement
  `makeUIView(context:)`, `updateUIView(_:context:)`, and optionally
  `makeCoordinator()`. Use for mature UIKit views SwiftUI lacks (e.g. certain
  `MKMapView`/`WKWebView`/camera/text-heavy controls — though iOS 26 adds a native
  SwiftUI `WebView`).
- **`UIViewControllerRepresentable`** — same pattern for a `UIViewController`
  (`makeUIViewController`/`updateUIViewController`). Use for `UIImagePickerController`,
  `PHPicker`, `SFSafariViewController`, `UIPageViewController`, etc.
- **Coordinator pattern** — the `Coordinator` (an `NSObject` you return from
  `makeCoordinator()`) acts as the **delegate/data-source** target, bridging
  UIKit's delegation to SwiftUI state (usually via `@Binding`s). This is *the*
  standard way to receive callbacks from wrapped UIKit.
- **`UIHostingController`** — host a SwiftUI view **inside** a UIKit app; push/present
  it like any view controller. Basis for **incremental adoption**: introduce SwiftUI
  screen-by-screen into a UIKit app without a rewrite. `UIHostingConfiguration` embeds
  SwiftUI in `UICollectionView`/`UITableView` cells.
- **When to drop to UIKit:** performance-critical/complex custom drawing, advanced
  text (`UITextView` features), fine-grained collection layouts, camera/AR, or any
  API not yet surfaced in SwiftUI. Otherwise stay in SwiftUI.
- **Data flow across the boundary:** pass SwiftUI state in via properties/bindings;
  send UIKit events back via the Coordinator → `@Binding`/closure. Avoid duplicating
  state on both sides. iOS 26's UIKit Observation support makes keeping UIKit views
  in sync with `@Observable` models much cleaner.

---

## 8. Testing

### 8.1 Swift Testing (`import Testing`) — the modern framework

Introduced WWDC 2024, shipped with **Swift 6 / Xcode 16**, and the default for new
test targets in Xcode 26. Macro-based and concurrency-native.

- **`@Test`** — marks any function (any name, free or in a type) as a test; no
  `test` prefix, no `XCTestCase` subclassing. Supports display names and traits.
- **`#expect(...)`** — soft assertion using ordinary Swift expressions; on failure
  it **captures and displays the operand values** and *continues* the test.
- **`#require(...)`** — like `#expect` but **throws to halt** the test on failure;
  must be called with `try`. Great for unwrapping optionals
  (`let x = try #require(optional)`).
- **Parameterized tests** — `@Test(arguments: […])` runs the test once per input
  (replaces XCTest's manual loops).
- **Suites** — a plain `struct`/`class` grouping tests; a fresh instance per test
  gives natural state isolation. `@Suite` for configuration; `init`/`deinit`
  replace `setUp`/`tearDown`.
- **Async-native** — just `await`; no `XCTestExpectation`/`waitForExpectations`.
  **Runs tests in parallel by default** (in-process), including async tests.
- **Traits** — `.tags`, `.enabled(if:)`, `.disabled`, `.timeLimit`,
  `.serialized` (opt out of parallelism), `.bug(...)`.

```swift
import Testing
@testable import MyApp

@Suite struct BookListTests {
    @Test func loadsBooks() async throws {
        let vm = BookListViewModel(service: MockBookService())
        await vm.load()
        #expect(vm.books.count == 3)
        let first = try #require(vm.books.first)
        #expect(first.title == "Dune")
    }
    @Test(arguments: ["", "  ", "\n"]) func rejectsBlankQuery(_ q: String) {
        #expect(BookListViewModel.isValid(query: q) == false)
    }
}
```

### 8.2 Swift Testing vs XCTest

- **Prefer Swift Testing** for new unit/logic tests: less ceremony, better failure
  diagnostics, parallel + async by design, parameterization.
- **XCTest is still required** for **UI tests (`XCUITest`)** and **performance tests
  (`measure`/`XCTMetric`)** — Swift Testing does not (yet) cover these. The two
  frameworks coexist in the same project/target set.

### 8.3 Testing `@Observable` models

Because `@Observable` models are plain classes with injected dependencies, testing
is direct: construct with mock/stub dependencies (or swift-dependencies /
Factory overrides), invoke methods (`await` async ones), and `#expect` on the
resulting state. This is the main reason to keep side effects in a model/ViewModel
rather than in the view. `@MainActor` models → mark tests `@MainActor` or await into them.

### 8.4 Previews and UI testing

- **`#Preview`** macro — previews are a first-class *development* tool, not a test,
  but they exercise real view code with sample/mock data and are the fastest inner
  loop. Provide preview data via in-memory `ModelContainer`
  (`.modelContainer(…, inMemory: true)`), `previewValue` dependencies, or sample
  `@Observable` models. Per-module previews are a benefit of SwiftPM modularization.
- **UI testing** — `XCUITest` for end-to-end; give views stable
  **`.accessibilityIdentifier`s** for reliable queries; keep UI tests few and
  high-value, pushing logic coverage down to fast unit tests on models.

---

## 9. Anti-Patterns & Pitfalls

- **Massive views.** Business/async logic stuffed into `body`. Fix: extract
  subviews and move logic into `@Observable` models/ViewModels; `body` should read
  as declarative composition.
- **Using `@State` for reference types (pre-Observation habits) / misusing wrappers.**
  With `@Observable`, own models with `@State`; do **not** try to pair `@Observable`
  with `@StateObject`/`@ObservedObject`/`@EnvironmentObject` (won't compile / wrong
  semantics). Conversely, don't wrap value types in classes just to store them.
- **Over-using `ObservableObject`.** New code on iOS 17+ should use `@Observable`;
  `ObservableObject`'s object-level invalidation causes unnecessary redraws. Keep
  `ObservableObject` only for back-deployment < iOS 17.
- **Coarse invalidation / god objects.** One giant observable app model read by
  every view re-renders broadly (less so with `@Observable`'s per-keyPath tracking,
  but still) — scope state to where it's used; split large models.
- **Navigation-state sprawl.** Navigation flags scattered as booleans
  (`@State var showDetail`, `isPresented` chains) across views. Prefer value-based
  navigation with a single `NavigationPath`/typed route array, ideally owned by a
  Router; makes deep links and restoration tractable.
- **Legacy `NavigationLink(destination:)` inside `NavigationStack`**, or
  misplaced/duplicated `navigationDestination` → dead taps. Use value links + one
  destination per type on a stable container.
- **Blocking the main actor.** Synchronous heavy work (JSON, disk, crypto) in
  `body`, `.onAppear`, or a `@MainActor` method janks the UI. Move to actors /
  background tasks and `await`. Don't do sync I/O on the main thread.
- **Ignoring Swift 6 concurrency warnings / `@unchecked Sendable` everywhere.**
  Silencing data-race diagnostics reintroduces the races the compiler caught.
  Model isolation deliberately (`@MainActor` UI, `actor` shared state, `Sendable`
  value models).
- **Retain cycles in closures/effects.** Escaping closures (Combine sinks, task
  closures, delegate captures) capturing `self` strongly → leaks. Use
  `[weak self]` (or capture only what's needed) in long-lived closures; prefer
  structured `.task` (auto-cancelled) over unmanaged `Task {}` that outlives the view.
- **Doing async work in `.onAppear { Task {} }`** instead of `.task` — loses
  automatic cancellation on disappear. Prefer `.task` / `.task(id:)`.
- **Storing large/sensitive data in `@AppStorage`/`UserDefaults`.** Use the file
  system/SwiftData for size, Keychain for secrets.
- **Fighting the framework.** Manually forcing view refreshes, mirroring one source
  of truth in multiple places, or wrapping everything in ViewModels reflexively.
  Trust single-source-of-truth + Observation.

---

## Quick decision cheatsheet (for the agent)

- **Model observability:** `@Observable` (iOS 17+); `ObservableObject` only for < iOS 17.
- **Own a model in a view:** `@State`. **Vend bindings from it:** `@Bindable`.
  **Shared across subtree:** `@Environment(Type.self)` + `.environment(...)`.
- **Architecture:** MV with `@Observable` by default → targeted ViewModel where
  logic warrants → TCA for large, determinism-critical, side-effect-heavy apps.
- **Navigation:** `NavigationStack` + value links + `navigationDestination(for:)` +
  a `NavigationPath`/typed route array (Router-owned for complex flows).
- **Persistence:** SwiftData (`@Model`/`ModelContainer`/`@Query`) default; Core Data
  for gaps/legacy; `@AppStorage` for settings; Keychain for secrets; CloudKit via
  SwiftData with its constraints.
- **Concurrency:** `.task` for lifecycle-bound async; `@MainActor` models; `actor`s
  for shared state; embrace Swift 6.2 default main-actor isolation.
- **DI:** Environment/init injection default; swift-dependencies or Factory when
  cross-cutting; SwiftPM feature modules to scale.
- **Testing:** Swift Testing (`@Test`/`#expect`/`#require`) for logic; XCTest/XCUITest
  for UI + performance; previews as the inner loop.

---

## Sources

Official Apple (primary authority):

- Observation framework — https://developer.apple.com/documentation/Observation
- Managing model data in your app — https://developer.apple.com/documentation/swiftui/managing-model-data-in-your-app
- SwiftData: Dive into inheritance and schema migration (WWDC25) — https://developer.apple.com/videos/play/wwdc2025/291/
- Apple Developer Forums — NavigationPath with @Observable — https://developer.apple.com/forums/thread/733238
- Apple Developer Forums — migrating to modern (iOS 16+) navigation — https://developer.apple.com/forums/thread/807010
- Apple Developer Forums — SwiftData relationships + CloudKit (iOS 18) — https://developer.apple.com/forums/thread/763713
- Apple Developer Forums — migrating schemas in SwiftData + CloudKit — https://developer.apple.com/forums/thread/764236

Community / well-regarded practitioners (labelled non-Apple):

- Donny Wals — @Observable in SwiftUI explained — https://www.donnywals.com/observable-in-swiftui-explained/
- Jesse Squires — @Observable is not a drop-in replacement for ObservableObject — https://www.jessesquires.com/blog/2024/09/09/swift-observable-macro/
- Nil Coalescing — Using @Observable in SwiftUI views — https://nilcoalescing.com/blog/ObservableInSwiftUI/
- Fatbobman — SwiftData limitations before adopting — https://fatbobman.com/en/posts/key-considerations-before-using-swiftdata/
- Fatbobman — resolving iCloud sync / initializeCloudKitSchema — https://fatbobman.com/en/snippet/resolving-incomplete-icloud-data-sync-in-ios-development-using-initializecloudkitschema/
- Fatbobman — Modern SwiftUI Navigation (NavigationStack / NavigationSplitView) — https://fatbobman.com/en/posts/new_navigator_of_swiftui_4/
- Fatbobman — SwiftUI Environment concepts and practice — https://fatbobman.com/en/posts/swiftui-environment-concepts-and-practice/
- Fatbobman — Swift Testing: #expect vs #require — https://fatbobman.com/en/snippet/swift-testing-differences-between-expect-and-require/
- Swift with Majid — Mastering NavigationStack / deep linking — https://swiftwithmajid.com/2022/06/21/mastering-navigationstack-in-swiftui-deep-linking/
- Swift with Majid — SwiftUI Performance: how to use UIKit — https://swiftwithmajid.com/2025/03/04/swiftui-performance-how-to-use-uikit/
- Swift by Sundell — Programmatic navigation in SwiftUI — https://www.swiftbysundell.com/articles/swiftui-programmatic-navigation/
- Swift by Sundell — SwiftUI and UIKit interoperability — https://www.swiftbysundell.com/articles/swiftui-and-uikit-interoperability-part-1/
- AzamSharp — The Ultimate SwiftData Guide — https://azamsharp.com/2023/07/04/the-ultimate-swift-data-guide.html
- SwiftAndTips — Is MVVM necessary for developing apps with SwiftUI? — https://swiftandtips.com/is-mvvm-necessary-for-developing-apps-with-swiftui
- Point-Free — The Composable Architecture — https://github.com/pointfreeco/swift-composable-architecture
- Point-Free — swift-dependencies — https://github.com/pointfreeco/swift-dependencies
- hmlongco — Factory (DI container) — https://github.com/hmlongco/Factory
- Hacking with Swift — Complete concurrency by default (Swift 6.0) — https://www.hackingwithswift.com/swift/6.0/concurrency
- A. van der Lee — Integrating SwiftUI with UIKit (UIViewRepresentable) — https://www.avanderlee.com/swiftui/integrating-swiftui-with-uikit/
- Hacking with Swift — Using coordinators to manage SwiftUI view controllers — https://www.hackingwithswift.com/books/ios-swiftui/using-coordinators-to-manage-swiftui-view-controllers
- ExploreSwiftUI — WWDC25 iOS 26 SwiftUI features — https://exploreswiftui.com/wwdc25
- Fatbobman's Swift Weekly #88 (WWDC 2025 special) — https://fatbobman.com/en/weekly/issue-088/
