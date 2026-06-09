/*
 * Matrix-generated suite (test-quality benchmark).
 * Scope: DateTimePeriod / DatePeriod, DateTimeUnit, UtcOffset core contracts.
 */
package kotlinx.datetime.matrix

import kotlinx.datetime.*
import kotlin.test.*

class MatrixPeriodUnitOffsetTest {

    // ===================== DateTimePeriod / DatePeriod =====================

    // ISO-8601 duration rendering, including the 'T' separator and fractional seconds.
    @Test
    fun dateTimePeriod_toString_isoDuration() {
        assertEquals("PT1H30M", DateTimePeriod(hours = 1, minutes = 30).toString())
        assertEquals("P1Y2M3D", DateTimePeriod(years = 1, months = 2, days = 3).toString())
        assertEquals("PT4.123456789S", DateTimePeriod(seconds = 4, nanoseconds = 123456789).toString())
        assertEquals("P1DT-3H", DateTimePeriod(days = 1, hours = -3).toString())  // mixed signs preserved
        assertEquals("P0D", DateTimePeriod().toString())                          // empty period
    }

    // Components normalize: months fold into years; minutes fold into hours.
    @Test
    fun dateTimePeriod_normalizesComponents() {
        val p = DateTimePeriod(months = 14)
        assertEquals(1, p.years)
        assertEquals(2, p.months)
        assertEquals("P1Y2M", p.toString())

        val t = DateTimePeriod(minutes = 90)
        assertEquals(1, t.hours)
        assertEquals(30, t.minutes)
    }

    // A period with only date components is a DatePeriod; one with time components is not.
    @Test
    fun dateTimePeriod_datePeriodSubtypeByContent() {
        assertIs<DatePeriod>(DateTimePeriod(months = 14))            // time comps all zero
        assertIs<DatePeriod>(DateTimePeriod(years = 1, days = 3))
        val withTime: DateTimePeriod = DateTimePeriod(hours = 1)
        assertFalse(withTime is DatePeriod)                          // has a time component
    }

    @Test
    fun dateTimePeriod_parseRoundTripsAndSubtype() {
        for (s in listOf("P1Y2M3D", "PT1H30M", "PT4.123456789S", "P1DT-3H")) {
            assertEquals(s, DateTimePeriod.parse(s).toString(), "round-trip identity for $s")
        }
        assertEquals(DateTimePeriod(hours = 1, minutes = 30), DateTimePeriod.parse("PT1H30M"))
        assertIs<DatePeriod>(DateTimePeriod.parse("P1Y40D"))         // no time comps -> DatePeriod
    }

    @Test
    fun dateTimePeriod_parseRejectsGarbage_asIllegalArgument() {
        for (bad in listOf("garbage", "", "1Y", "P")) {
            assertFailsWith<IllegalArgumentException>("parse should reject \"$bad\"") { DateTimePeriod.parse(bad) }
        }
    }

    @Test
    fun datePeriod_parseRejectsTimeComponents() {
        assertEquals("P1Y2M3D", DatePeriod(years = 1, months = 2, days = 3).toString())
        assertEquals("P0D", DatePeriod().toString())
        // DatePeriod.parse must reject any string carrying a non-zero time component.
        assertFailsWith<IllegalArgumentException> { DatePeriod.parse("P1DT1H") }
    }

    // ===================== DateTimeUnit =====================

    // Each predefined unit renders to its documented name; multiples get an "N-" prefix.
    @Test
    fun dateTimeUnit_toStringNames() {
        val expected = mapOf(
            DateTimeUnit.NANOSECOND to "NANOSECOND",
            DateTimeUnit.SECOND to "SECOND",
            DateTimeUnit.HOUR to "HOUR",
            DateTimeUnit.DAY to "DAY",
            DateTimeUnit.WEEK to "WEEK",
            DateTimeUnit.MONTH to "MONTH",
            DateTimeUnit.QUARTER to "QUARTER",
            DateTimeUnit.YEAR to "YEAR",
            DateTimeUnit.CENTURY to "CENTURY",
        )
        for ((unit, name) in expected) {
            assertEquals(name, unit.toString(), "name of $name unit")
        }
        assertEquals("5-DAY", (DateTimeUnit.DAY * 5).toString())   // scalar multiple
        assertEquals("2-HOUR", (DateTimeUnit.HOUR * 2).toString())
        assertEquals("MONTH", (DateTimeUnit.MONTH * 1).toString()) // scalar 1 -> bare name
    }

