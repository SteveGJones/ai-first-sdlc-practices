# Android Application Architecture — Reference (2025)

Authoritative reference for the `android-app-architect` agent. Scope is the **non-UI structure** of an Android app: layering, lifecycle/process-death survival, DI, persistence/data layer, background work, navigation/modularization, state/event modeling, testing, and anti-patterns. **Out of scope** (separate agents): Jetpack Compose UI toolkit, Gradle build system, Kotlin-the-language.

Sources are Google official (developer.android.com) unless labeled otherwise. Version-sensitive facts are flagged **[VERSION]**. Version numbers are current as of mid-2025 and drift quickly — treat them as "recent stable," not eternal truth.

---

## 1. The Recommended Architecture

Google's official guidance ("Guide to app architecture") defines a **layered architecture** with two mandatory layers and one optional layer.

### Layers

- **UI layer** — displays application data. Composed of UI elements (Compose or Views) plus **state holders** (typically `ViewModel`) that hold data, expose it, and handle UI-level logic.
- **Domain layer (optional)** — encapsulates complex or reusable business logic as **use cases / interactors**. Add only when it earns its place.
- **Data layer** — holds business logic and exposes application data via **repositories** backed by **data sources**.

Dependency direction is strictly one-way: **UI → domain → data** (UI never reaches past domain when domain is present; domain never depends on UI). The data layer knows nothing of the layers above it.

### Core principles (Google's own list)

1. **Separation of concerns** — "the most important principle." Split into classes/modules/layers with clearly defined responsibilities. **Do not store data in app components** (Activity, Service, BroadcastReceiver) — they are ephemeral and OS-controlled.
2. **Drive the UI from data models** — preferably persistent ones, so data survives OS-initiated destruction and works offline.
3. **Single source of truth (SSOT)** — each data type has one owner; **only the SSOT can mutate it**; it exposes data as **immutable** types and offers functions to modify. Centralizes changes, prevents tampering, aids debugging.
4. **Unidirectional data flow (UDF)** — **state flows down** (data → UI), **events flow up** (user actions → SSOT). More consistent, less error-prone, easier to debug/test.

Supporting rules Google states: reduce dependencies on Android framework classes (`Context`, `Toast`, etc.); define clear module boundaries; expose as little as possible per module; types own their concurrency policy and must be **main-safe** (safe to call from the main thread without blocking); persist as much fresh data as possible for offline use.

### Repository pattern

Repositories are the data layer's public API. Responsibilities: expose data, centralize changes, resolve conflicts between multiple data sources, abstract the data sources from callers, and contain business logic. Naming: `{Type}Repository` (e.g. `NewsRepository`); data sources `{Type}{Remote|Local}DataSource`. Repositories take their data sources as **constructor dependencies** (DI).

### ViewModel as state holder + StateFlow exposure

`ViewModel` is the recommended screen-level state holder with access to the data layer, and it **survives configuration changes automatically**. Canonical exposure pattern:

```kotlin
data class DiceUiState(val firstDieValue: Int? = null, val numberOfRolls: Int = 0)

class DiceRollViewModel : ViewModel() {
    private val _uiState = MutableStateFlow(DiceUiState())
    val uiState: StateFlow<DiceUiState> = _uiState.asStateFlow()   // immutable, read-only outward

    fun rollDice() = _uiState.update { it.copy(numberOfRolls = it.numberOfRolls + 1) }
}
```

Prefer a **single `UiState` object** for related state (fewer inconsistencies) over many separate streams. Derive async state with `stateIn` + `SharingStarted.WhileSubscribed(5_000)` — the 5-second stop timeout keeps the upstream alive across config changes/short backgrounding without leaking work.

**Jetpack libraries referenced by the guide:** ViewModel, Lifecycle, Navigation, Hilt (DI), Room, DataStore, WorkManager, Paging, plus Kotlin `StateFlow`/`Flow`.

---

## 2. Lifecycle & Process Death

**The golden rule:** *never rely on the app staying in memory.* Android can destroy activities on configuration change and can kill the whole process under memory pressure at any time. State survival is a layered responsibility.

