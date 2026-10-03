# Jetpack Compose UI Architecture — Reference (Android, 2025–2026)

Authoritative reference material for the `jetpack-compose-architect` agent. Focus: the
**Compose UI toolkit, its state model, and performance model**. Explicitly out of scope
(owned by other agents): Material Design 3 tokens/components; general app architecture
(Hilt/Room/data layer). All facts sourced from official Google docs (developer.android.com
and the Android Developers blog). **Version-sensitive facts are flagged** — Compose evolves
fast and the toolkit is shipped via the Compose BOM plus a standalone Compose Compiler
Gradle plugin that (since Kotlin 2.0) versions in lockstep with Kotlin.

> Verification date: 2026-07. Treat any version claim as a snapshot; confirm against the
> BOM/AndroidX release notes for the consumer's toolchain.

---

## 0. Mental model & versioning context

- Compose is **declarative**: the only way to change what is displayed is to call
  composable functions with new arguments (new state). You never mutate the view tree.
- Three top-level terms: **Composition** (the description of the UI built by running
  composables), **initial composition** (first run), **recomposition** (re-running
  composables when the state they read changes).
- **Toolchain, version-sensitive:**
  - Since **Kotlin 2.0**, the Compose Compiler moved into the Kotlin repository and is
    applied via the **Compose Compiler Gradle plugin** (`org.jetbrains.kotlin.plugin.compose`),
    versioned to match your Kotlin version. Before Kotlin 2.0 it was a separate
    `androidx.compose.compiler` artifact with its own compat table.
  - Runtime/UI/foundation/material libraries are pulled via the **Compose BOM**
    (`androidx.compose:compose-bom`); do not hard-pin individual Compose artifacts.

---

## 1. Composition & recomposition (stability, skippability, strong skipping)

### How composition works
- Composables emit UI by running; the runtime records which composables read which state.
- **Recomposition** re-runs *only* the composables that read changed state (and their
  restart scope), not the whole tree — provided those composables are **skippable**.

### Compiler-inferred function tags
- **Restartable** — the composable is a "scope" the runtime can re-enter to re-execute on
  a state change. Most `@Composable fun` returning `Unit` are restartable. Inline
  composables and those returning a value are typically **not** restartable.
- **Skippable** — during recomposition the runtime may skip this composable entirely *if
  all its arguments compare equal to their previous values*.

### Stability — the core concept
A parameter type is either **stable** or **unstable**; skippability depends on it.

- **Immutable** (`@Immutable`): properties can *never* change after construction and all
  methods are referentially transparent. Primitives, `String`, and function types qualify.
- **Stable** (`@Stable`): properties *may* change but the Compose runtime is **notified of
  every change** (i.e., changes flow only through `State`/snapshot objects). Compose's own
  stable mutable types: `MutableState`, `SnapshotStateList`, `SnapshotStateMap`.