    // Multiplication composes durations: 1000 ns == 1 microsecond, and units compare by value.
    @Test
    fun dateTimeUnit_multiplicationAndEquality() {
        assertEquals(DateTimeUnit.MICROSECOND, DateTimeUnit.NANOSECOND * 1000)
        assertEquals(DateTimeUnit.DayBased(1), DateTimeUnit.DAY)
        assertEquals(DateTimeUnit.MonthBased(12), DateTimeUnit.YEAR)
        assertEquals(DateTimeUnit.DayBased(7), DateTimeUnit.WEEK)
        assertNotEquals<DateTimeUnit>(DateTimeUnit.DayBased(1), DateTimeUnit.DayBased(2))
    }

    // A unit's length must be strictly positive.
    @Test
    fun dateTimeUnit_rejectsNonPositiveLength() {
        assertFailsWith<IllegalArgumentException> { DateTimeUnit.DayBased(0) }
        assertFailsWith<IllegalArgumentException> { DateTimeUnit.DayBased(-1) }
        assertFailsWith<IllegalArgumentException> { DateTimeUnit.TimeBased(0) }
        assertFailsWith<IllegalArgumentException> { DateTimeUnit.MonthBased(0) }
    }

    // ===================== UtcOffset =====================

    // ISO-8601 rendering: Z for zero, sign-padded HH:MM, seconds only when non-zero.
    @Test
    fun utcOffset_toStringIsoForm() {
        assertEquals("Z", UtcOffset.ZERO.toString())                  // zero offset -> "Z"
        assertEquals("+01:30", UtcOffset(hours = 1, minutes = 30).toString())
        assertEquals("-02:00", UtcOffset(hours = -2).toString())      // negative, minutes padded
        assertEquals("+05:00", UtcOffset(hours = 5).toString())
        assertEquals("+01:23:45", UtcOffset(hours = 1, minutes = 23, seconds = 45).toString()) // seconds shown
    }

    @Test
    fun utcOffset_totalSecondsAndParse() {
        assertEquals(0, UtcOffset.parse("Z").totalSeconds)
        assertEquals(5400, UtcOffset.parse("+01:30").totalSeconds)    // 1h30m = 5400s
        assertEquals(5400, UtcOffset(hours = 1, minutes = 30).totalSeconds)
        assertEquals(UtcOffset(hours = 5), UtcOffset.parse("+05:00"))
        assertEquals(UtcOffset.ZERO, UtcOffset.parse("Z"))
    }

    @Test
    fun utcOffset_parseRoundTrips() {
        for (s in listOf("Z", "+01:30", "-02:00", "+01:23:45")) {
            assertEquals(s, UtcOffset.parse(s).toString(), "round-trip identity for $s")
        }
    }

    // Constructor validation: same sign required, components bounded, range +/-18:00.
    @Test
    fun utcOffset_constructorValidation() {
        assertFailsWith<IllegalArgumentException> { UtcOffset(hours = 1, minutes = -30) } // mixed signs
        assertFailsWith<IllegalArgumentException> { UtcOffset(hours = 19) }               // beyond +18:00
        assertFailsWith<IllegalArgumentException> { UtcOffset(hours = 0, minutes = 60) }  // minute out of bounds
        assertNull(UtcOffset.orNull(hours = 1, minutes = -30))
        assertNull(UtcOffset.orNull(hours = 19))
    }

    @Test
    fun utcOffset_parseRejectsInvalid_asIllegalArgument() {
        for (bad in listOf("garbage", "+19:00", "1:30")) {
            assertFailsWith<IllegalArgumentException>("parse should reject \"$bad\"") { UtcOffset.parse(bad) }
        }
    }
}
