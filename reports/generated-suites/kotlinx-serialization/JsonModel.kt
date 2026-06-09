/*
 * Generated matrix suite (test-quality benchmark). Shared serializable model.
 *
 * SCOPE: the public Json string format of :kotlinx-serialization-json —
 *   Json.encodeToString / Json.decodeFromString over @Serializable classes,
 *   the JsonElement / JsonObject / JsonArray tree, JsonBuilder config flags
 *   (prettyPrint, encodeDefaults, explicitNulls, ignoreUnknownKeys, classDiscriminator,
 *   allowTrailingComma, allowComments, allowSpecialFloatingPointValues), and the
 *   SerializationException contract on malformed / mismatched / missing input.
 *
 * All expected JSON literals were computed once out-of-band and pinned
 * (see .rex_metrics/verifications.log). Tests assert exception TYPE, never message text.
 */
package kotlinx.serialization.genjson

import kotlinx.serialization.SerialName
import kotlinx.serialization.Serializable

@Serializable
data class Item(val id: Int, val name: String)

@Serializable
data class WithDefault(val name: String, val language: String = "kotlin")

@Serializable
data class Nullable(val name: String, val description: String?)

@Serializable
data class Nested(val item: Item, val tags: List<String>)

@Serializable
data class Holder(val c: Color)

enum class Color { RED, GREEN }

@Serializable
sealed interface Shape

@Serializable
@SerialName("circle")
data class Circle(val r: Int) : Shape

@Serializable
@SerialName("square")
data class Square(val side: Int) : Shape

@Serializable
data class Nums(val l: Long, val u: UInt, val ul: ULong)

enum class Named { VALUE_A, VALUE_B }

@Serializable
data class NamedHolder(val e: Named)

@Serializable
data class Coercible(val name: String = "def", val e: Named = Named.VALUE_A)

@Serializable
data class SingleKey(val key: String)

@Serializable
data class Opt(val a: Int, val b: Int = 99)

@Serializable
data class TwoWords(val firstName: String, val lastName: String)
