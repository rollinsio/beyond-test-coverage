//===----------------------------------------------------------------------===//
//
// Matrix-generated quality suite for OrderedCollections.OrderedSet.
// Public API only (`import OrderedCollections`, not @testable). Swift Testing.
// Every expected value was verified out-of-band (see .rex_metrics/verifications.log)
// and pinned as a fixed literal — never recomputed with the type under test.
//
//===----------------------------------------------------------------------===//

import Testing
import OrderedCollections

@Suite("OrderedSet public value semantics")
struct OrderedSetMatrixTests {

  // MARK: - Construction: dedup keeps first occurrence and preserves order

  /// Contract: `init(_:)` removes duplicates, keeping the FIRST occurrence,
  /// and preserves insertion order of the surviving members.
  @Test(arguments: [
    ([3, 1, 2, 3, 1], [3, 1, 2]),         // duplicate-heavy, dupes after first
    ([1, 1, 1, 1], [1]),                  // all duplicates collapse to one
    ([5, 4, 3, 2, 1], [5, 4, 3, 2, 1]),   // already-unique order preserved verbatim
    ([], []),                             // empty boundary
    ([42], [42]),                         // single-element boundary
    ([2, 1, 2, 3, 1, 4], [2, 1, 3, 4]),   // interleaved dupes
  ])
  func dedupPreservesFirstAndOrder(input: [Int], expected: [Int]) {
    #expect(OrderedSet(input).elements == expected)
  }

  /// Dedup is by value identity; `count` reflects unique members only.
  @Test func stringDedupCount() {
    let set = OrderedSet(["the-alpha-token", "the-bravo-token", "the-alpha-token"])
    #expect(set.count == 2)
    #expect(set.elements == ["the-alpha-token", "the-bravo-token"])
    #expect(set[0] == "the-alpha-token")   // first occurrence wins the slot
    #expect(set[1] == "the-bravo-token")
  }

  /// Array-literal init is equivalent to `init(_:)`: dedups, preserves order.
  @Test func arrayLiteralDedups() {
    let set: OrderedSet = ["repeated-string-value", "other-string-value", "repeated-string-value"]
    #expect(set.elements == ["repeated-string-value", "other-string-value"])
    #expect(set[0] == "repeated-string-value")
  }

  // MARK: - Equality is order-sensitive (unlike Set); unordered view is not

  /// Contract: two ordered sets are equal iff same members in the SAME order.
  @Test func equalityIsOrderSensitive() {
    let a: OrderedSet = [1, 2, 3]
    let b: OrderedSet = [3, 2, 1]
    let c: OrderedSet = [1, 2, 3]
    #expect(a != b)            // same members, different order -> not equal
    #expect(a == c)            // identical order -> equal
    #expect(a.unordered == b.unordered)  // unordered view ignores order
  }

  // MARK: - Membership / index lookup

  /// `firstIndex(of:)` returns the offset of a member, `nil` when absent.
  @Test(arguments: [
    ("anchor-element-aaa", 0 as Int?),
    ("anchor-element-bbb", 1 as Int?),
    ("anchor-element-ccc", 2 as Int?),
    ("totally-absent-key", nil as Int?),
  ])
  func firstIndexOf(member: String, expected: Int?) {
    let set: OrderedSet = ["anchor-element-aaa", "anchor-element-bbb", "anchor-element-ccc"]
    #expect(set.firstIndex(of: member) == expected)
    #expect(set.contains(member) == (expected != nil))
  }

  /// Integer index subscript returns the element at that offset.
  @Test func indexSubscriptReadsByOffset() {
    let set: OrderedSet = ["offset-zero-string", "offset-one-string", "offset-two-string"]
    #expect(set[0] == "offset-zero-string")
    #expect(set[1] == "offset-one-string")
    #expect(set[2] == "offset-two-string")   // last-index boundary
  }

  // MARK: - append / insert return (inserted, index)

  /// Appending a NEW element appends at the end; appending an EXISTING one is a
  /// no-op that reports the element's current index.
  @Test func appendReportsInsertedAndIndex() {
    var set: OrderedSet = ["seed-member-one", "seed-member-two"]
    let dup = set.append("seed-member-one")
    #expect(dup.inserted == false)
    #expect(dup.index == 0)
    #expect(set.elements == ["seed-member-one", "seed-member-two"])  // unchanged

    let fresh = set.append("seed-member-new")
    #expect(fresh.inserted == true)
    #expect(fresh.index == 2)
    #expect(set[2] == "seed-member-new")
    #expect(set.elements == ["seed-member-one", "seed-member-two", "seed-member-new"])
  }

