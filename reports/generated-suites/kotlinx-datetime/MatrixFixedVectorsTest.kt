/*
 * Matrix-generated suite (test-quality benchmark) — iter2 round 2.
 * A battery of fixed ISO-8601 vectors pinned as literals (verified out-of-band).
 * Every expected value is a known-good constant, never recomputed via the API under test.
 */
package kotlinx.datetime.matrix

import kotlinx.datetime.*
import kotlin.test.*

class MatrixFixedVectorsTest {

    // ---- LocalDateTime: exact render of pinned components (boundaries + fractions) ----
    @Test
    fun localDateTime_rendersPinnedVectors() {
        assertEquals("2020-08-30T18:43:05", LocalDateTime(2020, 8, 30, 18, 43, 5).toString())
        assertEquals("2020-08-30T18:43:00.500", LocalDateTime(2020, 8, 30, 18, 43, 0, 500_000_000).toString())
        assertEquals("2024-02-29T00:00:00.000000001", LocalDateTime(2024, 2, 29, 0, 0, 0, 1).toString())     // 1 ns past leap-midnight
        assertEquals("2024-02-29T23:59:59.999999999", LocalDateTime(2024, 2, 29, 23, 59, 59, 999_999_999).toString()) // leap-day max
        assertEquals("0000-01-01T00:00:00.500", LocalDateTime(0, 1, 1, 0, 0, 0, 500_000_000).toString())     // year zero
    }

    // ---- LocalDateTime: parse is the exact inverse of toString for long vectors ----
    @Test
    fun localDateTime_parseRoundTripsLongVectors() {
        val vectors = listOf(
            "2023-01-02T23:40:57.120",
            "0000-01-01T00:00:00.500",
            "-0001-12-31T23:59:59.999999999",
            "2024-02-29T23:59:59.999999999",
        )
        for (s in vectors) {
            assertEquals(s, LocalDateTime.parse(s).toString(), "round-trip identity for $s")
        }
    }

    // ---- DateTimePeriod: exact ISO duration rendering, including signs and fractions ----
    @Test
    fun dateTimePeriod_rendersPinnedVectors() {
        assertEquals("P1Y2M3DT4H5M6S", DateTimePeriod(years = 1, months = 2, days = 3, hours = 4, minutes = 5, seconds = 6).toString())
        assertEquals("-P2Y4M1D", DateTimePeriod(years = -2, months = -4, days = -1).toString())   // all nonpositive -> leading '-'
        assertEquals("-P1Y2M", DateTimePeriod(months = -14).toString())                           // negative normalization
        assertEquals("P1DT3H2M4.123456789S", DateTimePeriod(days = 1, hours = 3, minutes = 2, seconds = 4, nanoseconds = 123456789).toString())
    }

    @Test
    fun dateTimePeriod_parseRoundTripsLongVectors() {
        for (s in listOf("P1Y2M3DT4H5M6S", "P1DT3H2M4.123456789S", "-P2Y4M1D")) {
            assertEquals(s, DateTimePeriod.parse(s).toString(), "round-trip identity for $s")
        }
    }

    // ---- LocalDate.periodUntil renders the exact pinned period ----
    @Test
    fun localDate_periodUntil_pinnedVectors() {
        assertEquals("P1Y2M19D", LocalDate(2024, 1, 1).periodUntil(LocalDate(2025, 3, 20)).toString())
        assertEquals("P1Y2M5D", LocalDate(2024, 1, 15).periodUntil(LocalDate(2025, 3, 20)).toString())
    }

    // ---- UtcOffset: seconds-precision offset renders and parses to the pinned value ----
    @Test
    fun utcOffset_secondsPrecisionPinnedVector() {
        assertEquals("+10:36:30", UtcOffset(hours = 10, minutes = 36, seconds = 30).toString())
        assertEquals(38190, UtcOffset.parse("+10:36:30").totalSeconds)   // 10*3600 + 36*60 + 30
        assertEquals(UtcOffset(hours = 10, minutes = 36, seconds = 30), UtcOffset.parse("+10:36:30"))
    }

    // ---- LocalTime: nanosecond-precision render is exact ----
    @Test
    fun localTime_nanosecondPrecisionPinnedVector() {
        assertEquals("18:43:00.123456789", LocalTime(18, 43, 0, 123456789).toString())
        assertEquals(LocalTime(18, 43, 0, 123456789), LocalTime.parse("18:43:00.123456789"))
    }
}
