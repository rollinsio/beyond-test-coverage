//===----------------------------------------------------------------------===//
//
// This source file is part of the Swift Argument Parser open source project
//
// Copyright (c) 2024 Apple Inc. and the Swift project authors
// Licensed under Apache License v2.0 with Runtime Library Exception
//
// See https://swift.org/LICENSE.txt for license information
//
//===----------------------------------------------------------------------===//

// End-to-end parsing of `ParsableCommand` through its PUBLIC API
// (`parse(_:)` / `parseAsRoot(_:)`). Generated test-quality suite.
//
// Quality contract:
//  * Errors are asserted by PUBLIC CATEGORY via `exitCode(for:)` (the public
//    `ExitCode`), never by matching the human-readable message string — the
//    concrete thrown type (`CommandError`) is internal, so the observable public
//    contract is "throws, and its exit code is .validationFailure".
//  * Parsed values are pinned against fixed literal vectors.
//  * Repeated cases are parametrized via Swift Testing `@Test(arguments:)`.
//  * Real `ParsableCommand` structs are driven end-to-end; zero hand mocks.
//  * Boundaries (counting 0/1/N, inversion both ways + exclusivity, validate()
//    range edges) each have a dedicated, order/edge-observable case.
//
// Test types referenced by `@Test(arguments:)` parameter lists are `internal`
// (default visibility): the testing macro requires them to be at least as
// visible as the implicitly-`internal` test method.

import ArgumentParser
import Testing

// MARK: - Commands under test

fileprivate struct Basic: ParsableCommand {
  @Flag var verbose: Bool = false
  @Option var name: String
  @Option var count: Int = 1
  @Argument var path: String
}

fileprivate struct CustomNamed: ParsableCommand {
  @Option(name: [.customShort("n"), .customLong("full-name")]) var name: String
  @Option(name: .short) var count: Int = 0
}

fileprivate struct ShortFlags: ParsableCommand {
  @Flag(name: .short) var a: Bool = false
  @Flag(name: .short) var b: Bool = false
  @Flag(name: .short) var c: Bool = false
}

fileprivate struct Counting: ParsableCommand {
  @Flag(name: .shortAndLong) var verbose: Int
}

fileprivate struct Toggle: ParsableCommand {
  @Flag(inversion: .prefixedNo) var index: Bool = true
}

enum Mode: String, CaseIterable, ExpressibleByArgument {
  case fast, slow, auto
}

fileprivate struct Typed: ParsableCommand {
  @Option var mode: Mode
  @Option var ratio: Double
  @Option var enabled: Bool
}

enum Shape: String, EnumerableFlag {
  case circle, square, triangle
}

fileprivate struct Shapes: ParsableCommand {
  @Flag var shapes: [Shape] = []
}

fileprivate struct Repeating: ParsableCommand {
  @Option var values: [Int] = []
  @Argument var rest: [String] = []
}

fileprivate struct OptionalFields: ParsableCommand {
  @Option var label: String?
  @Argument var input: String?
}

fileprivate struct Terminated: ParsableCommand {
  @Option var name: String = "none"
  @Argument var rest: [String] = []
}

fileprivate struct Transformed: ParsableCommand {
  @Option(transform: { $0.uppercased() }) var tag: String
  @Option(transform: { (s: String) -> Int in
    guard let v = Int(s), v >= 0 else { throw ValidationError("must be >= 0") }
    return v
  }) var quantity: Int = 0
}

fileprivate struct Ranged: ParsableCommand {
  @Option var level: Int

  func validate() throws {
    guard (1...10).contains(level) else {
      throw ValidationError("level out of range")
    }
  }
}

fileprivate struct Shared: ParsableArguments {
  @Flag var verbose: Bool = false
  @Option var name: String
}

fileprivate struct Grouped: ParsableCommand {
  @OptionGroup var shared: Shared
  @Argument var path: String
}

