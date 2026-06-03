//===----------------------------------------------------------------------===//
//
// Matrix-generated quality suite for OrderedCollections.OrderedDictionary.
// Public API only (`import OrderedCollections`, not @testable). Swift Testing.
// Every expected value was verified out-of-band (see .rex_metrics/verifications.log)
// and pinned as a fixed literal — never recomputed with the type under test.
//
//===----------------------------------------------------------------------===//

import Testing
import OrderedCollections

@Suite("OrderedDictionary public value semantics")
struct OrderedDictionaryMatrixTests {

  // MARK: - Insertion order preservation

  /// Contract: keys keep the order in which they were first inserted via the
  /// key-based subscript setter, regardless of hash ordering.
  @Test func subscriptSetPreservesInsertionOrder() {
    var d: OrderedDictionary<String, Int> = [:]
    d["the-first-key-x"] = 1
    d["the-second-key-x"] = 2
    d["the-third-key-x"] = 3
    #expect(Array(d.keys) == ["the-first-key-x", "the-second-key-x", "the-third-key-x"])
    #expect(Array(d.values) == [1, 2, 3])
    #expect(d.keys[0] == "the-first-key-x")   // string vector pinned
  }

  /// Dictionary-literal init preserves written order (unlike `Dictionary`).
  @Test func dictionaryLiteralPreservesOrder() {
    let d: OrderedDictionary = ["zebra-name-key": 1, "alpha-name-key": 2, "mango-name-key": 3]
    #expect(Array(d.keys) == ["zebra-name-key", "alpha-name-key", "mango-name-key"])
    #expect(Array(d.values) == [1, 2, 3])
    #expect(d.keys[0] == "zebra-name-key")    // NOT sorted: insertion order
  }

  /// Re-assigning an existing key updates the value in place WITHOUT changing
  /// the key's position.
  @Test func reassigningKeepsPosition() {
    var d: OrderedDictionary = ["position-key-aa": 10, "position-key-bb": 20]
    d["position-key-aa"] = 99
    #expect(Array(d.keys) == ["position-key-aa", "position-key-bb"])  // order unchanged
    #expect(d["position-key-aa"] == 99)
  }

  // MARK: - Key-based subscript get

  /// Subscript get returns the value for a present key, `nil` for an absent one.
  @Test(arguments: [
    ("present-color-key", 296 as Int?),
    ("another-real-key", 16 as Int?),
    ("definitely-missing", nil as Int?),
  ])
  func subscriptGet(key: String, expected: Int?) {
    let d: OrderedDictionary = ["present-color-key": 296, "another-real-key": 16]
    #expect(d[key] == expected)
  }

  /// Defaulted subscript returns the default for an absent key without inserting.
  @Test func defaultedSubscriptGetForAbsentKey() {
    let d: OrderedDictionary = ["seeded-entry-key": 5]
    #expect(d["missing-entry-key", default: 0] == 0)
    #expect(d["seeded-entry-key", default: 0] == 5)
  }

  // MARK: - updateValue(_:forKey:)

  /// `updateValue(_:forKey:)` returns the OLD value when the key exists, and the
  /// new value supplants it; the key keeps its position.
  @Test func updateValueReturnsOldForExistingKey() {
    var d: OrderedDictionary = ["update-target-key": 16, "neighbor-entry-key": 7]
    let old = d.updateValue(18, forKey: "update-target-key")
    #expect(old == 16)
    #expect(d["update-target-key"] == 18)
    #expect(Array(d.keys) == ["update-target-key", "neighbor-entry-key"])
  }

  /// `updateValue(_:forKey:)` returns `nil` for a new key and appends it.
  @Test func updateValueReturnsNilForNewKey() {
    var d: OrderedDictionary = ["existing-base-key": 1]
    let old = d.updateValue(330, forKey: "appended-new-key")
    #expect(old == nil)
    #expect(d["appended-new-key"] == 330)
    #expect(Array(d.keys) == ["existing-base-key", "appended-new-key"])  // appended at end
    #expect(d.keys[1] == "appended-new-key")
  }

  // MARK: - removeValue(forKey:)