### Survival matrix (Google's "Save UI states" table)

| Mechanism | Storage | Config change | Process death | User dismissal (swipe/force-stop) | Data limits | Speed |
|---|---|---|---|---|---|---|
| **ViewModel** | In-memory | Survives | **Lost** | Lost | Complex objects OK | Fast |
| **Saved state** (`SavedStateHandle` / `rememberSaveable` / `onSaveInstanceState`) | In-memory Bundle, persisted by system | Survives | **Survives** | Lost | Primitives / small Parcelables only | Slow (serialization on main thread) |
| **Persistent storage** (Room / DataStore / files) | Disk / network | Survives | Survives | Survives | Large / unlimited | Slow (disk/IO) |

**Divide and conquer** (recommended): ViewModel holds the working screen state; `SavedStateHandle`/`rememberSaveable` holds the *minimum* to reconstruct it (IDs, query text, scroll position); Room/DataStore holds the real application data. On process-death restart, the saved ID/query re-triggers the ViewModel to reload from persistent storage.

### The APIs

- **`ViewModel`** — survives configuration changes. Scoped to a `ViewModelStoreOwner` (Activity, Fragment, Navigation destination, or a composable via `viewModel()`). Lives until the owner is *permanently* destroyed; `onCleared()` runs then. **Never** hold a reference to `Context`/`Activity`/`View`/`Resources` — leaks the Activity across a rotation.
- **`SavedStateHandle`** — survives **system-initiated process death**. Key-value map backed by a `Bundle`, so it inherits Bundle size limits: keep it small and lightweight. APIs: `get`/`set`/`contains`/`remove`/`keys`, and observable `getStateFlow(key, default)` / `getMutableStateFlow`. Auto-injected into ViewModels by the default factory (and by Hilt). Also the idiomatic way to read navigation arguments. **[VERSION]** Saved state is written only when the Activity moves to *stopped* — writing mid-lifecycle defers the save to the next stop.
- **`rememberSaveable`** — Compose equivalent of saved instance state for **UI logic** state; use `SavedStateHandle` for **business logic** state in the ViewModel.
- **`onSaveInstanceState(Bundle)`** — the classic View-system callback; same Bundle constraints. Largely superseded by SavedStateHandle/rememberSaveable in modern apps.

### Lifecycle-aware collection

Never observe a flow while the UI is not visible.

- **`repeatOnLifecycle(Lifecycle.State.STARTED) { ... }`** — the correct pattern for collecting flows in Activities/Fragments; the block restarts on STARTED and cancels on STOPPED.
- **`collectAsStateWithLifecycle()`** — the Compose equivalent (from `androidx.lifecycle:lifecycle-runtime-compose`); collects only between STARTED and STOPPED. Prefer it over plain `collectAsState()`, which keeps collecting in the background.
- `flowWithLifecycle(lifecycle)` — operator form for one-off flows.

Dependencies **[VERSION]**: `androidx.lifecycle:lifecycle-runtime-ktx`, `lifecycle-viewmodel-ktx`, `lifecycle-runtime-compose`, `lifecycle-viewmodel-compose` (lifecycle ~2.8.x).

---

## 3. Dependency Injection — Hilt

**Hilt** is Google's officially recommended DI library for Android, built on **Dagger** (compile-time DI, dependency-tree walking, compile-time verification). Manual DI and Koin are viable **non-Google** alternatives (see below).

### Setup **[VERSION]**

Hilt ~**2.57.x**; requires the Hilt Gradle plugin `com.google.dagger.hilt.android`, `com.google.dagger:hilt-android`, and the compiler via **KSP** (`ksp("com.google.dagger:hilt-android-compiler:…")`). Java 17 toolchain.

### Core annotations

- **`@HiltAndroidApp`** on the `Application` — triggers code generation and creates the app-level container. Required, once.
- **`@AndroidEntryPoint`** on Activity / Fragment / Service / BroadcastReceiver / View — enables field injection into framework classes.
- **`@Inject constructor(...)`** — constructor injection; Hilt knows how to build the type.
- **`@Module` + `@InstallIn(component)`** — tells Hilt how to provide types it can't construct.
  - **`@Provides`** — for types you build yourself or that come from external libraries (Retrofit, OkHttp, Room).
  - **`@Binds`** (abstract) — to bind an interface to its implementation with no extra code.
