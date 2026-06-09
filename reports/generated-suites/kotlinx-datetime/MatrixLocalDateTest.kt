/*
 * Matrix-generated suite (test-quality benchmark). Scope: LocalDate core contracts.
 * Public API only; expected values are fixed literals verified out-of-band.
 */
package kotlinx.datetime.matrix

import kotlinx.datetime.*
import kotlin.test.*

class MatrixLocalDateTest {

    // ---- toString: ISO-8601 extended, including expanded/negative/zero years ----
    @Test
    fun toString_isoExtendedForRepresentativeYears() {
        // expected ISO string FIRST, value under test SECOND
        assertEquals("2024-02-29", LocalDate(2024, 2, 29).toString())   // leap day
        assertEquals("0000-01-01", LocalDate(0, 1, 1).toString())       // year zero
        assertEquals("-0001-08-30", LocalDate(-1, 8, 30).toString())    // negative year, zero-padded
        assertEquals("+12020-08-30", LocalDate(12020, 8, 30).toString()) // expanded year >9999
    }

    // ---- parse is the exact inverse of toString for these vectors ----
    @Test
    fun parse_roundTripsFixedVectors() {
        val vectors = listOf("2024-02-29", "0000-01-01", "-0001-08-30", "+12020-08-30", "1970-01-01")
        for (s in vectors) {
            assertEquals(s, LocalDate.parse(s).toString(), "round-trip should be identity for $s")
        }
        // parse maps to the exact components (not via the same toString path)
        assertEquals(LocalDate(2024, 2, 29), LocalDate.parse("2024-02-29"))
    }

    @Test
    fun parse_rejectsMalformedAndOutOfRange_asIllegalArgument() {
        // DateTimeFormatException is internal and extends IllegalArgumentException.
        for (bad in listOf("not-a-date", "2024-13-01", "2024-02-30", "2024-00-01", "20240229")) {
            assertFailsWith<IllegalArgumentException>("parse should reject \"$bad\"") {
                LocalDate.parse(bad)
            }
        }
    }

    // ---- component accessors on a known date ----
    @Test
    fun components_matchKnownDate() {
        val d = LocalDate(2024, 2, 29)
        assertEquals(2024, d.year)
        assertEquals(Month.FEBRUARY, d.month)
        assertEquals(2, d.month.number)
        assertEquals(29, d.day)
        assertEquals(DayOfWeek.THURSDAY, d.dayOfWeek)
        assertEquals(60, d.dayOfYear)          // 31 (Jan) + 29 (Feb) in a leap year
        assertEquals(DayOfWeek.MONDAY, LocalDate(2024, 1, 1).dayOfWeek)
    }

    // ---- throwing constructor: invalid components raise IllegalArgumentException ----
    @Test
    fun constructor_rejectsOutOfRangeComponents() {
        val invalid: List<() -> LocalDate> = listOf(
            { LocalDate(2024, 13, 1) },   // month overflow
            { LocalDate(2024, 0, 1) },    // month underflow
            { LocalDate(2024, 1, 0) },    // day underflow
            { LocalDate(2024, 4, 31) },   // April has 30 days
            { LocalDate(2023, 2, 29) },   // not a leap year
            { LocalDate(2024, 2, 30) },   // Feb never has 30 days
        )
        for ((i, build) in invalid.withIndex()) {
            assertFailsWith<IllegalArgumentException>("invalid case #$i should throw") { build() }
        }
    }

    // ---- orNull mirrors the constructor but returns null instead of throwing ----
    @Test
    fun orNull_returnsNullForInvalidAndValueForValid() {
        assertNull(LocalDate.orNull(2023, 2, 29))   // non-leap Feb 29
        assertNull(LocalDate.orNull(2024, 13, 1))
        assertEquals(LocalDate(2024, 2, 29), LocalDate.orNull(2024, 2, 29))
    }

    // ---- epoch-day round trip with a pinned anchor ----
    @Test
    fun epochDays_anchorAndRoundTrip() {
        assertEquals(0L, LocalDate(1970, 1, 1).toEpochDays())   // epoch anchor
        assertEquals(LocalDate(1970, 1, 1), LocalDate.fromEpochDays(0))
        for (d in listOf(LocalDate(2024, 2, 29), LocalDate(0, 1, 1), LocalDate(-1, 12, 31))) {
            assertEquals(d, LocalDate.fromEpochDays(d.toEpochDays()), "epoch-day round trip for $d")
        }
    }