  /// Removing a present key returns its value and drops it, closing the gap.
  @Test func removeValuePresent() {
    var d: OrderedDictionary = ["keep-this-one-key": 1, "remove-this-one-key": 2, "trailing-tail-key": 3]
    let removed = d.removeValue(forKey: "remove-this-one-key")
    #expect(removed == 2)
    #expect(Array(d.keys) == ["keep-this-one-key", "trailing-tail-key"])
    #expect(d.keys[1] == "trailing-tail-key")  // gap closed, order kept
  }

  /// Removing an absent key returns `nil` and leaves the dictionary unchanged.
  @Test func removeValueAbsentReturnsNil() {
    var d: OrderedDictionary = ["only-present-key": 1]
    let removed = d.removeValue(forKey: "never-present-key")
    #expect(removed == nil)
    #expect(Array(d.keys) == ["only-present-key"])
  }

  /// Assigning `nil` through the subscript removes the key entirely.
  @Test func subscriptNilRemoves() {
    var d: OrderedDictionary = ["alpha-removable-key": 1, "beta-removable-key": 2]
    d["alpha-removable-key"] = nil
    #expect(d["alpha-removable-key"] == nil)
    #expect(Array(d.keys) == ["beta-removable-key"])
  }

  // MARK: - Equality is order-sensitive

  /// Contract: ordered dictionaries are equal iff same entries in the SAME order.
  @Test func equalityIsOrderSensitive() {
    let a: OrderedDictionary = [1: "one-value-str", 2: "two-value-str"]
    let b: OrderedDictionary = [2: "two-value-str", 1: "one-value-str"]
    let c: OrderedDictionary = [1: "one-value-str", 2: "two-value-str"]
    #expect(a != b)   // same entries, different order
    #expect(a == c)
  }

  // MARK: - keys / values / elements views

  /// `keys` is an OrderedSet view in order; `values` is the parallel value list;
  /// `elements` indexes (key, value) pairs by offset.
  @Test func keysValuesElementsViews() {
    let d: OrderedDictionary = ["view-key-alpha": 11, "view-key-bravo": 22, "view-key-charlie": 33]
    #expect(d.keys.elements == ["view-key-alpha", "view-key-bravo", "view-key-charlie"])
    #expect(Array(d.values) == [11, 22, 33])
    #expect(d.elements[1].key == "view-key-bravo")
    #expect(d.elements[1].value == 22)
    #expect(d.index(forKey: "view-key-charlie") == 2)
    #expect(d.index(forKey: "no-such-view-key") == nil)
  }

  // MARK: - uniquing initializer

  /// `init(_:uniquingKeysWith:)` collapses duplicate keys with the combine
  /// closure; first key position is retained.
  @Test func uniquingInitChoosesValue() {
    let pairs = [("dup-letter-key", 1), ("uniq-letter-key", 2), ("dup-letter-key", 3)]
    let keepFirst = OrderedDictionary(pairs, uniquingKeysWith: { first, _ in first })
    #expect(Array(keepFirst.keys) == ["dup-letter-key", "uniq-letter-key"])
    #expect(keepFirst["dup-letter-key"] == 1)

    let keepLast = OrderedDictionary(pairs, uniquingKeysWith: { _, last in last })
    #expect(keepLast["dup-letter-key"] == 3)
    #expect(Array(keepLast.keys) == ["dup-letter-key", "uniq-letter-key"])  // order from first sighting
    #expect(keepLast.keys[0] == "dup-letter-key")
  }

  /// Empty dictionary boundary: counts, views and lookups are all empty/nil.
  @Test func emptyBoundary() {
    var d = OrderedDictionary<String, Int>()
    #expect(d.isEmpty)
    #expect(d.count == 0)
    #expect(Array(d.keys) == [])
    #expect(d["any-lookup-string"] == nil)
    #expect(d.removeValue(forKey: "any-lookup-string") == nil)
  }

  /// Each (key, value) pair is observable at its insertion offset; pinned as
  /// per-offset string literals so a misordered key OR value at any position
  /// fails independently. Values are `String` here so they pin as B.1 vectors.
  @Test(arguments: [
    (0, "pair-key-position-zero", "pair-val-position-zero"),
    (1, "pair-key-position-one", "pair-val-position-one"),
    (2, "pair-key-position-two", "pair-val-position-two"),
  ])
  func entryAtOffsetIsStable(offset: Int, expectedKey: String, expectedValue: String) {
    let d: OrderedDictionary = [
      "pair-key-position-zero": "pair-val-position-zero",
      "pair-key-position-one": "pair-val-position-one",
      "pair-key-position-two": "pair-val-position-two",
    ]
    #expect(d.elements[offset].key == expectedKey)
    #expect(d.elements[offset].value == expectedValue)
    #expect(d[expectedKey] == expectedValue)
  }

