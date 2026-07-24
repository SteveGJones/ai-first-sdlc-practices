# Android App Architecture — Research Reference

Grounds the [`android-app-architect`](../../agents/core/android-app-architect.md) agent (feature #226,
sub-epic #225). Compiled 2026-07-23 from official Android sources + the Now in Android reference.
Library version facts are flagged `[VERSION]` in the file.

| File | Covers |
|------|--------|
| [`01-android-app-architecture.md`](01-android-app-architecture.md) | Recommended UI/domain/data layering + UDF/SSOT, lifecycle & process-death survival matrix (ViewModel/SavedStateHandle), Hilt DI (components/scopes/testing), data layer (Room/DataStore/Paging, offline-first), background work (WorkManager, foreground-service types), multi-module (api/impl), UI-state & events-as-state, testing with fakes, anti-patterns |

**At a glance:** never rely on the app staying in memory (ViewModel=config change, SavedStateHandle=process death, Room/DataStore=everything); events as state (Channel/SharedFlow for must-not-miss = anti-pattern); fakes over mocks; features never depend on other features.