fileprivate struct Root: ParsableCommand {
  static let configuration = CommandConfiguration(
    commandName: "root",
    subcommands: [Add.self, Remove.self])

  struct Add: ParsableCommand {
    static let configuration = CommandConfiguration(commandName: "add")
    @Option var item: String
    @Flag var force: Bool = false
  }

  struct Remove: ParsableCommand {
    static let configuration = CommandConfiguration(commandName: "remove")
    @Argument var target: String
  }
}

// MARK: - Scalar options & arguments (fixed-vector reads)

@Suite struct ScalarParsingTests {
  /// `@Option`/`@Argument`/`@Flag` populate their wrapped values from
  /// separated tokens. Long string literals double as B.1 fixed vectors.
  @Test func parsesSeparatedTokens() throws {
    let cmd = try Basic.parse([
      "--name", "quarterly-report", "--count", "3", "--verbose",
      "/var/log/output.txt",
    ])
    #expect(cmd.name == "quarterly-report")
    #expect(cmd.count == 3)
    #expect(cmd.verbose == true)
    #expect(cmd.path == "/var/log/output.txt")
  }

  /// `--key=value` joined syntax populates the same way as separated tokens.
  @Test func parsesJoinedEqualsTokens() throws {
    let cmd = try Basic.parse([
      "--name=quarterly-report", "--count=42", "relative/path/output.txt",
    ])
    #expect(cmd.name == "quarterly-report")
    #expect(cmd.count == 42)
    #expect(cmd.path == "relative/path/output.txt")
  }

  /// Defaults apply for omitted options/flags; only the required ones are given.
  @Test func appliesDefaultsWhenOmitted() throws {
    let cmd = try Basic.parse(["--name", "deployment-name", "artifacts/build.log"])
    #expect(cmd.count == 1)        // @Option default
    #expect(cmd.verbose == false)  // @Flag default
    #expect(cmd.name == "deployment-name")
    #expect(cmd.path == "artifacts/build.log")
  }

  /// Optional `@Option`/`@Argument` are nil when absent and bound when present.
  @Test func optionalFieldsBindOrStayNil() throws {
    let empty = try OptionalFields.parse([])
    #expect(empty.label == nil)
    #expect(empty.input == nil)

    let filled = try OptionalFields.parse(["--label", "primary-region", "us-east-1-zone"])
    #expect(filled.label == "primary-region")
    #expect(filled.input == "us-east-1-zone")
  }
}

// MARK: - Custom & short names

@Suite struct NameSpecificationTests {
  /// A `customShort`/`customLong` pair binds the SAME property from either
  /// spelling; `.short` derives a single-dash name from the property.
  @Test(arguments: [
    (["-n", "Alexandra-Smith"], "Alexandra-Smith"),
    (["--full-name", "Alexandra-Smith"], "Alexandra-Smith"),
  ])
  func bindsCustomNameFromEitherSpelling(_ args: [String], _ expected: String) throws {
    let cmd = try CustomNamed.parse(args)
    #expect(cmd.name == expected)
  }

  /// `.short` names derive a single-dash option (`-c`).
  @Test func derivesShortNameFromProperty() throws {
    let cmd = try CustomNamed.parse(["-n", "x", "-c", "5"])
    #expect(cmd.count == 5)
  }

  /// The parser requires the FULL long name — it does not accept an
  /// abbreviation/prefix of a declared long option.
  @Test func rejectsLongNameAbbreviation() {
    do {
      _ = try CustomNamed.parse(["--full", "value"])  // prefix of --full-name
      Issue.record("expected long-name abbreviation to be rejected")
    } catch {
      #expect(CustomNamed.exitCode(for: error) == .validationFailure)
    }
  }

  /// A short option without `allowingJoined` does not accept an attached value
  /// (`-nvalue`); the run-together token is an unknown composite option.
  @Test func rejectsAttachedShortValueWithoutJoined() {
    do {
      _ = try CustomNamed.parse(["-nAlexandra"])  // attached value, not opted in
      Issue.record("expected attached short value to be rejected")
    } catch {
      #expect(CustomNamed.exitCode(for: error) == .validationFailure)
    }
  }