- **Unstable**: anything the compiler can't prove stable — notably a `data class` with a
  `var` backed by plain (non-snapshot) storage, and **`List`/`Set`/`Map` are ALWAYS
  unstable** (the interface can't guarantee the concrete impl is immutable).

**Rules the compiler applies:**
- A `data class` is stable iff *all* its properties are stable.
- **Classes from modules NOT compiled with the Compose compiler plugin are always treated
  as unstable** (e.g., DTOs from a pure-Kotlin/Java library). This is a top source of
  "why won't this skip?" surprises.

**Fixes for instability:**
- Annotate the type `@Immutable` or `@Stable` (you are promising the contract; violating
  it causes undefined behavior / stale UI).
- Use **kotlinx.collections.immutable** (`ImmutableList`, `persistentListOf(...)`) instead
  of `List`.
- Wrap external types in an `@Immutable` UI model (`ContactUiModel`) and map into it.
- Provide a **stability configuration file** (compiler option) listing classes to treat as
  stable without touching their source — useful for third-party types you can't annotate.

### `@Stable` vs `@Immutable` — which to use
- Use `@Immutable` when the instance genuinely never mutates after construction.
- Use `@Stable` when it can mutate but only through observable (`State`) channels, so
  Compose is always notified.

### Skippability decision table
| Parameter state | Behavior on recomposition |
|---|---|
| Stable, unchanged | **Skipped** |
| Stable, changed | Recomposed |
| Unstable (without strong skipping) | **Always recomposed** |

### Strong skipping mode — **version-sensitive, default in Kotlin 2.0+**
- **Available** since Compose compiler **1.5.4** (opt-in). **Enabled by default from
  Kotlin 2.0.20** onward. Manual enable for older setups via the Compose Compiler Gradle
  plugin: `composeCompiler { enableStrongSkippingMode = true }` (older Gradle DSL:
  `enableStrongSkippingMode = true`).
- **Effect:** *all restartable composables become skippable, even those with unstable
  parameters.* (Non-restartable composables still can't be skipped.)
- **Equality semantics used to decide skipping:**
  - **Unstable** parameters → compared by **instance equality (`===`)**.
  - **Stable** parameters → compared by **structural equality (`.equals()`)**.
- **Automatic lambda memoization:** every lambda inside a composable is auto-wrapped in
  `remember(captures...)`. Keys follow the same equality rules (instance for unstable
  captures, structural for stable). This is why strong skipping stops lambda reallocations
  from breaking a parent's skip. (Lambdas are always treated as *stable* by the compiler;
  the pre-strong-skipping problem was reallocation, not instability.)
- **Opt-outs:** `@NonSkippableComposable` (force a restartable composable to always run),
  `@DontMemoize` on a lambda (skip auto-memoization).
- **Cost:** negligible — the Now in Android sample saw ~**20% faster home-screen
  recomposition** and only **~4 kB** APK growth.
- **Gotcha with Room/network objects:** sources that allocate a fresh object with equal
  values on each emission will *not* be skipped under instance equality — annotate the
  type `@Stable` so structural equality is used.

### `remember`, `rememberSaveable`, keys
- `remember { }` stores a value in the Composition across recompositions; forgotten when
  the composable leaves the Composition. Use for expensive-to-create objects.
- **Keyed remember:** `remember(key1, key2) { }` re-runs the calc lambda when a key
  changes — the correct way to invalidate cached state on input change.
- `rememberSaveable { }` additionally survives **configuration changes and process death**
  (backed by `SavedStateHandle`/`Bundle`). Does NOT survive the user dismissing the task.
  Custom types need `@Parcelize` (Parcelable), or a `Saver` (`mapSaver`/`listSaver`);
  `rememberSaveable(input, stateSaver = ...)` supports invalidation via `inputs`.

---

## 2. State & state hoisting (UDF)

### State primitives
- `mutableStateOf(x)` → `MutableState<T>` (observable; writes to `.value` schedule
  recomposition of readers). Specialized primitives avoid autoboxing:
  `mutableIntStateOf`, `mutableLongStateOf`, `mutableFloatStateOf`, `mutableDoubleStateOf`.
- Three read/write idioms:
  ```kotlin
  val s = remember { mutableStateOf(default) }        // s.value
  var v by remember { mutableStateOf(default) }       // property delegate
  val (v, setV) = remember { mutableStateOf(default) } // destructured
  ```
- Observable collections: `mutableStateListOf()` / `mutableStateMapOf()` (snapshot-backed,
  trigger recomposition on mutation) — unlike a plain `mutableListOf()` held in state,
  which does **not** trigger recomposition.
- `State<T>` is the **read-only** interface Compose observes. Convert external streams:
  - `Flow` → `collectAsStateWithLifecycle()` (**preferred**; lifecycle-aware, collects
    between STARTED and STOPPED — from `androidx.lifecycle:lifecycle-runtime-compose`).
  - `Flow` → `collectAsState()` (not lifecycle-aware; avoid on Android UIs).
  - `LiveData` → `observeAsState()`; RxJava → `subscribeAsState()`.

### State hoisting & unidirectional data flow (UDF)
- **State flows down, events flow up.** Hoist state to the caller and expose
  `value: T` + `onValueChange: (T) -> Unit`. This yields a **stateless** composable.
- **Stateful** composable = owns its own `remember`ed state (convenient, less reusable/
  testable). **Stateless** = all state passed in (reusable, testable, state can live
  anywhere including a ViewModel).
- **Where to hoist:** to at least the **lowest common ancestor** that reads it, and at
  least the **highest level it is written**; hoist together states that change together.
- Benefits: single source of truth, encapsulation, shareability, interceptability,
  decoupling.

### `derivedStateOf` — reduce recomposition frequency
- `derivedStateOf { }` produces a `State` that only changes when the *computed result*
  changes, even if inputs change more often (like `distinctUntilChanged`). Wrap in
  `remember`.
- **Correct** use: input changes far more often than the output the UI needs, e.g.
  `derivedStateOf { listState.firstVisibleItemIndex > 0 }`.
- **Anti-pattern:** deriving `"$firstName $lastName"` — recomposition happens as often as
  the inputs change anyway, so plain concatenation is cheaper.

### `snapshotFlow`
- `snapshotFlow { block }` converts Compose `State` reads into a cold `Flow`; emits when
  observed state changes and conflates equal values. Use it (inside `LaunchedEffect`) to
  run Flow operators over state (map/filter/`distinctUntilChanged`) for side effects such
  as analytics on scroll.

---

## 3. Side effects

| API | Purpose | Keys? | Lifecycle | Key pitfalls |
|---|---|---|---|---|
| `LaunchedEffect(keys) { suspend }` | Run coroutine tied to composition | Yes | Launches on enter; **cancels on leave; restarts when a key changes** | Missing a mutable var as a key → stale closure. `LaunchedEffect(Unit/true)` ties to call-site lifetime — use sparingly. |
| `rememberCoroutineScope()` | Launch coroutines from **non-composable** callbacks (onClick) | — | Scope cancelled when the call site leaves composition | Don't use for work meant to outlive the composable. |
| `rememberUpdatedState(v)` | Capture the *latest* value inside a long-lived effect **without restarting it** | — | — | Pair with `LaunchedEffect(Unit)`; forgetting it → stale value in long-lived effect. |
| `DisposableEffect(keys) { ...; onDispose { } }` | Effects needing cleanup (register/unregister listeners) | Yes | Dispose+restart on key change; dispose on leave | **`onDispose` is mandatory**; empty `onDispose` is a smell. |
| `SideEffect { }` | Publish Compose state to non-Compose code **after every successful recomposition** | No | Every successful recomposition | Runs every recomposition — keep it cheap. |
| `produceState(initial, keys) { value = ... }` | Turn non-Compose async source (Flow/LiveData/callback) into `State<T>` | Yes | Coroutine scoped to composition; `awaitDispose {}` for callback cleanup | Name the composable lowercase (returns a value). |

**Restart decision tree:** any mutable/immutable value used inside an effect block should
be a **key**; if it must not restart the effect, wrap it in `rememberUpdatedState`; values
`remember`ed with no keys need not be keys.

---

## 4. Layout & modifiers

### Modifier system & order
- Modifiers are an **ordered, immutable chain**; **order is significant**. `padding`
  before `background` vs after produces different results; `size` then `padding` shrinks
  the content box. Constraints pass **down** the chain (parent → child), sizes pass **up**.
- Compose layout is **single-pass** (each child measured once) — this is why `Layout`
  works without multiple measurement passes; **intrinsics** exist for the cases where a
  parent needs a child's preferred size before placing (`Modifier.height(IntrinsicSize.Min)`,
  `minIntrinsicWidth`, etc.).

