/*
 * Matrix-generated suite (test-quality benchmark). Scope: LocalDateTime core contracts.
 */
package kotlinx.datetime.matrix

import kotlinx.datetime.*
import kotlin.test.*

class MatrixLocalDateTimeTest {

    // ---- toString: ISO 'T' separator; seconds dropped on a round minute; fraction padded ----
    @Test
    fun toString_readableIsoForm() {
        assertEquals("2020-08-30T18:43", LocalDateTime(2020, 8, 30, 18, 43).toString())
        assertEquals("2020-08-30T18:43", LocalDateTime(2020, 8, 30, 18, 43, 0).toString())   // round minute
        assertEquals("2020-08-30T18:43:00.500", LocalDateTime(2020, 8, 30, 18, 43, 0, 500_000_000).toString())
        assertEquals("2024-02-29T23:59:59.999999999", LocalDateTime(2024, 2, 29, 23, 59, 59, 999_999_999).toString())
    }

    @Test
    fun parse_roundTripsAndMapsComponents() {
        for (s in listOf("2020-08-30T18:43", "2020-08-30T18:43:05", "2023-01-02T23:40:57.120")) {
            assertEquals(s, LocalDateTime.parse(s).toString(), "round-trip identity for $s")
        }
        assertEquals(LocalDateTime(2020, 8, 30, 18, 43), LocalDateTime.parse("2020-08-30T18:43"))
    }

    @Test
    fun parse_rejectsMalformedAndInvalid_asIllegalArgument() {
        for (bad in listOf("2020-08-30 18:43", "2024-02-30T00:00", "2020-08-30T24:00", "garbage")) {
            assertFailsWith<IllegalArgumentException>("parse should reject \"$bad\"") { LocalDateTime.parse(bad) }
        }
    }

    @Test
    fun components_matchKnownDateTime() {
        val dt = LocalDateTime(2020, 8, 30, 18, 43, 15, 123)
        assertEquals(2020, dt.year)
        assertEquals(Month.AUGUST, dt.month)
        assertEquals(30, dt.day)
        assertEquals(18, dt.hour)
        assertEquals(43, dt.minute)
        assertEquals(15, dt.second)
        assertEquals(123, dt.nanosecond)
        assertEquals(DayOfWeek.SUNDAY, dt.dayOfWeek)
    }

    // ---- date / time decomposition is exact ----
    @Test
    fun dateAndTime_decompose() {
        val dt = LocalDateTime(2020, 8, 30, 18, 43, 15, 123)
        assertEquals(LocalDate(2020, 8, 30), dt.date)
        assertEquals(LocalTime(18, 43, 15, 123), dt.time)
        // and recompose to the original
        assertEquals(dt, LocalDateTime(dt.date, dt.time))
    }

    @Test
    fun constructor_rejectsOutOfRangeComponents() {
        val invalid: List<() -> LocalDateTime> = listOf(
            { LocalDateTime(2024, 2, 30, 0, 0) },   // Feb 30 invalid date
            { LocalDateTime(2024, 1, 1, 24, 0) },   // hour 24 invalid
            { LocalDateTime(2024, 1, 1, 0, 60) },   // minute 60 invalid
            { LocalDateTime(2024, 13, 1, 0, 0) },   // month 13 invalid
        )
        for ((i, build) in invalid.withIndex()) {
            assertFailsWith<IllegalArgumentException>("invalid case #$i should throw") { build() }
        }
    }

    @Test
    fun orNull_returnsNullForInvalidAndValueForValid() {
        assertNull(LocalDateTime.orNull(2024, 2, 30, 0, 0))
        assertEquals(
            LocalDateTime(2020, 8, 30, 18, 43),
            LocalDateTime.orNull(2020, 8, 30, 18, 43)
        )
    }

    // ---- comparison: date dominates, then time; equal instants compare to zero ----
    @Test
    fun compareTo_ordersByDateThenTime() {
        assertTrue(LocalDateTime(2020, 8, 30, 18, 43) < LocalDateTime(2020, 8, 30, 18, 44))
        assertTrue(LocalDateTime(2020, 8, 30, 23, 59) < LocalDateTime(2020, 8, 31, 0, 0)) // date dominates
        assertEquals(0, LocalDateTime(2024, 1, 1, 0, 0).compareTo(LocalDateTime(2024, 1, 1, 0, 0)))
    }
}