- **`@HiltViewModel`** on a `ViewModel` with `@Inject constructor` — lets Hilt supply ViewModel dependencies; retrieve with `hiltViewModel()` (Compose) / `by viewModels()`.
- **Qualifiers** (`@Qualifier` custom annotations) — disambiguate multiple bindings of the same type (e.g. two differently-configured `OkHttpClient`s).
- **`@EntryPoint` / `EntryPointAccessors`** — access the graph from classes Hilt doesn't support (e.g. `ContentProvider`).

### Components & scopes

| Component | Injects into | Scope annotation | Lifetime |
|---|---|---|---|
| `SingletonComponent` | Application | `@Singleton` | App onCreate → app death |
| `ActivityRetainedComponent` | (n/a) | `@ActivityRetainedScoped` | First Activity onCreate → last destroy; **survives config changes** |
| `ViewModelComponent` | ViewModel | `@ViewModelScoped` | ViewModel created → cleared |
| `ActivityComponent` | Activity | `@ActivityScoped` | Activity onCreate → onDestroy |
| `FragmentComponent` | Fragment | `@FragmentScoped` | Fragment onAttach → onDestroy |
| `ServiceComponent` | Service | `@ServiceScoped` | Service onCreate → onDestroy |

Child components see parent bindings. Default bindings: `Application` everywhere; `Activity` in `ActivityComponent`; qualifiers `@ApplicationContext` / `@ActivityContext` for `Context`.

### Non-Google alternatives (label clearly)

- **Manual DI / service locator** — Google documents it; fine for small apps, but you lose compile-time verification and scoping boilerplate grows.
- **Koin** — third-party Kotlin DSL, **runtime** service locator (resolution errors surface at runtime, not compile time). Not a Google product; do not present as the default.
- **Dagger (plain)** — Hilt's foundation; use directly only when Hilt's opinionated components don't fit.

---

## 4. Persistence & Data Layer

### Room (relational, SSOT for structured data) **[VERSION]** ~2.8.x

SQLite abstraction with compile-time SQL verification.

- **`@Entity`** → table (`@PrimaryKey`, `@ColumnInfo`, `@Relation` for 1:1/1:N/N:M, `@TypeConverters` for complex types).
- **`@Dao`** → `@Query`, `@Insert`, `@Update`, `@Delete`.
- **`@Database(entities=[...], version=N)`** extends `RoomDatabase`; built via `Room.databaseBuilder(...)`.
- **Observable queries**: return `Flow<List<T>>` — emits on every underlying change (reactive SSOT). **Suspend** functions for one-shot reads/writes (main-safe; Room moves work off the main thread).
- **Migrations**: `Migration(from, to)` with `execSQL`, or **auto-migrations** (`@AutoMigration`, Room 2.4+). Ship a migration for every schema version bump.
- **KSP vs kapt**: use **KSP** (`ksp(...)`, faster) for Kotlin; kapt is legacy. Extensions: `room-ktx` (coroutines/Flow), `room-paging` (Paging 3), `room-testing` (in-memory DB for tests).

### DataStore (replaces SharedPreferences) **[VERSION]** ~1.1.x

Async, Flow-based, transactional key-value / typed storage on `Dispatchers.IO`. Why it replaces `SharedPreferences`: SharedPreferences exposes a synchronous, main-thread-blocking API, can't signal errors, and lacks transactional consistency. DataStore fixes all three.

- **Preferences DataStore** (`datastore-preferences`) — untyped key-value, SharedPreferences-like, no schema.
- **Proto DataStore** (`datastore`) — typed objects via protocol buffers, schema + type safety.
- Read via `dataStore.data: Flow<T>`; write via `suspend edit { ... }` / `updateData { ... }` (whole block is one transaction). **One instance per file per process.**

### Paging 3 **[VERSION]** ~3.3.x