  /// `insert(_:at:)` inserts a new element at the requested offset; a duplicate
  /// is rejected without moving anything.
  @Test func insertAtIndex() {
    var set: OrderedSet = [10, 20, 30]
    let r = set.insert(15, at: 1)
    #expect(r.inserted == true)
    #expect(r.index == 1)
    #expect(set.elements == [10, 15, 20, 30])

    let dup = set.insert(20, at: 0)   // already present at offset 2
    #expect(dup.inserted == false)
    #expect(dup.index == 2)
    #expect(set.elements == [10, 15, 20, 30])  // no move on duplicate
  }

  /// `updateOrAppend` returns the replaced element (or nil if appended).
  @Test func updateOrAppendReturnsOldOrNil() {
    var set: OrderedSet = [1, 2, 3]
    #expect(set.updateOrAppend(2) == 2)    // existing -> returns old member
    #expect(set.updateOrAppend(4) == nil)  // new -> appended, returns nil
    #expect(set.elements == [1, 2, 3, 4])
  }

  // MARK: - Removal

  /// `remove(at:)` returns and removes the element at the offset; remaining
  /// elements close the gap, preserving order.
  @Test func removeAtIndex() {
    var set: OrderedSet = ["first-list-item", "second-list-item", "third-list-item"]
    let removed = set.remove(at: 1)
    #expect(removed == "second-list-item")
    #expect(set.elements == ["first-list-item", "third-list-item"])
    #expect(set[1] == "third-list-item")   // gap closed
  }

  /// `removeFirst()` removes and returns element 0.
  @Test func removeFirstReturnsHead() {
    var set: OrderedSet = ["head-string-value", "tail-string-value"]
    let head = set.removeFirst()
    #expect(head == "head-string-value")
    #expect(set.elements == ["tail-string-value"])
    #expect(set[0] == "tail-string-value")
  }

  /// Removing down to empty leaves an empty set; boundary at count == 1.
  @Test func removeDownToEmpty() {
    var set: OrderedSet = [99]
    let only = set.remove(at: 0)
    #expect(only == 99)
    #expect(set.isEmpty)
    #expect(set.elements == [])
  }

  // MARK: - Set algebra (order semantics pinned from verified output)

  /// `union`: members of `self` first, then members of `other` not in `self`,
  /// in `other`'s order.
  @Test func unionAppendsNewInOtherOrder() {
    let a: OrderedSet = [1, 2, 3, 4]
    let b: OrderedSet = [0, 2, 4, 6]
    #expect(a.union(b).elements == [1, 2, 3, 4, 0, 6])
  }

  /// `intersection`: common members in `self`'s order.
  @Test func intersectionFollowsSelfOrder() {
    let a: OrderedSet = [1, 2, 3, 4]
    let b: OrderedSet = [6, 4, 2, 0]
    #expect(a.intersection(b).elements == [2, 4])
    // Generalization over an arbitrary Sequence yields the same ordered result.
    #expect(a.intersection([6, 4, 2, 0] as [Int]).elements == [2, 4])
  }

  /// `subtracting`: members of `self` absent from `other`, in `self`'s order.
  @Test func subtractingKeepsSelfOrder() {
    let a: OrderedSet = [1, 2, 3, 4]
    let b: OrderedSet = [0, 2, 4, 6]
    #expect(a.subtracting(b).elements == [1, 3])
  }

  /// `symmetricDifference`: self-only members (in self order) followed by
  /// other-only members (in other order). Pinned from verified output —
  /// for other = [0, 2, 4, 6] the tail order is [0, 6], NOT [6, 0].
  @Test func symmetricDifferenceConcatenatesUniques() {
    let a: OrderedSet = [1, 2, 3, 4]
    let b: OrderedSet = [0, 2, 4, 6]
    #expect(a.symmetricDifference(b).elements == [1, 3, 0, 6])
  }

