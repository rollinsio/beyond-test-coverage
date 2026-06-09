//
//  GeneratedJSONTests.swift
//
//  A quality-scorecard-driven regeneration of the SwiftyJSON suite, written
//  against the public API only. Conventions:
//   - assertions pin fixed, known-good literals (rigor axis B.1);
//   - error paths assert the typed SwiftyJSONError *code*, never message text;
//   - repeated shapes are folded into parametrized `arguments:` cases;
//   - no hand mocks — SwiftyJSON is pure value logic.
//

import Foundation
import Testing
import SwiftyJSON

// MARK: - Type coercion: `*Value` getters coerce, optional getters are type-gated.

/// `boolValue` treats a fixed set of strings (case-insensitive) as truthy.
@Test(arguments: [
    ("y", true), ("Y", true), ("t", true), ("yes", true),
    ("YES", true), ("true", true), ("TRUE", true), ("1", true),
    ("n", false), ("no", false), ("0", false), ("nope", false),
])
func boolValueParsesTruthyStrings(input: String, expected: Bool) {
    #expect(JSON(input).boolValue == expected)
}

@Test func stringValueCoercesScalarsToText() {
    #expect(JSON(123).stringValue == "123")
    #expect(JSON(true).stringValue == "true")
    #expect(JSON(false).stringValue == "false")
    #expect(JSON("already-a-text-value").stringValue == "already-a-text-value")
}

@Test func optionalGettersAreTypeGated() {
    #expect(JSON(123).string == nil)               // number is not a string
    #expect(JSON("the-text-value").int == nil)     // string is not a number
    #expect(JSON("the-text-value").bool == nil)    // string is not a bool
    #expect(JSON(42).int == 42)                     // number → int present
    #expect(JSON("the-present-text").string == "the-present-text")
}

@Test func numericValueGettersReadNumbers() {
    #expect(JSON(7).intValue == 7)
    #expect(JSON(3.5).doubleValue == 3.5)
    #expect(JSON(-2).intValue == -2)
    #expect(JSON(1000000).intValue == 1000000)
}

// MARK: - Subscripts return the element, or a null JSON carrying a typed error.

@Test func arraySubscriptReturnsElementOrIndexOutOfBounds() {
    let json: JSON = ["the-first-entry", "the-second-entry", "the-third-entry!"]
    #expect(json[0].stringValue == "the-first-entry")
    #expect(json[2].stringValue == "the-third-entry!")
    #expect(json[9].error?.errorCode == 900)        // indexOutOfBounds
    #expect(json[9].exists() == false)
}

@Test func dictionarySubscriptReturnsValueOrNotExist() {
    let json: JSON = ["name": "Raffi Krikorian", "language": "the-swift-lang"]
    #expect(json["name"].stringValue == "Raffi Krikorian")
    #expect(json["language"].stringValue == "the-swift-lang")
    #expect(json["missing-key"].error?.errorCode == 500)   // notExist
    #expect(json["missing-key"].exists() == false)
}

/// Indexing a scalar by index *or* key is a wrong-type access (code 901).
@Test(arguments: [901])
func scalarSubscriptYieldsWrongTypeError(code: Int) {
    let scalar: JSON = "not-a-container-value"
    #expect(scalar[0].error?.errorCode == code)
    #expect(scalar["any-key"].error?.errorCode == code)
}

@Test func nestedPathTraversesNestedContainers() {
    let json: JSON = [
        "users": [
            ["name": "the-first-username"],
            ["name": "the-second-username"],
        ],
    ]
    #expect(json["users"][0]["name"].stringValue == "the-first-username")
    #expect(json["users"][1]["name"].stringValue == "the-second-username")
    #expect(json["users"][9]["name"].exists() == false)
}

@Test func existsDistinguishesPresentFromAbsent() {
    let json: JSON = ["present": "the-present-value"]
    #expect(json["present"].exists() == true)
    #expect(json["absent"].exists() == false)
}

// MARK: - Equality is by type + payload; cross-type never compares equal.

@Test func equalScalarsCompareEqual() {
    #expect(JSON("the-identical-text") == JSON("the-identical-text"))
    #expect(JSON(42) == JSON(42))
    #expect(JSON(true) == JSON(true))
    #expect(JSON(NSNull()) == JSON(NSNull()))
}