Loads large datasets page-by-page. `PagingSource` (single source — network *or* DB), `RemoteMediator` (layered network + local DB cache), `Pager` produces a `Flow<PagingData<T>>`. Do **not** fold `PagingData` into your immutable `UiState` — it mutates over time; expose it as its own stream and collect with `collectAsLazyPagingItems()`.

### Network (common libraries — **not** Google/Jetpack)

**Retrofit** + **OkHttp** (Square) are the de-facto REST stack; **Ktor client** (JetBrains) is the Kotlin-multiplatform alternative; **kotlinx.serialization** / Moshi for JSON. Wrap them behind a `RemoteDataSource`. Both Retrofit and Ktor offer `suspend` endpoints that are main-safe.

### Offline-first & single source of truth

- The **local data source (Room/DataStore) is the canonical SSOT**. Higher layers **read only from local**; expose reads as `Flow`, writes as `suspend`.
- Convert per-layer models: `NetworkX.asEntity()` → `EntityX.asExternalModel()` — never leak network/DB models to the UI.
- **Write strategies**: online-only (must be real-time, e.g. payments), queued (non-time-sensitive, via WorkManager), lazy (critical local-first data written locally then synced).
- **Synchronization**: pull-based (fetch on demand) or push-based (`synchronize()` fetches baseline, server notifies of staleness). Conflict resolution commonly **"last write wins"** using timestamp metadata.
- In-memory caching in a repository must be thread-safe (`Mutex().withLock { }`).

---

## 5. Background Work

Choose by *guarantee* and *lifetime*, not convenience.

### WorkManager — deferrable, guaranteed work **[VERSION]** ~2.9.x (`androidx.work:work-runtime-ktx`)

For persistent work that **must run** even across app exit and device reboot (sync, upload, periodic backend push). Backed by an internal SQLite DB; reschedules after reboot; respects Doze/battery.

- Requests: **`OneTimeWorkRequest`** and **`PeriodicWorkRequest`** (min interval 15 min). Workers: **`CoroutineWorker`** (`suspend doWork()` returning `Result.success/failure/retry`) is the Kotlin recommendation; also `Worker`, `RxWorker`, `ListenableWorker`.
- **`Constraints`** — network type, charging, device idle, battery/storage not low.
- **Chaining** — `beginWith(a).then(b).then(c).enqueue()`; parallel via a list; output `Data` flows between steps. Unique work via `enqueueUniqueWork` / `beginUniqueWork` with `ExistingWorkPolicy`.
- **Expedited work** — `setExpedited(OutOfQuotaPolicy.RUN_AS_NON_EXPEDITED)` for important-but-quick tasks; runs as a foreground service where needed.
- **Long-running** — call `setForeground(getForegroundInfo())` to promote to a foreground service.
- **Backoff** — `BackoffPolicy` (exponential/linear) for `Result.retry()`.
- **Don't** use WorkManager for in-process work that can safely die with the app (use coroutines), for exact-time alarms (use `AlarmManager`), or for immediate UI-bound async (coroutines).

### Foreground services (user-visible ongoing work)

**[VERSION] Android 14 (API 34)** requires, for every foreground service: the base `FOREGROUND_SERVICE` permission, a declared **`android:foregroundServiceType`** in the manifest, the matching **type-specific permission** (e.g. `FOREGROUND_SERVICE_LOCATION`), and passing the type constant to `startForeground(id, notification, ServiceInfo.FOREGROUND_SERVICE_TYPE_*)`. Runtime permissions apply per type (camera→`CAMERA`, microphone→`RECORD_AUDIO`, location→`ACCESS_FINE/COARSE_LOCATION`).

Types include: `camera`, `microphone`, `location`, `connectedDevice`, `dataSync`, `mediaPlayback`, `mediaProcessing`, `mediaProjection`, `health`, `phoneCall`, `remoteMessaging`, `shortService` (~3 min, must implement `onTimeout()`), `specialUse` (needs a manifest `<property>` justification), `systemExempted`.

