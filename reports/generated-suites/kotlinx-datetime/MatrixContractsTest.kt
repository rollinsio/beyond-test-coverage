/*
 * Matrix-generated suite (test-quality benchmark) — iter20 round 3.
 * Additional contracts: rounding-toward-zero, normalization equality, ISO Formats vs
 * toString, basic formats, week folding, until-with-unit. Pinned literals verified out-of-band.
 */
package kotlinx.datetime.matrix

import kotlinx.datetime.*
import kotlin.test.*

class MatrixContractsTest {

    // ---- until / *Until round toward zero: a partial unit counts as zero ----
    @Test
    fun until_roundsTowardZero() {
        // Jan 31 -> Feb 29 is less than a whole month (no day-of-month match), so 0 months.
        assertEquals(0, LocalDate(2024, 1, 31).monthsUntil(LocalDate(2024, 2, 29)))
        assertEquals(1, LocalDate(2024, 1, 31).monthsUntil(LocalDate(2024, 3, 1)))
        // Leap Feb 29 -> next Feb 28 is one day short of a full year.
        assertEquals(0, LocalDate(2024, 2, 29).yearsUntil(LocalDate(2025, 2, 28)))
        assertEquals(1, LocalDate(2024, 2, 29).yearsUntil(LocalDate(2025, 3, 1)))
    }

    // ---- until(unit): whole count of the given unit, toward zero ----
    @Test
    fun untilWithUnit_wholeCounts() {
        val a = LocalDate(2024, 1, 1)
        assertEquals(60L, a.until(LocalDate(2024, 3, 1), DateTimeUnit.DAY))
        assertEquals(8L, a.until(LocalDate(2024, 3, 1), DateTimeUnit.WEEK))   // 60/7 -> 8, toward zero
        assertEquals(24L, a.until(LocalDate(2026, 1, 1), DateTimeUnit.MONTH))
    }

    // ---- DateTimePeriod equality is defined by normalized totals, not raw construction args ----
    @Test
    fun dateTimePeriod_normalizationEquality() {
        assertEquals(DateTimePeriod(years = 2, days = 41), DateTimePeriod(months = 24, days = 41))
        assertEquals(
            DateTimePeriod(years = 2, hours = 3, minutes = 3),
            DateTimePeriod(months = 24, hours = 2, minutes = 63),
        )
        // Days are NOT folded into months (calendar days vary), so they stay verbatim.
        assertEquals("P1Y2M41D", DatePeriod(months = 14, days = 41).toString())
    }

    // ---- Formats.ISO differs from toString: ISO always includes seconds ----
    @Test
    fun isoFormat_alwaysIncludesSeconds_unlikeToString() {
        assertEquals("18:43", LocalTime(18, 43).toString())                       // toString drops round-minute seconds
        assertEquals("18:43:00", LocalTime.Formats.ISO.format(LocalTime(18, 43))) // Formats.ISO keeps them
    }

    // ---- predefined formats render the documented basic/four-digit forms ----
    @Test
    fun predefinedFormats_renderDocumentedForms() {
        assertEquals("2024-02-29", LocalDate.Formats.ISO.format(LocalDate(2024, 2, 29)))
        assertEquals("20200830", LocalDate.Formats.ISO_BASIC.format(LocalDate(2020, 8, 30)))
        assertEquals("+0130", UtcOffset.Formats.FOUR_DIGITS.format(UtcOffset(hours = 1, minutes = 30)))
        // ISO_BASIC parse is the inverse of ISO_BASIC format.
        assertEquals(LocalDate(2020, 8, 30), LocalDate.parse("20200830", LocalDate.Formats.ISO_BASIC))
    }

    // ---- negative UtcOffset with seconds; high-order component may exceed normal bounds ----
    @Test
    fun utcOffset_negativeAndOverflowingHighOrder() {
        assertEquals("-01:23:45", UtcOffset(hours = -1, minutes = -23, seconds = -45).toString())
        assertEquals(-5025, UtcOffset.parse("-01:23:45").totalSeconds)  // -(3600+1380+45)
        assertEquals("-01:00", UtcOffset(seconds = -3600).toString())   // seconds beyond 59 allowed as sole component
        assertEquals("+04:01", UtcOffset(minutes = 241).toString())     // 241 min = 4h 1m
    }

    // ---- DatePeriod folds weeks into days on parse; mixed signs preserved ----
    @Test
    fun dateTimePeriod_parseWeekFoldingAndNanoseconds() {
        assertEquals("P17D", DateTimePeriod.parse("P2W3D").toString())          // 2*7 + 3
        assertEquals("-PT0.000000001S", DateTimePeriod.parse("-PT0.000000001S").toString()) // minus one nanosecond
        assertEquals("P1Y40D", DateTimePeriod.parse("P1Y40D").toString())
        assertIs<DatePeriod>(DateTimePeriod.parse("P2W3D"))                      // no time comps -> DatePeriod
    }

    // ---- DateTimeUnit normalizes multiples to the coarsest named unit ----
    @Test
    fun dateTimeUnit_multiplesNormalizeToCoarsestName() {
        assertEquals("2-WEEK", (DateTimeUnit.WEEK * 2).toString())
        assertEquals("2-QUARTER", (DateTimeUnit.MONTH * 6).toString())  // 6 months = 2 quarters
        assertEquals("YEAR", (DateTimeUnit.MONTH * 12).toString())      // 12 months = 1 year
        assertEquals("WEEK", (DateTimeUnit.DAY * 7).toString())         // 7 days = 1 week
    }

    // ---- atTime composes LocalDate + components into the expected LocalDateTime ----
    @Test
    fun localDate_atTime_composesDateTime() {
        assertEquals(
            "2024-02-29T23:59:59.999999999",
            LocalDate(2024, 2, 29).atTime(23, 59, 59, 999_999_999).toString(),
        )
        assertEquals(
            LocalDateTime(2024, 2, 29, 23, 59, 59, 999_999_999),
            LocalDate(2024, 2, 29).atTime(LocalTime(23, 59, 59, 999_999_999)),
        )
    }
}