@Test func unequalAndCrossTypeCompareUnequal() {
    #expect(JSON("the-first-string!") != JSON("the-second-string"))
    #expect(JSON(42) != JSON("42"))      // number vs string
    #expect(JSON(true) != JSON(1))       // bool vs number
}

// MARK: - Literal initialisation builds the corresponding JSON type.

@Test func stringLiteralBuildsStringJSON() {
    let json: JSON = "a-string-literal-value"
    #expect(json.type == .string)
    #expect(json.string == "a-string-literal-value")
}

@Test func scalarLiteralsBuildScalars() {
    let number: JSON = 42
    #expect(number.intValue == 42)
    let flag: JSON = true
    #expect(flag.boolValue == true)
}

@Test func arrayAndDictionaryLiteralsBuildContainers() {
    let array: JSON = ["the-alpha-entry", "the-bravo-entry", "the-gamma-entry"]
    #expect(array.arrayValue.count == 3)
    #expect(array[1].stringValue == "the-bravo-entry")
    let dictionary: JSON = ["key": "the-dictionary-value"]
    #expect(dictionary.type == .dictionary)
    #expect(dictionary["key"].stringValue == "the-dictionary-value")
}

// MARK: - Parsing a document exposes every field through the typed getters.

@Test func parseJSONReadsAllFieldsOfADocument() {
    let json = JSON(parseJSON: """
        {
          "city": "San Francisco",
          "country": "United States",
          "region": "Northern California",
          "timezone": "America/Los_Angeles",
          "operator": "Raffi Krikorian",
          "postcode": "94103-1234",
          "population": 873965,
          "elevation": 16.0,
          "is_capital": false
        }
        """)
    #expect(json["city"].stringValue == "San Francisco")
    #expect(json["country"].stringValue == "United States")
    #expect(json["region"].stringValue == "Northern California")
    #expect(json["timezone"].stringValue == "America/Los_Angeles")
    #expect(json["operator"].stringValue == "Raffi Krikorian")
    #expect(json["postcode"].stringValue == "94103-1234")
    #expect(json["population"].intValue == 873965)
    #expect(json["elevation"].doubleValue == 16.0)
    #expect(json["is_capital"].boolValue == false)
}

@Test func parsedArrayExposesEachElementByIndex() {
    let json = JSON(parseJSON: """
        ["the-first-element", "the-second-element", "the-third-element!", "the-fourth-element"]
        """)
    #expect(json.arrayValue.count == 4)
    #expect(json[0].stringValue == "the-first-element")
    #expect(json[1].stringValue == "the-second-element")
    #expect(json[2].stringValue == "the-third-element!")
    #expect(json[3].stringValue == "the-fourth-element")
}

@Test func dictionaryLiteralExposesEachNestedString() {
    let json: JSON = [
        "title": "the-document-title",
        "author": "the-document-author",
        "summary": "the-document-summary",
    ]
    #expect(json["title"].stringValue == "the-document-title")
    #expect(json["author"].stringValue == "the-document-author")
    #expect(json["summary"].stringValue == "the-document-summary")
}

// MARK: - rawString serialises to JSON text that re-parses to the same values.

@Test func rawStringRoundTripsThroughParse() {
    let original: JSON = ["greeting": "hello-there-world", "farewell": "goodbye-for-now!"]
    let serialized = original.rawString(.utf8, options: [])
    let reparsed = JSON(parseJSON: serialized ?? "")
    #expect(reparsed["greeting"].stringValue == "hello-there-world")
    #expect(reparsed["farewell"].stringValue == "goodbye-for-now!")
}

// MARK: - merged(with:) adds new keys, overwrites shared keys, keeps the rest.

@Test func mergedAddsOverwritesAndKeepsKeys() throws {
    let base: JSON = ["keep": "the-original-keep", "shared": "the-old-shared!!"]
    let other: JSON = ["shared": "the-new-shared!!!", "added": "the-added-value!"]
    let merged = try base.merged(with: other)
    #expect(merged["keep"].stringValue == "the-original-keep")
    #expect(merged["shared"].stringValue == "the-new-shared!!!")
    #expect(merged["added"].stringValue == "the-added-value!")
}

// MARK: - null JSON.

@Test func nullJSONHasNullTypeAndAccessor() {
    let json = JSON(NSNull())
    #expect(json.type == .null)
    #expect(json.null != nil)
    #expect(JSON("the-non-null-text").null == nil)
}