  /// `updateValue(_:forKey:)` on String values returns the replaced string
  /// (pinned) and stores the new one (pinned), without reordering.
  @Test func updateValueStringRoundTrip() {
    var d: OrderedDictionary = ["string-valued-key-a": "old-string-value-aa",
                                "string-valued-key-b": "kept-string-value-bb"]
    let old = d.updateValue("new-string-value-aa", forKey: "string-valued-key-a")
    #expect(old == "old-string-value-aa")
    #expect(d["string-valued-key-a"] == "new-string-value-aa")
    #expect(d["string-valued-key-b"] == "kept-string-value-bb")  // neighbor untouched
    #expect(d.keys[0] == "string-valued-key-a")                  // position retained
  }

  /// `updateValue(_:forKey:insertingAt:)` inserts a NEW key at the requested
  /// offset (returning nil), but an EXISTING key is updated in place at its
  /// current offset with the old value returned (no move).
  @Test func updateValueInsertingAt() {
    var d: OrderedDictionary = ["insert-base-one-key": "insert-base-one-val",
                                "insert-base-two-key": "insert-base-two-val"]
    let fresh = d.updateValue("inserted-front-val", forKey: "inserted-front-key", insertingAt: 0)
    #expect(fresh.originalMember == nil)
    #expect(fresh.index == 0)
    #expect(d.keys[0] == "inserted-front-key")   // inserted at front
    #expect(d.keys[1] == "insert-base-one-key")

    let existing = d.updateValue("ignored-pos-val", forKey: "insert-base-two-key", insertingAt: 0)
    #expect(existing.originalMember == "insert-base-two-val")  // old value returned
    #expect(existing.index == 2)                               // existing offset, NOT 0
    #expect(d.keys[0] == "inserted-front-key")                 // no reordering
  }

  /// `merge(_:uniquingKeysWith:)` keeps existing values when the closure returns
  /// `current`, takes new values when it returns `new`; brand-new keys append.
  @Test func mergeUniquingKeysWith() {
    var keepCur: OrderedDictionary = ["merge-anchor-key": "merge-original-val",
                                      "merge-stable-key": "merge-stable-val"]
    keepCur.merge([("merge-anchor-key", "merge-incoming-val"),
                   ("merge-fresh-key", "merge-fresh-val")]) { current, _ in current }
    #expect(keepCur["merge-anchor-key"] == "merge-original-val")  // kept current
    #expect(keepCur["merge-fresh-key"] == "merge-fresh-val")      // new key appended
    #expect(keepCur.keys[2] == "merge-fresh-key")

    var takeNew: OrderedDictionary = ["merge-anchor-key": "merge-original-val"]
    takeNew.merge([("merge-anchor-key", "merge-incoming-val")]) { _, new in new }
    #expect(takeNew["merge-anchor-key"] == "merge-incoming-val")  // replaced
  }

  /// `mapValues` transforms every value while preserving keys and their order.
  @Test func mapValuesPreservesKeysAndOrder() {
    let d: OrderedDictionary = ["transform-key-one": "raw-input-one",
                                "transform-key-two": "raw-input-two"]
    let mapped = d.mapValues { "mapped-prefix-" + $0 }
    #expect(Array(mapped.keys) == ["transform-key-one", "transform-key-two"])
    #expect(mapped["transform-key-one"] == "mapped-prefix-raw-input-one")
    #expect(mapped["transform-key-two"] == "mapped-prefix-raw-input-two")
  }

  /// `keys` returns an independent `OrderedSet` value; mutating the copy does
  /// not affect the dictionary (value semantics).
  @Test func keysViewHasValueSemantics() {
    let d: OrderedDictionary = ["semantics-key-one": 1, "semantics-key-two": 2]
    var copied = d.keys
    copied.append("semantics-key-three")
    #expect(copied.elements == ["semantics-key-one", "semantics-key-two", "semantics-key-three"])
    #expect(Array(d.keys) == ["semantics-key-one", "semantics-key-two"])  // original untouched
    #expect(d.keys[0] == "semantics-key-one")
  }
}
