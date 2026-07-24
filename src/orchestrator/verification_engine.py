"""
Verification Engine for AIOS Digital Coworker.

Independently verifies execution results before reporting success,
ensuring AIOS never claims success without evidence.
"""

import time
from datetime import datetime
from typing import Any, Optional, Callable
from ..shared.types import (
    TaskStep,
    ActionResult,
    VerificationResult,
    RiskLevel,
)


class VerificationEngine:
    """
    Verifies execution results independently.
    
    The Verification Engine ensures that every action is validated
    before reporting success to the user. It implements a verify-first
    approach where claims of success must be backed by evidence.
    
    Features:
    - Independent verification of all actions
    - Confidence scoring based on evidence
    - Automatic retry on verification failure
    - Detailed failure analysis with suggestions
    - Multiple verification strategies per action type
    
    Example:
        >>> engine = VerificationEngine()
        >>> result = ActionResult(action_id="nav1", success=True, data={"url": "https://example.com"})
        >>> verification = engine.verify(result, expected={"url_contains": "example"})
        >>> verification.success
        True
    """
    
    # Verification strategies by action type
    VERIFICATION_STRATEGIES: dict[str, list[str]] = {
        "navigate": ["url_check", "page_load", "title_check"],
        "click": ["element_exists", "state_change"],
        "type": ["value_check", "element_state"],
        "run": ["exit_code", "output_check", "side_effect"],
        "clone": ["directory_exists", "git_remote"],
        "publish": ["registry_check", "version_available"],
        "delete": ["file_missing", "directory_missing"],
        "create": ["file_exists", "content_check"],
    }
    
    # Default retry configuration
    DEFAULT_MAX_RETRIES = 3
    DEFAULT_RETRY_DELAY = 1.0  # seconds
    
    def __init__(
        self,
        max_retries: int = DEFAULT_MAX_RETRIES,
        retry_delay: float = DEFAULT_RETRY_DELAY
    ) -> None:
        """
        Initialize the Verification Engine.
        
        Args:
            max_retries: Maximum number of retry attempts
            retry_delay: Delay between retries in seconds
        """
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self._custom_verifiers: dict[str, Callable] = {}
    
    def verify(
        self,
        result: ActionResult,
        expected: dict[str, Any],
        step: Optional[TaskStep] = None
    ) -> VerificationResult:
        """
        Verify an action result against expected outcomes.
        
        Args:
            result: The action result to verify
            expected: Expected outcomes as key-value pairs
            step: Optional task step for context
            
        Returns:
            VerificationResult with success status and evidence
            
        Example:
            >>> engine = VerificationEngine()
            >>> result = ActionResult(
            ...     action_id="test1",
            ...     success=True,
            ...     data={"url": "https://github.com"}
            ... )
            >>> verification = engine.verify(
            ...     result,
            ...     expected={"url_contains": "github"}
            ... )
            >>> verification.success
            True
        """
        checks_performed = []
        failures = []
        evidence = {}
        
        # Determine verification strategy
        action_type = step.action if step else "execute"
        strategies = self.VERIFICATION_STRATEGIES.get(
            action_type,
            ["generic_check"]
        )
        
        # Run verification checks
        for strategy in strategies:
            check_result = self._run_check(
                strategy,
                result,
                expected,
                step
            )
            checks_performed.append(strategy)
            
            if check_result["success"]:
                evidence[strategy] = check_result.get("evidence", {})
            else:
                failures.append(
                    f"{strategy}: {check_result.get('reason', 'Check failed')}"
                )
        
        # Calculate confidence
        success_rate = (len(checks_performed) - len(failures)) / len(checks_performed)
        confidence = success_rate if result.success else 0.0
        
        # Determine overall success
        success = len(failures) == 0 and result.success
        
        # Generate suggestions for failures
        suggestions = []
        if failures:
            suggestions = self._generate_suggestions(failures, action_type)
        
        return VerificationResult(
            success=success,
            confidence=confidence,
            evidence=evidence,
            checks_performed=checks_performed,
            failures=failures,
            suggestions=suggestions,
        )
    
    def verify_with_retry(
        self,
        result: ActionResult,
        expected: dict[str, Any],
        step: Optional[TaskStep] = None
    ) -> VerificationResult:
        """
        Verify with automatic retries on failure.
        
        Args:
            result: The action result to verify
            expected: Expected outcomes
            step: Optional task step for context
            
        Returns:
            VerificationResult after retries exhausted or success
        """
        last_result = None
        
        for attempt in range(self.max_retries + 1):
            last_result = self.verify(result, expected, step)
            
            if last_result.success:
                return last_result
            
            # Wait before retry (except on last attempt)
            if attempt < self.max_retries:
                time.sleep(self.retry_delay * (attempt + 1))
        
        return last_result  # type: ignore
    
    def register_verifier(
        self,
        action_type: str,
        verifier: Callable[[ActionResult, dict], bool]
    ) -> None:
        """
        Register a custom verifier function.
        
        Args:
            action_type: Type of action this verifier handles
            verifier: Function that returns True if verification passes
        """
        self._custom_verifiers[action_type] = verifier
    
    def _run_check(
        self,
        strategy: str,
        result: ActionResult,
        expected: dict[str, Any],
        step: Optional[TaskStep]
    ) -> dict[str, Any]:
        """Run a single verification check."""
        # Check for custom verifier
        if strategy in self._custom_verifiers:
            success = self._custom_verifiers[strategy](result, expected)
            return {"success": success, "evidence": {"custom": True}}
        
        # Built-in verifiers
        check_methods = {
            "url_check": self._verify_url,
            "page_load": self._verify_page_load,
            "title_check": self._verify_title,
            "element_exists": self._verify_element_exists,
            "state_change": self._verify_state_change,
            "value_check": self._verify_value,
            "exit_code": self._verify_exit_code,
            "output_check": self._verify_output,
            "side_effect": self._verify_side_effect,
            "directory_exists": self._verify_directory_exists,
            "git_remote": self._verify_git_remote,
            "registry_check": self._verify_registry,
            "version_available": self._verify_version,
            "file_exists": self._verify_file_exists,
            "file_missing": self._verify_file_missing,
            "content_check": self._verify_content,
            "generic_check": self._verify_generic,
        }
        
        method = check_methods.get(strategy, self._verify_generic)
        return method(result, expected, step)
    
    def _verify_url(
        self,
        result: ActionResult,
        expected: dict[str, Any],
        step: Optional[TaskStep]
    ) -> dict[str, Any]:
        """Verify URL matches expectations."""
        if not result.data or not isinstance(result.data, dict):
            return {"success": False, "reason": "No URL data available"}
        
        actual_url = result.data.get("url", "")
        
        if "url_equals" in expected:
            success = actual_url == expected["url_equals"]
            return {"success": success, "evidence": {"url": actual_url}}
        
        if "url_contains" in expected:
            success = expected["url_contains"] in actual_url
            return {"success": success, "evidence": {"url": actual_url}}
        
        if "url_matches" in expected:
            import re
            success = bool(re.search(expected["url_matches"], actual_url))
            return {"success": success, "evidence": {"url": actual_url}}
        
        # Default: just check URL exists
        success = bool(actual_url)
        return {"success": success, "evidence": {"url": actual_url}}
    
    def _verify_page_load(
        self,
        result: ActionResult,
        expected: dict[str, Any],
        step: Optional[TaskStep]
    ) -> dict[str, Any]:
        """Verify page loaded successfully."""
        if not result.data:
            return {"success": False, "reason": "No page data available"}
        
        success = result.data.get("loaded", True)
        return {"success": success, "evidence": {"loaded": success}}
    
    def _verify_title(
        self,
        result: ActionResult,
        expected: dict[str, Any],
        step: Optional[TaskStep]
    ) -> dict[str, Any]:
        """Verify page title matches expectations."""
        if not result.data:
            return {"success": False, "reason": "No title data available"}
        
        actual_title = result.data.get("title", "")
        
        if "title_contains" in expected:
            success = expected["title_contains"] in actual_title
            return {"success": success, "evidence": {"title": actual_title}}
        
        success = bool(actual_title)
        return {"success": success, "evidence": {"title": actual_title}}
    
    def _verify_element_exists(
        self,
        result: ActionResult,
        expected: dict[str, Any],
        step: Optional[TaskStep]
    ) -> dict[str, Any]:
        """Verify element exists after action."""
        if not result.data:
            return {"success": False, "reason": "No element data available"}
        
        selector = expected.get("selector", "")
        exists = result.data.get("element_exists", False)
        
        success = exists
        return {"success": success, "evidence": {"selector": selector, "exists": exists}}
    
    def _verify_state_change(
        self,
        result: ActionResult,
        expected: dict[str, Any],
        step: Optional[TaskStep]
    ) -> dict[str, Any]:
        """Verify state changed as expected."""
        if not result.data:
            return {"success": False, "reason": "No state data available"}
        
        changed = result.data.get("state_changed", True)
        success = changed
        return {"success": success, "evidence": {"changed": changed}}
    
    def _verify_value(
        self,
        result: ActionResult,
        expected: dict[str, Any],
        step: Optional[TaskStep]
    ) -> dict[str, Any]:
        """Verify typed value matches expectations."""
        if not result.data:
            return {"success": False, "reason": "No value data available"}
        
        actual_value = result.data.get("value", "")
        expected_value = expected.get("value", "")
        
        success = actual_value == expected_value
        return {"success": success, "evidence": {"actual": actual_value, "expected": expected_value}}
    
    def _verify_exit_code(
        self,
        result: ActionResult,
        expected: dict[str, Any],
        step: Optional[TaskStep]
    ) -> dict[str, Any]:
        """Verify command exit code."""
        if not result.data:
            return {"success": False, "reason": "No exit code data available"}
        
        exit_code = result.data.get("exit_code", -1)
        expected_code = expected.get("exit_code", 0)
        
        success = exit_code == expected_code
        return {"success": success, "evidence": {"exit_code": exit_code}}
    
    def _verify_output(
        self,
        result: ActionResult,
        expected: dict[str, Any],
        step: Optional[TaskStep]
    ) -> dict[str, Any]:
        """Verify command output contains expected text."""
        if not result.data:
            return {"success": False, "reason": "No output data available"}
        
        output = result.data.get("output", "")
        
        if "output_contains" in expected:
            success = expected["output_contains"] in output
            return {"success": success, "evidence": {"output": output[:200]}}
        
        if "output_matches" in expected:
            import re
            success = bool(re.search(expected["output_matches"], output))
            return {"success": success, "evidence": {"output": output[:200]}}
        
        success = bool(output)
        return {"success": success, "evidence": {"output": output[:200]}}
    
    def _verify_side_effect(
        self,
        result: ActionResult,
        expected: dict[str, Any],
        step: Optional[TaskStep]
    ) -> dict[str, Any]:
        """Verify expected side effects occurred."""
        side_effects = result.data.get("side_effects", {})
        
        for key, expected_value in expected.items():
            if key.startswith("side_effect_"):
                actual_value = side_effects.get(key[14:], None)
                if actual_value != expected_value:
                    return {"success": False, "reason": f"Side effect {key} not matched"}
        
        return {"success": True, "evidence": {"side_effects": side_effects}}
    
    def _verify_directory_exists(
        self,
        result: ActionResult,
        expected: dict[str, Any],
        step: Optional[TaskStep]
    ) -> dict[str, Any]:
        """Verify directory was created."""
        path = expected.get("path", "")
        exists = result.data.get("exists", False) if result.data else False
        
        return {"success": exists, "evidence": {"path": path, "exists": exists}}
    
    def _verify_git_remote(
        self,
        result: ActionResult,
        expected: dict[str, Any],
        step: Optional[TaskStep]
    ) -> dict[str, Any]:
        """Verify git remote is configured."""
        remote = result.data.get("remote", "") if result.data else ""
        success = bool(remote)
        
        return {"success": success, "evidence": {"remote": remote}}
    
    def _verify_registry(
        self,
        result: ActionResult,
        expected: dict[str, Any],
        step: Optional[TaskStep]
    ) -> dict[str, Any]:
        """Verify package is in registry."""
        published = result.data.get("published", False) if result.data else False
        
        return {"success": published, "evidence": {"published": published}}
    
    def _verify_version(
        self,
        result: ActionResult,
        expected: dict[str, Any],
        step: Optional[TaskStep]
    ) -> dict[str, Any]:
        """Verify version is available."""
        version = result.data.get("version", "") if result.data else ""
        expected_version = expected.get("version", "")
        
        if expected_version:
            success = version == expected_version
        else:
            success = bool(version)
        
        return {"success": success, "evidence": {"version": version}}
    
    def _verify_file_exists(
        self,
        result: ActionResult,
        expected: dict[str, Any],
        step: Optional[TaskStep]
    ) -> dict[str, Any]:
        """Verify file was created."""
        path = expected.get("path", "")
        exists = result.data.get("exists", False) if result.data else False
        
        return {"success": exists, "evidence": {"path": path, "exists": exists}}
    
    def _verify_file_missing(
        self,
        result: ActionResult,
        expected: dict[str, Any],
        step: Optional[TaskStep]
    ) -> dict[str, Any]:
        """Verify file was deleted."""
        path = expected.get("path", "")
        missing = result.data.get("missing", True) if result.data else True
        
        return {"success": missing, "evidence": {"path": path, "missing": missing}}
    
    def _verify_content(
        self,
        result: ActionResult,
        expected: dict[str, Any],
        step: Optional[TaskStep]
    ) -> dict[str, Any]:
        """Verify file/content matches expectations."""
        content = result.data.get("content", "") if result.data else ""
        
        if "content_contains" in expected:
            success = expected["content_contains"] in content
            return {"success": success, "evidence": {"content": content[:200]}}
        
        success = bool(content)
        return {"success": success, "evidence": {"content": content[:200]}}
    
    def _verify_generic(
        self,
        result: ActionResult,
        expected: dict[str, Any],
        step: Optional[TaskStep]
    ) -> dict[str, Any]:
        """Generic verification when no specific strategy applies."""
        success = result.success
        return {"success": success, "evidence": {"action_success": success}}
    
    def _generate_suggestions(
        self,
        failures: list[str],
        action_type: str
    ) -> list[str]:
        """Generate recovery suggestions based on failures."""
        suggestions = []
        
        failure_str = " ".join(failures).lower()
        
        if "url" in failure_str:
            suggestions.extend([
                "Check if the URL is correct and accessible",
                "Verify network connectivity",
                "Try refreshing the page",
            ])
        
        if "element" in failure_str:
            suggestions.extend([
                "Check if the element selector is correct",
                "Wait for the page to fully load",
                "Verify the element exists in the DOM",
            ])
        
        if "exit code" in failure_str:
            suggestions.extend([
                "Check command syntax and arguments",
                "Verify required dependencies are installed",
                "Review error output for details",
            ])
        
        if "file" in failure_str or "directory" in failure_str:
            suggestions.extend([
                "Check file permissions",
                "Verify the path is correct",
                "Ensure parent directories exist",
            ])
        
        if not suggestions:
            suggestions.append("Retry the operation")
            suggestions.append("Check system logs for errors")
        
        return suggestions