**[VERSION] Android 15 (API 35):** apps targeting 15 **cannot** start `dataSync`, `mediaPlayback`, `mediaProjection`, or `phoneCall` foreground services from a `BOOT_COMPLETED` receiver; `dataSync` has a rolling time cap; `mediaProcessing` is capped ~6h/24h. Google Play also requires declaring FGS types in the Play Console.

### Coroutines & lifecycle-aware scopes

- **`viewModelScope`** — cancelled automatically when the ViewModel is cleared. Default home for ViewModel async work.
- **`lifecycleScope`** — tied to a `Lifecycle` (Activity/Fragment); pair with `repeatOnLifecycle` for flow collection.
- **`Dispatchers`** — `Main` (UI), `IO` (blocking disk/network), `Default` (CPU-bound). Push blocking work off the main thread with `withContext(ioDispatcher)`; inject the dispatcher for testability.
- **Structured concurrency** — child coroutines cancel with their scope; never orphan work. See §9 for `GlobalScope` misuse.

---

## 6. Navigation & Modularization

### Navigation architecture

Use the Jetpack **Navigation component** (Navigation-Compose, or the newer **Navigation 3** for Compose). **Navigation is UI logic** — handle it in the UI layer, not by exposing navigation "commands" from the ViewModel. When navigation depends on business logic, expose the *decision* as UI state and let the UI react (e.g. observe `uiState.isLoggedIn` in a `LaunchedEffect`, then navigate; reset a guard flag to avoid re-navigation). Pass **primitive IDs** between destinations, not whole objects; the destination's ViewModel reloads from a repository using the ID (often via `SavedStateHandle`).

### Multi-module strategy

Google's modularization guidance: organize into **loosely coupled, self-contained** modules — **high cohesion, low coupling**.

**Module types:**
- **App module** — entry point; depends on feature modules; owns root navigation. One per form factor (phone / Wear / TV / Auto).
- **Feature modules** (`:feature:*`) — a screen or user flow with its UI + ViewModel. **Depend on data/core modules only, never on other feature modules** (avoids cycles; the app module mediates).
- **Data modules** (`:data:*`) — repositories, data sources, models; expose *only* the repository, hide the rest with `internal`/`private`.
- **Core / common modules** (`:core:*`) — shared infra: `:core:ui`, `:core:network`, `:core:database`, `:core:common`, `:core:testing`, etc.
- **Test modules** — shared test code/fakes.

**Benefits:** faster incremental/parallel/cached builds, reuse, strict visibility control, clear ownership, encapsulation, isolated testability, and support for Play Feature Delivery.

**api vs impl split** (a key scaling pattern): give a feature two submodules — an **`:api`** module with the public interface/navigation keys and an **`:impl`** module with the concrete implementation. Consumers depend on `:api`; the app wires `:impl` in (often as a `runtimeOnly`/variant-specific dependency). This enables **dependency inversion** — swap implementations by build variant (e.g. `debugImplementation(:database:impl:room)`, `androidTestImplementation(:database:impl:mock)`) — and cuts rebuilds because changing an impl doesn't recompile its consumers.