  /// Combined single-dash flags (`-abc`) set each constituent flag; a single
  /// `-a` leaves the others at their default.
  @Test(arguments: [
    (["-abc"], [true, true, true]),
    (["-a"], [true, false, false]),
    (["-ac"], [true, false, true]),
    ([] as [String], [false, false, false]),
  ])
  func expandsCombinedShortFlags(_ args: [String], _ expected: [Bool]) throws {
    let cmd = try ShortFlags.parse(args)
    #expect([cmd.a, cmd.b, cmd.c] == expected)
  }
}

// MARK: - Typed values via ExpressibleByArgument (parametrized vectors)

@Suite struct TypedValueTests {
  /// A `RawRepresentable` enum option parses each of its raw cases.
  @Test(arguments: [
    ("fast", Mode.fast),
    ("slow", Mode.slow),
    ("auto", Mode.auto),
  ])
  func parsesEnumOptionRawValue(_ raw: String, _ expected: Mode) throws {
    let cmd = try Typed.parse(["--mode", raw, "--ratio", "1.0", "--enabled", "true"])
    #expect(cmd.mode == expected)
  }

  /// `Double` and `Bool` options round-trip from their string spellings. Each
  /// row supplies the full `--ratio` token so a leading-dash value uses the
  /// joined form (the separated form is covered by
  /// `rejectsLeadingDashAsSeparatedValue`).
  @Test(arguments: [
    ("--ratio=0", 0.0, "true", true),
    ("--ratio=3.14", 3.14, "false", false),
    ("--ratio=-2.5", -2.5, "true", true),
  ])
  func parsesDoubleAndBoolOptions(
    _ ratioToken: String, _ ratio: Double, _ enabledRaw: String, _ enabled: Bool
  ) throws {
    let cmd = try Typed.parse(["--mode", "fast", ratioToken, "--enabled", enabledRaw])
    #expect(cmd.ratio == ratio)
    #expect(cmd.enabled == enabled)
  }

  /// A leading-dash value supplied with SEPARATED syntax is read as another
  /// option, so the option's value is missing — a usage failure.
  @Test func rejectsLeadingDashAsSeparatedValue() {
    do {
      _ = try Typed.parse(["--mode", "fast", "--ratio", "-2.5", "--enabled", "true"])
      Issue.record("expected separated leading-dash value to throw")
    } catch {
      #expect(Typed.exitCode(for: error) == .validationFailure)
    }
  }
}

// MARK: - transform closures

@Suite struct TransformTests {
  /// A `transform:` closure is applied to the raw argument before binding.
  @Test(arguments: [
    ("hello-world-tag", "HELLO-WORLD-TAG"),
    ("Mixed-Case-Input", "MIXED-CASE-INPUT"),
  ])
  func appliesTransformClosure(_ raw: String, _ expected: String) throws {
    let cmd = try Transformed.parse(["--tag", raw])
    #expect(cmd.tag == expected)
  }

  /// A successful transform binds the converted value; a throwing transform is
  /// a usage failure.
  @Test func transformBindsConvertedValue() throws {
    let cmd = try Transformed.parse(["--tag", "x", "--quantity", "7"])
    #expect(cmd.quantity == 7)
  }

  @Test func throwingTransformIsUsageFailure() {
    do {
      _ = try Transformed.parse(["--tag", "x", "--quantity", "-1"])
      Issue.record("expected throwing transform to fail parse")
    } catch {
      #expect(Transformed.exitCode(for: error) == .validationFailure)
    }
  }
}

// MARK: - Counting flags (boundary coverage: 0, 1, N)

@Suite struct CountingFlagTests {
  /// A counting `@Flag` equals the number of occurrences (short or long).
  @Test(arguments: [
    ([] as [String], 0),
    (["-v"], 1),
    (["--verbose"], 1),
    (["-v", "-v", "-v"], 3),
    (["-vv"], 2),  // combined short form
  ])
  func countsFlagOccurrences(_ args: [String], _ expected: Int) throws {
    let cmd = try Counting.parse(args)
    #expect(cmd.verbose == expected)
  }
}