  /// Boundary: set algebra against the empty set / self.
  @Test func setAlgebraBoundaries() {
    let a: OrderedSet = [7, 8, 9]
    let empty = OrderedSet<Int>()
    #expect(a.union(empty).elements == [7, 8, 9])
    #expect(a.intersection(empty).elements == [])
    #expect(a.subtracting(empty).elements == [7, 8, 9])
    #expect(a.intersection(a).elements == [7, 8, 9])     // intersection with self
    #expect(a.subtracting(a).elements == [])             // subtract self -> empty
  }

  /// Set algebra preserves the actual member *strings* (string vectors pinned).
  @Test func setAlgebraStringMembers() {
    let a: OrderedSet = ["union-keep-alpha", "union-keep-bravo"]
    let b: OrderedSet = ["union-keep-bravo", "union-add-charlie"]
    let u = a.union(b)
    #expect(u.elements == ["union-keep-alpha", "union-keep-bravo", "union-add-charlie"])
    #expect(u[0] == "union-keep-alpha")
    #expect(u[1] == "union-keep-bravo")
    #expect(u[2] == "union-add-charlie")     // appended member, string pinned
    let i = a.intersection(b)
    #expect(i[0] == "union-keep-bravo")       // sole common member, string pinned
    let s = a.subtracting(b)
    #expect(s[0] == "union-keep-alpha")       // only self-exclusive member
  }

  /// Insertion order is observable member-by-member at each offset: a fixed
  /// vector is pinned so a misordering at ANY position fails (not just the
  /// whole-array compare). Each offset is an independent mutation target.
  @Test(arguments: [
    (0, "ordered-slot-zero-aa"),
    (1, "ordered-slot-one-bbb"),
    (2, "ordered-slot-two-ccc"),
    (3, "ordered-slot-three-d"),
    (4, "ordered-slot-four-eee"),
  ])
  func memberAtOffsetIsStable(offset: Int, expected: String) {
    let set: OrderedSet = [
      "ordered-slot-zero-aa",
      "ordered-slot-one-bbb",
      "ordered-slot-two-ccc",
      "ordered-slot-three-d",
      "ordered-slot-four-eee",
    ]
    #expect(set[offset] == expected)
    #expect(set.firstIndex(of: expected) == offset)
  }

  /// `removeFirst` peels members off the front in order; each peeled value is a
  /// pinned string literal, and the new head after each peel is pinned too.
  @Test func removeFirstPeelsInOrder() {
    var set: OrderedSet = ["peel-order-first-x", "peel-order-second-x", "peel-order-third-x"]
    #expect(set.removeFirst() == "peel-order-first-x")
    #expect(set[0] == "peel-order-second-x")
    #expect(set.removeFirst() == "peel-order-second-x")
    #expect(set[0] == "peel-order-third-x")
    #expect(set.removeFirst() == "peel-order-third-x")
    #expect(set.isEmpty)
  }

  /// `removeAll(where:)` drops every matching member and preserves the order of
  /// the survivors. Surviving string members are pinned by offset.
  @Test func removeAllWherePreservesSurvivorOrder() {
    var set: OrderedSet = ["survivor-even-aa", "dropped-odd-bbb",
                           "survivor-even-cc", "dropped-odd-ddd",
                           "survivor-even-ee"]
    set.removeAll(where: { $0.hasPrefix("dropped") })
    #expect(set.elements == ["survivor-even-aa", "survivor-even-cc", "survivor-even-ee"])
    #expect(set[0] == "survivor-even-aa")
    #expect(set[1] == "survivor-even-cc")
    #expect(set[2] == "survivor-even-ee")
  }

  /// Numeric `removeAll(where:)` boundary: predicate that matches everything
  /// empties the set; one that matches nothing leaves it intact.
  @Test func removeAllWhereBoundaries() {
    var all: OrderedSet = [5, 6, 7, 8, 9, 10, 11]
    all.removeAll(where: { !$0.isMultiple(of: 2) })   // drop odds
    #expect(all.elements == [6, 8, 10])

    var none: OrderedSet = [1, 2, 3]
    none.removeAll(where: { _ in false })             // keep all
    #expect(none.elements == [1, 2, 3])

    var every: OrderedSet = [1, 2, 3]
    every.removeAll(where: { _ in true })             // drop all
    #expect(every.elements == [])
  }
}