### Custom layout
- `Layout(content) { measurables, constraints -> ... layout(w,h){ placeable.place() } }`
  for measuring/placing multiple children. The `layout` modifier
  (`Modifier.layout { measurable, constraints -> }`) customizes a *single* element.
- **`SubcomposeLayout`** defers composition of some children until measurement (so their
  content can depend on the measured size of others). Powers `BoxWithConstraints` and the
  lazy lists. **Costs more** than `Layout` — avoid when a plain `Layout` + intrinsics works.

### `Modifier.Node` — the modern custom-modifier API
Three parts:
1. **Factory** — `fun Modifier.foo(...) = this then FooElement(...)`.
2. **`ModifierNodeElement<N>`** — a **stateless `data class`** with `create()` and
   `update(node)`. Must implement `equals`/`hashCode` (use `data class`); `update()` runs
   only when `equals` is false — you mutate the existing node rather than allocate a new one.
3. **`Modifier.Node`** subclass — the **stateful** implementation; survives recomposition
   and is reused.

- **Prefer `Modifier.Node` over the deprecated `composed { }`** — far more performant
  (nodes aren't recomposed each call; factories can be hoisted out of composition).
- Node capability interfaces: `DrawModifierNode`, `LayoutModifierNode`,
  `SemanticsModifierNode`, `PointerInputModifierNode`, `ParentDataModifierNode`,
  `LayoutAwareModifierNode` (`onMeasured`/`onPlaced`), `GlobalPositionAwareModifierNode`
  (`onGloballyPositioned`), `CompositionLocalConsumerModifierNode` (`currentValueOf(...)`),
  `ObserverModifierNode` (`observeReads`/`onObservedReadsChanged`), `DelegatingNode`
  (`delegate(...)` to compose behavior), `TraversableNode`.
- Lifecycle: `onAttach()` / `onReset()` / `onDetach()`; `coroutineScope` available for
  animations. Fine-grained invalidation: `invalidateDraw()`, `invalidateMeasurement()`,
  `invalidatePlacement()`; opt out of auto-invalidation with
  `override val shouldAutoInvalidate = false`.

### Lazy lists — `LazyColumn` / `LazyRow` / grids
- Components: `LazyColumn`, `LazyRow`, `LazyVerticalGrid`, `LazyHorizontalGrid`,
  `LazyVerticalStaggeredGrid`, `LazyHorizontalStaggeredGrid`. They compose/lay out **only
  visible items** (DSL-based, unlike `RecyclerView`).
- DSL (`LazyListScope`): `item { }`, `items(count) { }`, `items(list) { }`,
  `itemsIndexed(list) { }`, `stickyHeader { }`.
- **`key = { it.id }`** — give items a **stable, unique** identity. Without it, item state
  is position-keyed and breaks on insert/reorder. Required for correct `animateItem()` and
  for `rememberSaveable` inside items. **Key type must be Bundle-storable** (primitive/
  enum/Parcelable).
- **`contentType = { it.type }`** (since Compose **1.2**) — lets the runtime reuse
  compositions only between items of the same type; improves reuse for heterogeneous lists.
- **Item animations:** `Modifier.animateItem(fadeInSpec, placementSpec, fadeOutSpec)`
  (current API; supersedes the older `animateItemPlacement()`). Requires item keys.
- State: `rememberLazyListState()` → `firstVisibleItemIndex`,
  `firstVisibleItemScrollOffset`, `layoutInfo`; `scrollToItem()` /
  `animateScrollToItem()` are suspend functions. Grids: `GridCells.Fixed(n)` /
  `GridCells.Adaptive(minSize)`, item spans via `GridItemSpan(maxLineSpan)`.
- **Pitfalls:** never nest a scrollable of the **same direction** without a bounded height
  (`LazyColumn` inside `Modifier.verticalScroll` throws) — instead use one `LazyColumn`
  with mixed `item`/`items`; avoid 0-px items (forces eager composition of everything);
  benchmark scrolling only in **release + R8** builds.

---

## 5. Navigation (Navigation-Compose & Navigation 3)

### Navigation-Compose (the current stable path)
- `NavController` (`rememberNavController()`) + `NavHost(navController, startDestination)`;
  destinations declared with `composable(...) { }`; nested graphs via `navigation(...)`.
- **Type-safe navigation — version-sensitive: Navigation 2.8.0+.** Requires the **Kotlin
  Serialization plugin**.
  - Define routes as `@Serializable` types: `@Serializable object Home`,
    `@Serializable data class Profile(val id: String)`.
  - Graph: `composable<Profile> { entry -> val p = entry.toRoute<Profile>() }`.
  - Navigate with a typed instance: `navController.navigate(Profile(id))`.
  - Retrieve args anywhere: `backStackEntry.toRoute<T>()` or, in a ViewModel,
    `savedStateHandle.toRoute<T>()`.
  - Benefits: compile-time argument typing, no string routes, no manual `NavArgument`,
    full IDE refactor support. Complex arg types use a custom `NavType`.

### Navigation 3 — **version-sensitive; ALPHA, not production-ready**
- Announced May 2025 ("Announcing Jetpack Navigation 3 for Compose"); artifact group
  `androidx.navigation3` (e.g. `navigation3-runtime`). **As of mid-2026 it is in
  `1.0.0-alphaXX`** (alpha10 seen 2026) — **API unstable, subject to change; do not adopt
  for production yet.** Flag maturity explicitly to consumers.
- Design: **you own the back stack** as ordinary Compose state (a list of `NavKey`s you
  push/remove). `NavDisplay` renders it and reacts to changes; an `entryProvider` resolves
  keys → content. Built-in adaptive/multi-pane "scene strategies". Compose-only; the
  runtime is now KMP-capable (JVM/Native/Web targets).
- Migration guidance: migrate string routes → **type-safe** routes first; Nav3 routes are
  strongly typed.

---

## 6. Architecture patterns (MVVM / MVI with Compose)

- **UDF end-to-end:** `ViewModel` exposes UI state via an observable holder — **`StateFlow`
  is the recommended choice** — and the UI collects it with **`collectAsStateWithLifecycle()`**.
  Events flow up as function calls / lambdas the ViewModel handles.
- **Model UI state as a sealed type** (MVI-friendly):
  ```kotlin
  sealed interface UiState {
      data object Loading : UiState
      data class Success(val items: List<ItemUiModel>) : UiState
      data class Error(val message: String) : UiState
  }
  ```
- **Pass minimal, specific, immutable params + event lambdas** to composables (e.g.
  `Header(title, subtitle)` not `Header(news)`) — improves reuse and skippability.
- **State holders:** for complex *UI-element* logic (not business logic), use a plain
  `@Stable` state-holder class created with `remember(...)`. Rule of thumb:
  **ViewModel** for screen/business state that must survive config changes & navigation;
  **plain state holder / `rememberSaveable` / `remember`** for UI-element state.
- **One-off events (navigation, snackbars, toasts):** these are **not** state. Google's
  guidance is to **reduce them to state where possible**; where a true one-off is needed,
  expose it so the UI consumes-and-acknowledges it (the event is removed once handled).
  A `Channel`/`SharedFlow(replay = 0)` is a common implementation, but the official
  recommendation is to prefer modeling as state and to have the ViewModel expose a
  consumed flag rather than fire-and-forget. Trigger navigation from the UI layer in
  response to state, not by holding a `NavController` in the ViewModel.

---

## 7. Performance

### The three phases
1. **Composition** — *what* to show (runs composables, builds/updates the tree).
2. **Layout** — **measure** then **place** (size + position each node).
3. **Drawing** — render into the canvas.
Compose can **skip phases**: swapping two same-size icons redraws only (skips composition
and layout).

### Deferring state reads — the central performance lever
- **A state read registers the reader for the phase in which it happens.** Read in
  composition → recomposes on change; read in layout → only relayout; read in draw → only
  redraw. So **push reads to the latest phase possible.**
- Use **lambda-based modifiers** so a frequently-changing value is read in layout/draw, not
  composition:
  - `Modifier.offset { IntOffset(x, 0) }` (lambda) reads in **layout** — avoids
    recomposition — vs `Modifier.offset(x.dp)` (value) which reads in composition.
  - `Modifier.graphicsLayer { translationX = ...; alpha = ... }` reads in **draw**; it
    does not change measured size/placement. **Prefer the lambda `graphicsLayer` for
    animations / frequently-changing visual state.**
- Pass **lambdas returning state** to children rather than the resolved value, so only the
  child that actually reads it recomposes.

### Other best practices
- **Move calculations out of composables** (they can run every frame). Precompute in the
  ViewModel or `remember`.
- Ensure composables are **skippable/stable** (see §1); use **strong skipping**.
- Use `derivedStateOf` to cut recomposition frequency; use `key` in lazy lists.
- Don't do heavy work in the composition; don't allocate in hot paths.

### Diagnostics & tooling — **compiler metrics/reports**
- **Layout Inspector** shows **recomposition counts** and skip counts per composable — the
  primary way to spot over-recomposing nodes.
- **Compose compiler reports/metrics** (off by default). Enable via the Compose Compiler
  Gradle plugin, on a **release build**:
  ```kotlin
  composeCompiler {
      reportsDestination = layout.buildDirectory.dir("compose_compiler")
      metricsDestination = layout.buildDirectory.dir("compose_compiler")
  }
  ```
  Outputs include `<module>-composables.txt` (per-composable: restartable? skippable?
  parameter stability), `<module>-classes.txt` (per-class stability), and a metrics JSON
  with aggregate counts.
- **Common jank causes:** unstable parameters preventing skips; unnecessary state reads in
  composition; backwards writes; heavy work in composables; unbounded/eager lazy items;
  benchmarking debug builds. **Always measure with R8/release.** (Baseline Profiles and
  Macrobenchmark address startup/scroll jank but sit at the app-perf layer.)

---

## 8. Testing & tooling

- **Rules:** `createComposeRule()` (isolated, **no Activity** — set UI with
  `composeTestRule.setContent { }`) vs `createAndroidComposeRule<MyActivity>()` (needs the
  Activity/context).
- **Finders** query the **semantics tree**: `onNodeWithText(...)`, `onNodeWithTag(...)`,
  `onNodeWithContentDescription(...)`; add stable identifiers with **`Modifier.testTag("x")`**.
- **Actions:** `performClick()`, `performTextInput(...)`, `performScrollTo()`,
  `performTouchInput { }`. **Assertions:** `assertIsDisplayed()`, `assertTextEquals(...)`,
  `assertExists()`, `assertIsEnabled()`.
- **Synchronization:** the harness auto-waits for the UI to be idle (recomposition/
  animations) before acting/asserting; `waitUntil { }`, `mainClock`, and
  `composeTestRule.awaitIdle()` give manual control.
- **Dependencies:** `androidTestImplementation("androidx.compose.ui:ui-test-junit4")`;
  `debugImplementation("androidx.compose.ui:ui-test-manifest")` (needed by
  `createComposeRule()`, not by `createAndroidComposeRule`).
- **Previews:** `@Preview` renders composables in the IDE (no device); parameters like
  `showBackground`, `uiMode`, `device`, `fontScale`, `widthDp`. **Multipreview**:
  define/annotate with a custom annotation (e.g. `@PreviewLightDark`, `@PreviewFontScale`,
  or your own `@Preview`-stacked annotation) to render many configurations at once.
  `@PreviewParameter` supplies sample data.

---

## 9. Interop & incremental adoption (Compose ↔ View)

- **View inside Compose:** the **`AndroidView`** composable —
  `AndroidView(factory = { ctx -> MyView(ctx) }, update = { view -> /* re-run on recompose */ },
  onReset = { }, onRelease = { })`. `AndroidViewBinding(MyLayoutBinding::inflate)` embeds an
  existing XML layout via ViewBinding.
- **Compose inside Views:** **`ComposeView`** — add it in XML or code, then
  `composeView.setContent { }`. Control composition lifetime with
  **`ViewCompositionStrategy`** (e.g. `DisposeOnViewTreeLifecycleDestroyed` — important for
  Fragments/RecyclerView to avoid leaks).
- **Adoption strategy:** Compose and Views coexist during migration — add Compose screens/
  components incrementally via `ComposeView` (including inside Fragments), embed legacy
  Views via `AndroidView`, and migrate screen-by-screen. Official migration scenarios cover
  RecyclerView → Lazy lists, CoordinatorLayout, and Navigation → Navigation-Compose.

---

## Version-sensitivity cheat sheet (confirm against consumer toolchain)

| Feature | Availability |
|---|---|
| Strong skipping mode | Compiler **1.5.4+** (opt-in); **default in Kotlin 2.0.20+** |
| Compose Compiler as Kotlin Gradle plugin | **Kotlin 2.0+** |
| Type-safe Navigation (`@Serializable` routes, `toRoute`) | **Navigation 2.8.0+** |
| Navigation 3 | **`1.0.0-alphaXX` (alpha10 seen 2026)** — not production-ready |
| `contentType` in lazy lists | Compose **1.2+** |
| `Modifier.animateItem()` | supersedes `animateItemPlacement()` |
| `collectAsStateWithLifecycle()` | `androidx.lifecycle:lifecycle-runtime-compose` |
| `Modifier.Node` custom modifiers | current API; `composed {}` deprecated |

---

## Sources (all Google/official unless noted)

- Stability in Compose — https://developer.android.com/develop/ui/compose/performance/stability
- Diagnose stability issues — https://developer.android.com/develop/ui/compose/performance/stability/diagnose
- Fix stability issues — https://developer.android.com/develop/ui/compose/performance/stability/fix
- Strong skipping mode — https://developer.android.com/develop/ui/compose/performance/stability/strongskipping
- Compose phases — https://developer.android.com/develop/ui/compose/phases
- Compose phases & performance — https://developer.android.com/develop/ui/compose/performance/phases
- Compose performance (hub) — https://developer.android.com/develop/ui/compose/performance
- Follow best practices — https://developer.android.com/develop/ui/compose/performance/bestpractices
- Compose Compiler Gradle plugin — https://developer.android.com/develop/ui/compose/compiler
- Set up dependencies & compiler — https://developer.android.com/develop/ui/compose/setup-compose-dependencies-and-compiler
- Graphics modifiers (graphicsLayer) — https://developer.android.com/develop/ui/compose/graphics/draw/modifiers
- State and Jetpack Compose — https://developer.android.com/develop/ui/compose/state
- Where to hoist state — https://developer.android.com/develop/ui/compose/state-hoisting
- Save UI state in Compose — https://developer.android.com/develop/ui/compose/state-saving
- Side-effects in Compose — https://developer.android.com/develop/ui/compose/side-effects
- Compose UI architecture — https://developer.android.com/develop/ui/compose/architecture
- Lifecycle of composables — https://developer.android.com/develop/ui/compose/lifecycle
- Compose modifiers — https://developer.android.com/develop/ui/compose/modifiers
- Constraints and modifier order — https://developer.android.com/develop/ui/compose/layouts/constraints-modifiers
- Custom layouts — https://developer.android.com/develop/ui/compose/layouts/custom
- Intrinsic measurements — https://developer.android.com/develop/ui/compose/layouts/intrinsic-measurements
- Create custom modifiers (Modifier.Node) — https://developer.android.com/develop/ui/compose/custom-modifiers
- Modifier.Node API reference — https://developer.android.com/reference/kotlin/androidx/compose/ui/Modifier.Node
- SubcomposeLayout reference — https://developer.android.com/reference/kotlin/androidx/compose/ui/layout/SubcomposeLayout
- Lists & grids (lazy) — https://developer.android.com/develop/ui/compose/lists
- Navigation with Compose — https://developer.android.com/develop/ui/compose/navigation
- Type safety in Navigation — https://developer.android.com/guide/navigation/design/type-safety
- Migrating to type-safe navigation — https://developer.android.com/guide/navigation/type-safe-destinations
- Navigation release notes — https://developer.android.com/jetpack/androidx/releases/navigation
- Navigation 3 (guide) — https://developer.android.com/guide/navigation/navigation-3
- navigation3 release notes — https://developer.android.com/jetpack/androidx/releases/navigation3
- Announcing Jetpack Navigation 3 (blog, May 2025) — https://android-developers.googleblog.com/2025/05/announcing-jetpack-navigation-3-for-compose.html
- StateFlow and SharedFlow — https://developer.android.com/kotlin/flow/stateflow-and-sharedflow
- Lifecycle-aware coroutines — https://developer.android.com/topic/libraries/architecture/coroutines
- Testing your Compose layout — https://developer.android.com/develop/ui/compose/testing
- Compose-View interoperability APIs — https://developer.android.com/develop/ui/compose/migrate/interoperability-apis
- What's new in Jetpack Compose at I/O '24 (blog, strong skipping/compiler) — https://android-developers.googleblog.com/2024/05/whats-new-in-jetpack-compose-at-io-24.html
- Compose Compiler release notes — https://developer.android.com/jetpack/androidx/releases/compose-compiler
- Practical performance codelab — https://developer.android.com/codelabs/jetpack-compose-performance