// MARK: - Inverted boolean flags (both directions + exclusivity)

@Suite struct InversionFlagTests {
  /// `inversion: .prefixedNo` exposes an on flag, an off `--no-` flag, and the
  /// declared default when neither is given; the last spelling wins
  /// (`.chooseLast` default exclusivity), which an order-swap pair pins.
  @Test(arguments: [
    ([] as [String], true),       // default
    (["--index"], true),
    (["--no-index"], false),
    (["--index", "--no-index"], false),  // .chooseLast
    (["--no-index", "--index"], true),   // order observable
  ])
  func resolvesInvertedFlag(_ args: [String], _ expected: Bool) throws {
    let cmd = try Toggle.parse(args)
    #expect(cmd.index == expected)
  }
}

// MARK: - EnumerableFlag arrays (order-sensitive collection)

@Suite struct EnumerableFlagTests {
  /// Each `EnumerableFlag` case is its own long flag; selections collect in the
  /// order the user supplied them (order-swap pins iteration order).
  @Test(arguments: [
    ([] as [String], [] as [Shape]),
    (["--circle"], [.circle]),
    (["--circle", "--triangle"], [.circle, .triangle]),
    (["--triangle", "--circle"], [.triangle, .circle]),
    (["--square", "--square"], [.square, .square]),
  ])
  func collectsEnumerableFlags(_ args: [String], _ expected: [Shape]) throws {
    let cmd = try Shapes.parse(args)
    #expect(cmd.shapes == expected)
  }
}

// MARK: - Repeating options, positional arrays, and the `--` terminator

@Suite struct RepeatingTests {
  /// A repeating `@Option` collects every occurrence's value in order, and a
  /// trailing positional `@Argument` array collects the rest.
  @Test func collectsRepeatingOptionsAndPositionals() throws {
    let cmd = try Repeating.parse([
      "--values", "1", "--values", "2", "--values", "3",
      "first-positional", "second-positional",
    ])
    #expect(cmd.values == [1, 2, 3])
    #expect(cmd.rest == ["first-positional", "second-positional"])
  }

  /// Empty input yields the declared empty-array defaults.
  @Test func emptyInputYieldsEmptyArrays() throws {
    let cmd = try Repeating.parse([])
    #expect(cmd.values == [])
    #expect(cmd.rest == [])
  }

  /// Everything after the `--` terminator is treated as a positional value,
  /// even tokens that look like options.
  @Test func terminatorRoutesOptionLikeTokensToPositionals() throws {
    let cmd = try Terminated.parse(["--", "--name", "literal-value"])
    #expect(cmd.rest == ["--name", "literal-value"])
    #expect(cmd.name == "none")  // option after -- is NOT consumed
  }
}

// MARK: - OptionGroup composition

@Suite struct OptionGroupTests {
  /// An `@OptionGroup` flattens a shared `ParsableArguments` into the command;
  /// its members and the command's own positional are all bound.
  @Test func flattensSharedArguments() throws {
    let cmd = try Grouped.parse([
      "--name", "service-alpha-prod", "--verbose", "config/deploy.yaml",
    ])
    #expect(cmd.shared.name == "service-alpha-prod")
    #expect(cmd.shared.verbose == true)
    #expect(cmd.path == "config/deploy.yaml")
  }

  /// A required member inside the group is still required.
  @Test func missingGroupedRequiredIsUsageFailure() {
    do {
      _ = try Grouped.parse(["only-positional"])
      Issue.record("expected missing grouped --name to fail")
    } catch {
      #expect(Grouped.exitCode(for: error) == .validationFailure)
    }
  }
}

// MARK: - Error categories (public ExitCode, never message prose)