    // ---- month arithmetic clamps the day to the end of the target month ----
    @Test
    fun plusMonth_clampsEndOfMonth() {
        assertEquals(LocalDate(2021, 2, 28), LocalDate(2021, 1, 31).plus(1, DateTimeUnit.MONTH)) // non-leap
        assertEquals(LocalDate(2024, 2, 29), LocalDate(2024, 1, 31).plus(1, DateTimeUnit.MONTH)) // leap
        assertEquals(LocalDate(2021, 2, 28), LocalDate(2020, 2, 29).plus(1, DateTimeUnit.YEAR))  // leap->non-leap
    }

    // ---- single-day steps across the leap-day boundary, both directions ----
    @Test
    fun plusMinusDay_crossesLeapBoundary() {
        assertEquals(LocalDate(2024, 2, 29), LocalDate(2024, 3, 1).minus(1, DateTimeUnit.DAY))
        assertEquals(LocalDate(2024, 3, 1), LocalDate(2024, 2, 29).plus(1, DateTimeUnit.DAY))
        assertEquals(LocalDate(2024, 2, 28), LocalDate(2024, 2, 29).minus(1, DateTimeUnit.DAY))
    }

    // ---- plus(DatePeriod) applies years/months before days ----
    @Test
    fun plusDatePeriod_combinesComponents() {
        assertEquals(LocalDate(2024, 2, 2), LocalDate(2024, 1, 1).plus(DatePeriod(months = 1, days = 1)))
        assertEquals(LocalDate(2025, 3, 16), LocalDate(2024, 1, 15).plus(DatePeriod(years = 1, months = 2, days = 1)))
        // minus(period) is the inverse of plus(period)
        val start = LocalDate(2024, 1, 15)
        val p = DatePeriod(years = 1, months = 2, days = 1)
        assertEquals(start, start.plus(p).minus(p))
    }

    // ---- until / *Until: magnitude and sign ----
    @Test
    fun until_magnitudeAndSign() {
        val a = LocalDate(2024, 1, 1)
        val b = LocalDate(2024, 3, 1)
        assertEquals(60, a.daysUntil(b))            // leap-year Jan(31)+Feb(29)
        assertEquals(-60, b.daysUntil(a))           // reversed -> negated
        assertEquals(14, a.monthsUntil(LocalDate(2025, 3, 1)))
        assertEquals(3, a.yearsUntil(LocalDate(2027, 1, 1)))
        assertEquals(0, a.daysUntil(a))             // identical -> zero
    }

    @Test
    fun periodUntil_isAddBackInverse() {
        val a = LocalDate(2024, 1, 15)
        val b = LocalDate(2025, 3, 20)
        assertEquals("P1Y2M5D", a.periodUntil(b).toString())   // fixed expected, verified out-of-band
        assertEquals(b, a.plus(a.periodUntil(b)))              // adding the period back reaches b
    }

    // ---- comparison defines a strict ordering ----
    @Test
    fun compareTo_ordersByCalendarPosition() {
        val earlier = LocalDate(2024, 1, 1)
        val later = LocalDate(2024, 1, 2)
        assertTrue(earlier < later)
        assertTrue(later > earlier)
        assertEquals(0, earlier.compareTo(LocalDate(2024, 1, 1)))
        assertTrue(LocalDate(-1, 12, 31) < LocalDate(0, 1, 1))  // negative year is earlier
    }

    // ---- arithmetic past the supported range overflows with DateTimeArithmeticException ----
    @Test
    fun arithmeticOverflow_throwsArithmeticException() {
        assertFailsWith<DateTimeArithmeticException> {
            LocalDate(999_999_999, 12, 31).plus(1, DateTimeUnit.YEAR)
        }
        assertFailsWith<DateTimeArithmeticException> {
            LocalDate(-999_999_999, 1, 1).minus(1, DateTimeUnit.DAY)
        }
    }
}
