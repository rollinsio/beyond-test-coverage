package com.github.michaelbull.result

import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertNull
import kotlin.test.fail

/**
 * The transform / combinator surface: map family, and/or, andThen/orElse,
 * recover, and the on-side-effect hooks. Each test pins the transformed value
 * (a fixed literal) and checks the *other* branch is passed through untouched —
 * behaviour, never a constructor read-back.
 */
class ResultOpsTest {

    // ── map / mapError: transform one branch, pass the other through ─────────
    @Test
    fun mapTransformsOkValue() {
        assertEquals("HELLO, WORLD!", Ok("hello, world!").map { it.uppercase() }.get())
    }

    @Test
    fun mapLeavesErrUnchanged() {
        val err: Result<String, String> = Err("the-untouched-err")
        assertEquals("the-untouched-err", err.map { it.uppercase() }.getError())
    }

    @Test
    fun mapErrorTransformsErrValue() {
        assertEquals("ERR: not-found!", Err("not-found!").mapError { "ERR: $it" }.getError())
    }

    @Test
    fun mapErrorLeavesOkUnchanged() {
        assertEquals("the-untouched-ok!", Ok("the-untouched-ok!").mapError { "unused" }.get())
    }

    // ── flatMap / flatten / transpose ────────────────────────────────────────
    @Test
    fun flatMapChainsThroughOk() {
        assertEquals(12, Ok("twelve-chars").flatMap { Ok(it.length) }.get())
    }

    @Test
    fun flattenUnwrapsNestedOk() {
        assertEquals("the-inner-value!", Ok(Ok("the-inner-value!")).flatten().get())
    }

    @Test
    fun flattenPropagatesInnerErr() {
        val nested: Result<Result<Int, String>, String> = Ok(Err("the-inner-error"))
        assertEquals("the-inner-error", nested.flatten().getError())
    }

    @Test
    fun transposeOkNullCollapsesToNull() {
        val result: Result<String?, String> = Ok(null)
        assertNull(result.transpose())
    }

    @Test
    fun transposeOkValueStaysOk() {
        val result: Result<String?, String> = Ok("the-present-value")
        assertEquals("the-present-value", result.transpose()?.get())
    }

    // ── mapBoth: collapse to U via the matching branch ───────────────────────
    @Test
    fun mapBothSelectsSuccessBranchForOk() {
        assertEquals("ok:the-value-here", Ok("the-value-here").mapBoth({ "ok:$it" }, { "err:$it" }))
    }

    @Test
    fun mapBothSelectsFailureBranchForErr() {
        assertEquals("err:the-error-her", Err("the-error-her").mapBoth({ "ok:$it" }, { "err:$it" }))
    }

    // ── and / andThen: sequence, short-circuiting on the first Err ───────────
    @Test
    fun andReturnsSecondResultWhenFirstIsOk() {
        val first: Result<String, String> = Ok("first")
        val second: Result<String, String> = Ok("second-value-x!")
        assertEquals("second-value-x!", (first and second).get())
    }

    @Test
    fun andShortCircuitsOnFirstErr() {
        val first: Result<Int, String> = Err("the-first-error")
        val second: Result<Int, String> = Ok(2)
        assertEquals("the-first-error", (first and second).getError())
    }

    @Test
    fun andThenChainsOnOk() {
        assertEquals("CHAINED-VALUE!", Ok("chained-value!").andThen { Ok(it.uppercase()) }.get())
    }

    @Test
    fun andThenShortCircuitsOnErr() {
        val start: Result<String, String> = Err("upstream-error")
        assertEquals("upstream-error", start.andThen { Ok(it.length) }.getError())
    }

    // ── or / orElse: alternatives taken only on Err ──────────────────────────
    @Test
    fun orReturnsSelfWhenOk() {
        val a: Result<String, String> = Ok("the-primary-ok!")
        val b: Result<String, String> = Ok("the-secondary!")
        assertEquals("the-primary-ok!", (a or b).get())
    }

    @Test
    fun orReturnsAlternativeWhenErr() {
        val a: Result<String, String> = Err("primary-failed")
        val b: Result<String, String> = Ok("the-secondary!!")
        assertEquals("the-secondary!!", (a or b).get())
    }

    @Test
    fun orElseTransformsErrToRecoveredResult() {
        assertEquals("recovered-by-else", Err("err").orElse { Ok("recovered-by-else") }.get())
    }

    @Test
    fun orElseKeepsOkValueNotTheAlternative() {
        val ok: Result<String, String> = Ok("the-original-okk")
        assertEquals("the-original-okk", ok.orElse { Ok("the-unused-fallbk") }.get())
    }

    // ── recover / recoverIf: Err → Ok, conditionally ─────────────────────────
    @Test
    fun recoverConvertsErrToOk() {
        assertEquals("recovered-value!", Err("boom").recover { "recovered-value!" }.get())
    }

    @Test
    fun recoverLeavesOkWithoutCallingTransform() {
        assertEquals("the-original-okv", Ok("the-original-okv").recover { fail("recover ran on Ok") }.get())
    }

    @Test
    fun recoverIfTransformsOnlyWhenPredicateHolds() {
        val recovered = Err("retryable").recoverIf({ it == "retryable" }, { "default-value-x" })
        assertEquals("default-value-x", recovered.get())
    }

    @Test
    fun recoverIfKeepsErrWhenPredicateFails() {
        val kept = Err("fatal-error-xx").recoverIf({ it == "retryable" }, { "unused" })
        assertEquals("fatal-error-xx", kept.getError())
    }

    // ── onOk / onErr: side-effect hooks fire on one branch, return self ──────
    @Test
    fun onOkRunsActionForOkAndReturnsSelf() {
        var seen: String? = null
        val result = Ok("the-observed-value").onOk { seen = it }
        assertEquals("the-observed-value", seen)
        assertEquals("the-observed-value", result.get())
    }

    @Test
    fun onOkSkipsActionForErr() {
        Err("boom").onOk { fail("onOk ran on Err") }
    }

    @Test
    fun onErrRunsActionForErrAndReturnsSelf() {
        var seen: String? = null
        val result = Err("the-observed-error").onErr { seen = it }
        assertEquals("the-observed-error", seen)
        assertEquals("the-observed-error", result.getError())
    }

    @Test
    fun onErrSkipsActionForOk() {
        Ok("value").onErr { fail("onErr ran on Ok") }
    }
}