**Gradle guidance:** prefer **`implementation`** over **`api`** (don't leak transitive deps; faster builds); use **version catalogs** and **convention plugins** to share build logic; prefer pure Kotlin/Java library modules over Android library modules when no Android resources are needed. **Pitfalls:** too fine-grained (build/boilerplate overhead) or too coarse (monolith); don't modularize a tiny app that won't grow. The **Now in Android** sample (`android/nowinandroid`) is Google's reference for this layout.

### Dynamic feature modules (brief)

`com.android.dynamic-feature` modules delivered on demand via **Play Feature Delivery** (install-time / conditional / on-demand). Keeps the base APK small for rarely-used large features. Adds complexity (SplitInstallManager, `@Nullable` module access) — use only when download size genuinely matters.

---

## 7. State & Events

### Modeling UI state

- Immutable **`data class {Screen}UiState`** with sensible defaults; name it `[Functionality]UiState`.
- Prefer a **single state object** per screen for related fields (loading, content, error, empty all in one).
- Model mutually-exclusive states with a **sealed interface/class** for the Loading-Content-Error (LCE) pattern:

```kotlin
sealed interface NewsUiState {
    data object Loading : NewsUiState
    data class Success(val news: List<Article>) : NewsUiState
    data object Error : NewsUiState
}
```

- **Empty/loading/error** are first-class states, not afterthoughts: booleans like `isLoading`, an `errorMessages: List<Message>`, or an explicit sealed variant. Transient messages (snackbars) live in state as a `userMessage`, and the UI calls back (`userMessageShown()`) to clear them once consumed.

### One-off events — Google's current guidance

**ViewModel events should always result in a UI state update.** Google explicitly labels exposing ViewModel events via **Kotlin `Channel`** or **`SharedFlow`** an **antipattern** for state-bearing events: when the producer (ViewModel) outlives the consumer (Compose UI), delivery/processing is **not guaranteed**, which can drop events and leave the app inconsistent. Modeling events as state gives reproducibility across config change and process death, delivery guarantees, and easier testing.

Nuance / the debate: `SharedFlow`/`Channel` remain reasonable for **genuinely transient, fire-and-forget effects** where re-delivery would be *wrong* (a one-time toast, a "play sound," a navigation trigger you don't want replayed) **and** collection is lifecycle-aware. But the moment an "event" represents something the UI must not miss, hold it in state instead. Guideline verbatim: *"Don't think about what actions the UI needs to make; think about how those actions affect the UI state."*

---

## 8. Testing

### Test locations

- **Local unit tests** — `src/test/`, run on the JVM (host), fast, no device. Home for ViewModel / repository / use-case / mapper tests.
- **Instrumented tests** — `src/androidTest/`, run on device/emulator. UI tests (Espresso for Views, Compose test rule for Compose) and framework integration (real Room DB, etc.).
- **Robolectric** — run Android-framework-dependent tests on the JVM without a device (host-side integration).

### Google's guidance: **fakes over mocks**

Google recommends **test doubles that are real working implementations (fakes)** over mocking frameworks. A `FakeUserRepository` implementing the same interface is more realistic and less brittle than a mock with stubbed method-by-method behavior; it survives refactors that mocks break on. Make dependencies replaceable via **interfaces + constructor injection** (DI even without a framework).

### Testing the pieces

- **ViewModels** — construct directly with fake repositories/use-cases; inject a `TestDispatcher`/`TestScope` (via a passed `CoroutineDispatcher`) to control time; assert on emitted `UiState`.
- **Flow testing** — **`Turbine`** (CashApp, **third-party**) is the standard for asserting Flow emissions (`flow.test { assertEquals(x, awaitItem()) }`); pairs with `kotlinx-coroutines-test` (`runTest`, `StandardTestDispatcher`).
- **`SavedStateHandle`** — construct with a seeded map: `SavedStateHandle(mapOf("id" to testId))`.
- **Repositories / data layer** — inject fake data sources; use **Room in-memory DB** (`Room.inMemoryDatabaseBuilder`) and **MockWebServer / WireMock** (third-party) for HTTP.

### Hilt testing **[VERSION]** `com.google.dagger:hilt-android-testing`

- **`@HiltAndroidTest`** on the test class; **`HiltAndroidRule(this)`** ordered first (`@get:Rule(order = 0)`); call `hiltRule.inject()` in `@Before` for field injection.
- **`@TestInstallIn(replaces = [ProdModule::class])`** — swap a module across a whole source set (preferred). **`@UninstallModules` + `@BindValue`** — replace bindings in a single test (build-time cost; can't touch `@TestInstallIn` modules).
- **`HiltTestApplication`** via a custom `AndroidJUnitRunner` (instrumented) or `robolectric.properties` (Robolectric); `@CustomTestApplication` when a custom base Application is required.

**Test pyramid:** many small/fast unit tests, fewer medium integration tests, few large end-to-end tests.

---

## 9. Anti-Patterns (what the agent should flag)

1. **God ViewModel / God Activity** — one class owning many unrelated screens' logic. Fix: split by screen; extract a domain layer; keep ViewModels close to a single screen/destination.
2. **Leaking `Context`** — storing `Activity`/`View`/`Context`/`Resources` in a ViewModel (or any object outliving the Activity) leaks it across rotation. Use `@ApplicationContext`, or move Context-dependent work to the data layer.
3. **Business logic in the UI** — parsing, validation, network decisions inside composables/Activities/Fragments. Fix: push to ViewModel → domain → data; the UI only renders state and forwards events.
4. **Ignoring process death** — assuming the process (and in-memory ViewModel) survives. Fix: back critical minimal state with `SavedStateHandle`/`rememberSaveable`, real data with Room/DataStore.
5. **Blocking the main thread** — synchronous disk/network/CPU work on `Dispatchers.Main` (jank/ANR). Fix: main-safe APIs + `withContext(Dispatchers.IO/Default)`; keep ViewModel work main-safe and let lower layers switch threads.
6. **Misusing `GlobalScope`** — launching work in `GlobalScope` (unbounded lifetime, not cancelled, breaks structured concurrency, leaks). Fix: `viewModelScope` / `lifecycleScope`, or an injected application-scoped `CoroutineScope` for work that must outlive a screen.
7. **Events as unguaranteed streams** — exposing must-not-miss ViewModel events via `Channel`/`SharedFlow` (Google antipattern). Fix: model as UI state (§7).
8. **Mutable state escaping the SSOT** — exposing `MutableStateFlow`/mutable collections outward, or mutating data outside its owner. Fix: expose `StateFlow`/immutable types; mutate only inside the owner.
9. **Feature-to-feature module dependencies** — creates cycles and coupling. Fix: depend on shared `:data`/`:core`; mediate through the app module; use api/impl split.
10. **Storing data in app components** — using Activity/Service fields as the source of truth. Fix: repositories + persistent storage.

---

## Sources

Google official — developer.android.com:
- Guide to app architecture — https://developer.android.com/topic/architecture
- UI layer — https://developer.android.com/topic/architecture/ui-layer
- UI events — https://developer.android.com/topic/architecture/ui-layer/events
- Domain layer — https://developer.android.com/topic/architecture/domain-layer
- Data layer — https://developer.android.com/topic/architecture/data-layer
- Offline-first — https://developer.android.com/topic/architecture/data-layer/offline-first
- ViewModel — https://developer.android.com/topic/libraries/architecture/viewmodel
- Saved state / SavedStateHandle — https://developer.android.com/topic/libraries/architecture/viewmodel/viewmodel-savedstate
- Saving UI states — https://developer.android.com/topic/libraries/architecture/saving-states
- Coroutines & lifecycle-aware components — https://developer.android.com/topic/libraries/architecture/coroutines
- Hilt (DI) — https://developer.android.com/training/dependency-injection/hilt-android
- Hilt testing — https://developer.android.com/training/dependency-injection/hilt-testing
- Room — https://developer.android.com/training/data-storage/room
- DataStore — https://developer.android.com/topic/libraries/architecture/datastore
- Paging 3 overview — https://developer.android.com/topic/libraries/architecture/paging/v3-overview
- WorkManager — https://developer.android.com/topic/libraries/architecture/workmanager
- Foreground service types — https://developer.android.com/develop/background-work/services/fgs/service-types
- Modularization overview — https://developer.android.com/topic/modularization
- Modularization patterns — https://developer.android.com/topic/modularization/patterns
- Testing fundamentals — https://developer.android.com/training/testing/fundamentals
- Now in Android sample — https://github.com/android/nowinandroid

Third-party / community (labeled as such; used only for the api/impl pattern and ecosystem context):
- droidcon — Multi-module feature architecture (2024) — https://www.droidcon.com/2024/08/30/approaches-for-multi-module-feature-architecture-on-android/
- ASOS Tech Blog — API/Implementation modularisation pattern — https://medium.com/asos-techblog/slaying-the-monolith-api-implementation-modularisation-pattern-in-android-development-22a07c24e9dd
- Turbine (CashApp) — https://github.com/cashapp/turbine

Non-Google libraries referenced: Retrofit/OkHttp & Turbine (Square/CashApp), Ktor & kotlinx.serialization (JetBrains), Koin (community DI), MockWebServer/WireMock — all flagged inline as non-Google.