@Suite struct ParseErrorTests {
  /// Malformed/incomplete invocations all surface as a usage failure
  /// (`ExitCode.validationFailure`) — asserted by public category, not message.
  @Test(arguments: [
    [] as [String],                                  // missing required --name and path
    ["--name", "x"],                                 // missing required positional
    ["--name", "x", "--count", "notAnInt", "p"],     // bad Int value
    ["--name", "x", "--bogus", "p"],                 // unknown option
    ["--name", "x", "p", "extra"],                   // unexpected extra positional
  ])
  func reportsUsageFailure(_ args: [String]) {
    do {
      _ = try Basic.parse(args)
      Issue.record("expected parse(\(args)) to throw")
    } catch {
      #expect(Basic.exitCode(for: error) == .validationFailure)
    }
  }

  /// A `ValidationError` thrown from `validate()` is reported as a usage failure
  /// for out-of-range input, and the in-range boundary parses cleanly.
  @Test(arguments: [
    (0, false),    // below lower boundary -> throws
    (1, true),     // lower boundary inclusive
    (10, true),    // upper boundary inclusive
    (11, false),   // above upper boundary -> throws
  ])
  func enforcesValidateBoundaries(_ level: Int, _ shouldSucceed: Bool) {
    do {
      let cmd = try Ranged.parse(["--level", "\(level)"])
      #expect(shouldSucceed)
      #expect(cmd.level == level)
    } catch {
      #expect(!shouldSucceed)
      #expect(Ranged.exitCode(for: error) == .validationFailure)
    }
  }

  /// An invalid enum raw value for an `ExpressibleByArgument` option fails.
  @Test func rejectsUnknownEnumValue() {
    do {
      _ = try Typed.parse(["--mode", "sideways", "--ratio", "1", "--enabled", "true"])
      Issue.record("expected unknown enum value to throw")
    } catch {
      #expect(Typed.exitCode(for: error) == .validationFailure)
    }
  }
}

// MARK: - Subcommand routing via parseAsRoot

@Suite struct SubcommandTests {
  /// `parseAsRoot` dispatches to the named subcommand and binds its arguments.
  @Test func routesToAddSubcommand() throws {
    let parsed = try Root.parseAsRoot(["add", "--item", "configuration-widget", "--force"])
    let add = try #require(parsed as? Root.Add)
    #expect(add.item == "configuration-widget")
    #expect(add.force == true)
  }

  /// A different subcommand name routes to its own type with its own arguments.
  @Test func routesToRemoveSubcommand() throws {
    let parsed = try Root.parseAsRoot(["remove", "target-archive.tar.gz"])
    let remove = try #require(parsed as? Root.Remove)
    #expect(remove.target == "target-archive.tar.gz")
  }

  /// Subcommand-level problems (unknown name, missing required arg) are usage
  /// failures, asserted by public category.
  @Test(arguments: [
    ["nonexistent"],          // unknown subcommand
    ["add"],                  // subcommand missing required --item
    ["remove"],               // subcommand missing required positional
  ])
  func reportsSubcommandUsageFailure(_ args: [String]) {
    do {
      _ = try Root.parseAsRoot(args)
      Issue.record("expected parseAsRoot(\(args)) to throw")
    } catch {
      #expect(Root.exitCode(for: error) == .validationFailure)
    }
  }
}

// MARK: - ExitCode public constants (documented contract)

@Suite struct ExitCodeTests {
  /// The public `ExitCode` constants carry their documented raw POSIX values.
  @Test(arguments: [
    (ExitCode.success, Int32(0)),
    (ExitCode.failure, Int32(1)),
    (ExitCode.validationFailure, Int32(64)),
  ])
  func exposesDocumentedRawValues(_ code: ExitCode, _ raw: Int32) {
    #expect(code.rawValue == raw)
  }

  /// `isSuccess` is true only for the success code.
  @Test func isSuccessReflectsSuccessCodeOnly() {
    #expect(ExitCode.success.isSuccess)
    #expect(!ExitCode.failure.isSuccess)
    #expect(!ExitCode.validationFailure.isSuccess)
  }
}
