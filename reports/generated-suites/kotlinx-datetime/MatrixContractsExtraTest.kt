/*
 * Matrix-generated suite (test-quality benchmark) — iter20 round 4.
 * Signed-period rendering, fraction normalization, the LocalDate minus(LocalDate) operator,
 * and finer time-unit names. Pinned literals verified out-of-band.
 */
package kotlinx.datetime.matrix

import kotlinx.datetime.*
import kotlin.test.*

class MatrixContractsExtraTest {

    // ---- signed DateTimePeriod rendering: leading '-' vs per-component sign ----
    @Test
    fun dateTimePeriod_signedRendering() {
        assertEquals("-PT1H30M", DateTimePeriod(hours = -1, minutes = -30).toString())       // all nonpositive -> leading '-'
        assertEquals("-PT4.500000000S", DateTimePeriod(seconds = -4, nanoseconds = -500_000_000).toString())
        assertEquals("PT25H", DateTimePeriod(hours = 25).toString())                          // hours not folded into days
    }

    // ---- parse: an outer '-' negates the entire period ----
    @Test
    fun dateTimePeriod_outerSignNegatesWhole() {
        assertEquals("P2M-1D", DateTimePeriod.parse("-P-2M1D").toString())
        assertEquals(DateTimePeriod(months = 2, days = -1), DateTimePeriod.parse("-P-2M1D"))
    }

    // ---- fractional seconds pad to a multiple of three digits on render ----
    @Test
    fun localDateTime_fractionPadsToMultipleOfThree() {
        assertEquals("2020-08-30T18:43:00.500", LocalDateTime.parse("2020-08-30T18:43:00.5").toString())
        assertEquals("2024-12-31T23:59:59", LocalDateTime(2024, 12, 31, 23, 59, 59).toString())  // no fraction, seconds kept
        assertEquals("-0001-01-01T00:00", LocalDateTime(-1, 1, 1, 0, 0, 0).toString())            // negative year, round minute
    }

    // ---- minus(LocalDate) and the range/operator forms agree with periodUntil ----
    @Test
    fun localDate_minusDate_isReversedPeriodUntil() {
        val a = LocalDate(2024, 1, 15)
        val b = LocalDate(2025, 3, 20)
        // a - b == b.periodUntil(a); here b - a == a.periodUntil(b)
        assertEquals("P1Y2M5D", (b - a).toString())
        assertEquals(a.periodUntil(b), b - a)
    }

    // ---- end-of-month clamp also applies to minus(DatePeriod) and plus(DatePeriod) ----
    @Test
    fun localDate_periodArithmeticClamp() {
        assertEquals("2024-02-01", LocalDate(2024, 3, 1).minus(DatePeriod(months = 1)).toString())
        assertEquals("2024-02-29", LocalDate(2024, 1, 31).plus(DatePeriod(months = 1)).toString())  // leap clamp
    }

    // ---- finer time-unit names and multiples ----
    @Test
    fun dateTimeUnit_fineUnitNames() {
        assertEquals("MILLISECOND", DateTimeUnit.MILLISECOND.toString())
        assertEquals("MICROSECOND", DateTimeUnit.MICROSECOND.toString())
        assertEquals("30-SECOND", (DateTimeUnit.SECOND * 30).toString())
        assertEquals(DateTimeUnit.MILLISECOND, DateTimeUnit.MICROSECOND * 1000)
    }
}
