/*
 * Matrix-generated suite (test-quality benchmark). Scope: LocalTime core contracts.
 */
package kotlinx.datetime.matrix

import kotlinx.datetime.*
import kotlin.test.*

class MatrixLocalTimeTest {

    // ---- toString: seconds omitted on a round minute; fraction padded to a multiple of 3 ----
    @Test
    fun toString_readableIsoForm() {
        assertEquals("00:00", LocalTime(0, 0).toString())                 // midnight, round minute
        assertEquals("18:43", LocalTime(18, 43, 0).toString())            // explicit zero seconds dropped
        assertEquals("18:43:05", LocalTime(18, 43, 5).toString())         // non-zero seconds kept
        assertEquals("18:43:00.500", LocalTime(18, 43, 0, 500_000_000).toString()) // frac padded 1->3 digits
        assertEquals("23:59:59.999999999", LocalTime(23, 59, 59, 999_999_999).toString()) // max time
    }

    @Test
    fun parse_roundTripsAndMapsComponents() {
        for (s in listOf("00:00", "18:43", "18:43:05", "23:40:57.120", "23:59:59.999999999")) {
            assertEquals(s, LocalTime.parse(s).toString(), "round-trip identity for $s")
        }
        assertEquals(LocalTime(12, 34), LocalTime.parse("12:34"))
        assertEquals(LocalTime(23, 40, 57, 120_000_000), LocalTime.parse("23:40:57.120"))
    }

    @Test
    fun parse_rejectsOutOfRange_asIllegalArgument() {
        for (bad in listOf("24:00", "12:60", "12:00:60", "noon")) {
            assertFailsWith<IllegalArgumentException>("parse should reject \"$bad\"") { LocalTime.parse(bad) }
        }
    }

    @Test
    fun components_matchKnownTime() {
        val t = LocalTime(23, 59, 59, 999_999_999)
        assertEquals(23, t.hour)
        assertEquals(59, t.minute)
        assertEquals(59, t.second)
        assertEquals(999_999_999, t.nanosecond)
    }

    @Test
    fun constructor_rejectsOutOfRangeComponents() {
        val invalid: List<() -> LocalTime> = listOf(
            { LocalTime(24, 0) },             // hour past 23
            { LocalTime(0, 60) },             // minute past 59
            { LocalTime(0, 0, 60) },          // second past 59
            { LocalTime(0, 0, 0, 1_000_000_000) }, // nanosecond past 999_999_999
            { LocalTime(-1, 0) },             // negative hour
        )
        for ((i, build) in invalid.withIndex()) {
            assertFailsWith<IllegalArgumentException>("invalid case #$i should throw") { build() }
        }
    }

    @Test
    fun orNull_returnsNullForInvalidAndValueForValid() {
        assertNull(LocalTime.orNull(24, 0))
        assertNull(LocalTime.orNull(0, 60))
        assertEquals(LocalTime(23, 59, 59, 999_999_999), LocalTime.orNull(23, 59, 59, 999_999_999))
    }

    // ---- second-of-day is wall-clock position, not elapsed seconds; pinned anchors ----
    @Test
    fun toSecondOfDay_pinnedAnchors() {
        assertEquals(0, LocalTime(0, 0).toSecondOfDay())
        assertEquals(3600, LocalTime(1, 0).toSecondOfDay())
        assertEquals(86399, LocalTime(23, 59, 59).toSecondOfDay())
    }

    @Test
    fun nanosecondOfDay_maxBoundary() {
        assertEquals(86_399_999_999_999L, LocalTime(23, 59, 59, 999_999_999).toNanosecondOfDay())
        assertEquals(0L, LocalTime(0, 0).toNanosecondOfDay())
    }

    // ---- fromSecondOfDay inverts toSecondOfDay and is bounded to [0, 86400) ----
    @Test
    fun fromSecondOfDay_roundTripAndBounds() {
        assertEquals(LocalTime(1, 1, 1), LocalTime.fromSecondOfDay(3661))
        for (t in listOf(LocalTime(0, 0), LocalTime(12, 30, 15), LocalTime(23, 59, 59))) {
            assertEquals(t, LocalTime.fromSecondOfDay(t.toSecondOfDay()), "round trip for $t")
        }
        assertFailsWith<IllegalArgumentException> { LocalTime.fromSecondOfDay(86400) }  // out of range high
        assertFailsWith<IllegalArgumentException> { LocalTime.fromSecondOfDay(-1) }     // out of range low
    }

    @Test
    fun compareTo_ordersWithinDay() {
        assertTrue(LocalTime(0, 0) < LocalTime(0, 0, 0, 1))    // one nanosecond later
        assertTrue(LocalTime(13, 0) < LocalTime(13, 0, 1))
        assertTrue(LocalTime(23, 59, 59, 999_999_999) > LocalTime(0, 0))
        assertEquals(0, LocalTime(12, 34).compareTo(LocalTime(12, 34, 0, 0)))
    }
}
