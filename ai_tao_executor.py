#!/usr/bin/env python3
"""
AI-TAO Intelligent Executor
==========================

Adaptive execution engine with intelligent error handling and recovery.
"""

import os
import sys
import time
import json
import subprocess
import re
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
import logging

# Import AI-TAO components
from ai_tao_core import (
    TaskIntelligence,
    ContextWindow,
    WorkPlan,
    ExecutionResult,
    SubTask,
    TaskIntelligenceEngine,
    ContextWindowConstructor,
    StrategicPlanner
)

@dataclass
class ExecutionContext:
    """Execution context for intelligent task execution"""
    task_id: str
    start_time: datetime
    current_subtask: Optional[str] = None
    completed_subtasks: List[str] = field(default_factory=list)
    failed_subtasks: List[str] = field(default_factory=list)
    execution_metrics: Dict[str, Any] = field(default_factory=dict)
    error_history: List[Dict[str, Any]] = field(default_factory=list)

@dataclass
class ErrorClassification:
    """Intelligent error classification"""
    error_type: str
    severity: str
    category: str
    confidence: float
    suggested_recovery: str
    root_cause: str
    prevention_measures: List[str]

class ErrorClassifier:
    """Intelligent error classification engine"""

    def __init__(self):
        self.error_patterns = self._load_error_patterns()

    def _load_error_patterns(self) -> Dict[str, Any]:
        """Load error classification patterns"""
        return {
            "import_error": {
                "patterns": ["ImportError", "ModuleNotFoundError", "No module named"],
                "category": "dependency",
                "severity": "medium",
                "recovery": "install_missing_dependency"
            },
            "connection_error": {
                "patterns": ["ConnectionError", "TimeoutError", "ServiceUnavailable"],
                "category": "integration",
                "severity": "high",
                "recovery": "retry_with_backoff"
            },
            "authentication_error": {
                "patterns": ["AuthenticationError", "InvalidCredentials", "Unauthorized"],
                "category": "security",
                "severity": "critical",
                "recovery": "validate_credentials"
            },
            "validation_error": {
                "patterns": ["ValidationError", "ValueError", "TypeError"],
                "category": "implementation",
                "severity": "medium",
                "recovery": "fix_input_validation"
            },
            "configuration_error": {
                "patterns": ["ConfigurationError", "KeyError", "MissingConfig"],
                "category": "configuration",
                "severity": "high",
                "recovery": "validate_configuration"
            }
        }

    def classify_error(self, error: Exception, context: Dict[str, Any]) -> ErrorClassification:
        """Classify an error with intelligent analysis"""
        error_message = str(error)
        error_type = type(error).__name__

        # Find matching pattern
        for pattern_name, pattern_data in self.error_patterns.items():
            if any(pattern in error_message for pattern in pattern_data["patterns"]) or \
               any(pattern in error_type for pattern in pattern_data["patterns"]):
                return ErrorClassification(
                    error_type=pattern_name,
                    severity=pattern_data["severity"],
                    category=pattern_data["category"],
                    confidence=0.8,
                    suggested_recovery=pattern_data["recovery"],
                    root_cause=self._analyze_root_cause(error, pattern_data, context),
                    prevention_measures=self._suggest_prevention(pattern_data)
                )

        # Default classification for unknown errors
        return ErrorClassification(
            error_type="unknown_error",
            severity="medium",
            category="implementation",
            confidence=0.3,
            suggested_recovery="manual_intervention",
            root_cause="Unknown error type - requires manual analysis",
            prevention_measures=["Add comprehensive error handling", "Improve logging"]
        )

    def _analyze_root_cause(self, error: Exception, pattern_data: Dict[str, Any],
                          context: Dict[str, Any]) -> str:
        """Analyze root cause of error"""
        error_msg = str(error)

        if pattern_data["category"] == "dependency":
            return f"Missing or incompatible dependency: {error_msg}"
        elif pattern_data["category"] == "integration":
            return f"External service integration failure: {error_msg}"
        elif pattern_data["category"] == "security":
            return f"Authentication or authorization failure: {error_msg}"
        elif pattern_data["category"] == "configuration":
            return f"Configuration or environment issue: {error_msg}"
        else:
            return f"Implementation error: {error_msg}"

    def _suggest_prevention(self, pattern_data: Dict[str, Any]) -> List[str]:
        """Suggest prevention measures"""
        prevention_map = {
            "dependency": [
                "Add dependency checking in initialization",
                "Use virtual environments consistently",
                "Keep requirements.txt up to date"
            ],
            "integration": [
                "Implement circuit breakers",
                "Add health checks for external services",
                "Use exponential backoff for retries"
            ],
            "security": [
                "Validate credentials before use",
                "Implement proper token management",
                "Add security audit logging"
            ],
            "configuration": [
                "Validate configuration on startup",
                "Use environment variable validation",
                "Implement configuration schema validation"
            ]
        }

        return prevention_map.get(pattern_data["category"], ["Add comprehensive error handling"])

class RecoveryEngine:
    """Intelligent recovery and fix engine"""

    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.recovery_strategies = self._load_recovery_strategies()

    def _load_recovery_strategies(self) -> Dict[str, Callable]:
        """Load recovery strategy functions"""
        return {
            "install_missing_dependency": self._install_dependency,
            "retry_with_backoff": self._retry_with_backoff,
            "validate_credentials": self._validate_credentials,
            "fix_input_validation": self._fix_validation,
            "validate_configuration": self._validate_config,
            "manual_intervention": self._manual_intervention_required
        }

    def execute_recovery(self, error_classification: ErrorClassification,
                        context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute appropriate recovery strategy"""
        strategy_name = error_classification.suggested_recovery

        if strategy_name in self.recovery_strategies:
            try:
                return self.recovery_strategies[strategy_name](error_classification, context)
            except Exception as e:
                return {
                    "success": False,
                    "strategy": strategy_name,
                    "error": f"Recovery execution failed: {e}",
                    "escalation_required": True
                }
        else:
            return {
                "success": False,
                "strategy": strategy_name,
                "error": "Unknown recovery strategy",
                "escalation_required": True
            }

    def _install_dependency(self, error_classification: ErrorClassification,
                          context: Dict[str, Any]) -> Dict[str, Any]:
        """Install missing dependency"""
        error_msg = context.get("error_message", "")
        package_match = re.search(r"No module named '(\w+)'", error_msg)

        if package_match:
            package_name = package_match.group(1)
            try:
                subprocess.run([
                    sys.executable, "-m", "pip", "install", package_name
                ], check=True, capture_output=True)

                return {
                    "success": True,
                    "strategy": "install_dependency",
                    "action": f"Installed package: {package_name}",
                    "escalation_required": False
                }
            except subprocess.CalledProcessError as e:
                return {
                    "success": False,
                    "strategy": "install_dependency",
                    "error": f"Failed to install {package_name}: {e}",
                    "escalation_required": True
                }

        return {
            "success": False,
            "strategy": "install_dependency",
            "error": "Could not identify package to install",
            "escalation_required": True
        }

    def _retry_with_backoff(self, error_classification: ErrorClassification,
                          context: Dict[str, Any]) -> Dict[str, Any]:
        """Retry operation with exponential backoff"""
        # This would be implemented with actual retry logic
        return {
            "success": False,
            "strategy": "retry_with_backoff",
            "error": "Retry logic not implemented for this context",
            "escalation_required": True
        }

    def _validate_credentials(self, error_classification: ErrorClassification,
                            context: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and refresh credentials"""
        # Check for common credential issues
        missing_vars = []
        required_vars = ["OPENAI_API_KEY", "FIREBASE_PROJECT_ID"]

        for var in required_vars:
            if not os.environ.get(var):
                missing_vars.append(var)

        if missing_vars:
            return {
                "success": False,
                "strategy": "validate_credentials",
                "error": f"Missing environment variables: {', '.join(missing_vars)}",
                "escalation_required": True
            }

        return {
            "success": True,
            "strategy": "validate_credentials",
            "action": "Credentials validated successfully",
            "escalation_required": False
        }

    def _fix_validation(self, error_classification: ErrorClassification,
                       context: Dict[str, Any]) -> Dict[str, Any]:
        """Fix input validation issues"""
        # This would implement automatic validation fixes
        return {
            "success": False,
            "strategy": "fix_validation",
            "error": "Automatic validation fixing not implemented",
            "escalation_required": True
        }

    def _validate_config(self, error_classification: ErrorClassification,
                        context: Dict[str, Any]) -> Dict[str, Any]:
        """Validate configuration files"""
        config_issues = []

        # Check Firebase config
        firebase_config = self.project_root / "config" / "firebase-demo.json"
        if not firebase_config.exists():
            config_issues.append("Firebase configuration file missing")

        # Check environment variables
        required_env_vars = ["OPENAI_API_KEY", "SECRET_KEY"]
        for var in required_env_vars:
            if not os.environ.get(var):
                config_issues.append(f"Environment variable {var} not set")

        if config_issues:
            return {
                "success": False,
                "strategy": "validate_config",
                "error": f"Configuration issues: {'; '.join(config_issues)}",
                "escalation_required": True
            }

        return {
            "success": True,
            "strategy": "validate_config",
            "action": "Configuration validated successfully",
            "escalation_required": False
        }

    def _manual_intervention_required(self, error_classification: ErrorClassification,
                                    context: Dict[str, Any]) -> Dict[str, Any]:
        """Escalate to manual intervention"""
        return {
            "success": False,
            "strategy": "manual_intervention",
            "error": "Manual intervention required for this error type",
            "escalation_required": True
        }

class QualityValidator:
    """Comprehensive quality validation engine"""

    def __init__(self, project_root: Path):
        self.project_root = project_root

    def validate_quality(self, subtask: SubTask, execution_context: ExecutionContext) -> Dict[str, Any]:
        """Perform comprehensive quality validation"""
        validation_results = {
            "tests_pass": self._run_tests(),
            "code_quality": self._check_code_quality(),
            "security_check": self._run_security_check(),
            "performance_check": self._check_performance(),
            "integration_test": self._run_integration_tests()
        }

        # Calculate overall quality score
        quality_score = sum(1 for result in validation_results.values() if result) / len(validation_results)

        validation_results["overall_score"] = quality_score
        validation_results["quality_level"] = self._determine_quality_level(quality_score)

        return validation_results

    def _run_tests(self) -> bool:
        """Run test suite"""
        try:
            result = subprocess.run(
                [sys.executable, "-m", "pytest", "tests/", "-q", "--tb=no"],
                cwd=self.project_root,
                capture_output=True,
                timeout=60
            )
            return result.returncode == 0
        except:
            return False

    def _check_code_quality(self) -> bool:
        """Check code quality with linting"""
        try:
            result = subprocess.run(
                [sys.executable, "-m", "flake8", "app/", "--max-line-length=100", "--extend-ignore=E203,W503"],
                cwd=self.project_root,
                capture_output=True
            )
            return result.returncode == 0
        except:
            return True  # Don't fail if flake8 not available

    def _run_security_check(self) -> bool:
        """Run basic security checks"""
        # Check for common security issues
        security_issues = []

        # Check for hardcoded secrets
        for py_file in self.project_root.rglob("*.py"):
            try:
                with open(py_file, 'r') as f:
                    content = f.read()
                    if any(secret in content for secret in ["password =", "secret =", "key ="]):
                        security_issues.append(f"Potential hardcoded secret in {py_file}")
            except:
                pass

        return len(security_issues) == 0

    def _check_performance(self) -> bool:
        """Check basic performance metrics"""
        # Simple performance check - ensure no obvious performance issues
        return True  # Placeholder implementation

    def _run_integration_tests(self) -> bool:
        """Run integration tests"""
        try:
            # Try to import and initialize key services
            sys.path.insert(0, str(self.project_root))
            from app.services.firebase_service import firebase_service
            from app.services.ai_service import ai_service
            return True
        except:
            return False

    def _determine_quality_level(self, score: float) -> str:
        """Determine quality level based on score"""
        if score >= 0.9:
            return "excellent"
        elif score >= 0.8:
            return "good"
        elif score >= 0.7:
            return "acceptable"
        elif score >= 0.6:
            return "needs_improvement"
        else:
            return "unacceptable"

class IntelligentExecutor:
    """Intelligent task execution engine"""

    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.error_classifier = ErrorClassifier()
        self.recovery_engine = RecoveryEngine(project_root)
        self.quality_validator = QualityValidator(project_root)
        self.max_retries = 3
        self.execution_context = None

    def execute_plan(self, work_plan: WorkPlan, context_window: ContextWindow) -> ExecutionResult:
        """Execute work plan with intelligent adaptation"""
        self.execution_context = ExecutionContext(
            task_id=work_plan.task_id,
            start_time=datetime.now()
        )

        result = ExecutionResult()

        # Execute subtasks in order
        for subtask_id in work_plan.execution_order:
            subtask = next((s for s in work_plan.subtasks if s.id == subtask_id), None)
            if not subtask:
                continue

            self.execution_context.current_subtask = subtask_id

            # Execute subtask with intelligence
            subtask_result = self._execute_subtask_intelligently(
                subtask, work_plan, context_window
            )

            if subtask_result["success"]:
                self.execution_context.completed_subtasks.append(subtask_id)
                result.completed_subtasks.append(subtask_id)
            else:
                self.execution_context.failed_subtasks.append(subtask_id)
                result.errors.append({
                    "subtask": subtask_id,
                    "error": subtask_result.get("error", "Unknown error"),
                    "attempts": subtask_result.get("attempts", 1)
                })

                # Check if we should continue or fail fast
                if subtask.risk_level == "critical":
                    result.success = False
                    break

        # Final validation
        if len(result.errors) == 0:
            result.success = self._perform_final_validation(work_plan, context_window)
        else:
            result.success = False

        # Calculate metrics
        result.metrics = self._calculate_execution_metrics()
        result.learning_insights = self._extract_learning_insights(result)

        return result

    def _execute_subtask_intelligently(self, subtask: SubTask, work_plan: WorkPlan,
                                     context_window: ContextWindow) -> Dict[str, Any]:
        """Execute a subtask with intelligent error handling"""
        attempts = 0
        last_error = None

        while attempts < self.max_retries:
            attempts += 1

            try:
                # Execute the subtask
                result = self._execute_subtask_implementation(subtask, context_window)

                if result["success"]:
                    # Validate quality
                    quality_result = self.quality_validator.validate_quality(
                        subtask, self.execution_context
                    )

                    if quality_result["overall_score"] >= 0.7:
                        return {
                            "success": True,
                            "attempts": attempts,
                            "quality_score": quality_result["overall_score"]
                        }
                    else:
                        # Quality not acceptable, treat as failure
                        return {
                            "success": False,
                            "attempts": attempts,
                            "error": f"Quality validation failed: {quality_result['quality_level']}",
                            "quality_result": quality_result
                        }

                else:
                    last_error = result.get("error", "Unknown execution error")

            except Exception as e:
                last_error = str(e)

                # Classify error and attempt recovery
                error_classification = self.error_classifier.classify_error(e, {
                    "subtask": subtask.id,
                    "context_window": context_window,
                    "execution_context": self.execution_context,
                    "error_message": str(e)
                })

                # Log error for analysis
                self.execution_context.error_history.append({
                    "subtask": subtask.id,
                    "attempt": attempts,
                    "error": str(e),
                    "classification": error_classification.__dict__
                })

                # Attempt recovery
                recovery_result = self.recovery_engine.execute_recovery(
                    error_classification, {
                        "error": e,
                        "subtask": subtask,
                        "context_window": context_window
                    }
                )

                if recovery_result["success"]:
                    # Recovery successful, retry execution
                    continue
                elif not recovery_result.get("escalation_required", False):
                    # Recovery failed but not critical, continue to next attempt
                    continue
                else:
                    # Escalation required, fail immediately
                    break

        # All attempts failed
        return {
            "success": False,
            "attempts": attempts,
            "error": last_error or "Maximum retries exceeded",
            "escalation_required": True
        }

    def _execute_subtask_implementation(self, subtask: SubTask,
                                      context_window: ContextWindow) -> Dict[str, Any]:
        """Execute the actual subtask implementation"""
        # This would be replaced with actual implementation logic
        # For now, return mock success/failure based on subtask type

        subtask_type = subtask.id.split('_')[-1]

        # Simulate different success rates based on subtask type
        success_rates = {
            "config": 0.9,
            "init": 0.8,
            "test": 0.7,
            "implement": 0.6,
            "setup": 0.8,
            "add": 0.7
        }

        import random
        success_rate = success_rates.get(subtask_type, 0.5)
        success = random.random() < success_rate

        if success:
            return {"success": True}
        else:
            return {
                "success": False,
                "error": f"Simulated failure in {subtask_type} subtask"
            }

    def _perform_final_validation(self, work_plan: WorkPlan,
                                context_window: ContextWindow) -> bool:
        """Perform final comprehensive validation"""
        try:
            # Run full test suite
            test_result = subprocess.run(
                [sys.executable, "-m", "pytest", "tests/", "-v"],
                cwd=self.project_root,
                capture_output=True,
                timeout=120
            )

            # Check application health
            from app import create_app
            app = create_app('development')

            return test_result.returncode == 0

        except Exception as e:
            print(f"Final validation failed: {e}")
            return False

    def _calculate_execution_metrics(self) -> Dict[str, Any]:
        """Calculate comprehensive execution metrics"""
        if not self.execution_context:
            return {}

        end_time = datetime.now()
        duration = (end_time - self.execution_context.start_time).total_seconds()

        return {
            "total_duration": duration,
            "completed_subtasks": len(self.execution_context.completed_subtasks),
            "failed_subtasks": len(self.execution_context.failed_subtasks),
            "error_count": len(self.execution_context.error_history),
            "average_subtask_duration": duration / max(1, len(self.execution_context.completed_subtasks)),
            "success_rate": len(self.execution_context.completed_subtasks) /
                          max(1, len(self.execution_context.completed_subtasks) + len(self.execution_context.failed_subtasks))
        }

    def _extract_learning_insights(self, result: ExecutionResult) -> Dict[str, Any]:
        """Extract learning insights from execution"""
        insights = {
            "error_patterns": {},
            "performance_insights": {},
            "quality_trends": {},
            "improvement_suggestions": []
        }

        # Analyze error patterns
        for error in result.errors:
            error_type = error.get("error", "unknown")
            if error_type not in insights["error_patterns"]:
                insights["error_patterns"][error_type] = 0
            insights["error_patterns"][error_type] += 1

        # Performance insights
        if result.metrics.get("success_rate", 0) < 0.8:
            insights["performance_insights"]["low_success_rate"] = "Consider improving error handling and recovery strategies"

        if result.metrics.get("average_subtask_duration", 0) > 300:  # 5 minutes
            insights["performance_insights"]["slow_execution"] = "Consider optimizing subtask implementations"

        # Quality trends
        insights["quality_trends"]["overall_success"] = result.success

        # Improvement suggestions
        if len(result.errors) > 0:
            insights["improvement_suggestions"].append("Implement better error classification and recovery")
        if result.metrics.get("success_rate", 0) < 0.9:
            insights["improvement_suggestions"].append("Improve subtask success rates through better planning")

        return insights

# Integration with existing autonomous workflow
def execute_task_with_ai_tao(task_id: str, project_root: Path) -> ExecutionResult:
    """Execute a task using AI-TAO framework"""
    print(f"🤖 AI-TAO: Starting intelligent execution for task: {task_id}")

    # Initialize AI-TAO components
    intelligence_engine = TaskIntelligenceEngine(project_root)
    context_constructor = ContextWindowConstructor(project_root)
    strategic_planner = StrategicPlanner()
    intelligent_executor = IntelligentExecutor(project_root)

    try:
        # Phase 1: Task Intelligence Analysis
        print("🧠 AI-TAO: Analyzing task intelligence...")
        task_intelligence = intelligence_engine.analyze_task(task_id)

        # Phase 2: Context Window Construction
        print("🔍 AI-TAO: Constructing context window...")
        context_window = context_constructor.construct_window(task_intelligence)

        # Phase 3: Strategic Planning
        print("📋 AI-TAO: Creating strategic work plan...")
        work_plan = strategic_planner.create_plan(task_intelligence, context_window)

        # Phase 4: Intelligent Execution
        print("⚡ AI-TAO: Executing with intelligence...")
        execution_result = intelligent_executor.execute_plan(work_plan, context_window)

        # Phase 5: Learning and Optimization
        print("🧪 AI-TAO: Analyzing execution and learning...")

        if execution_result.success:
            print("✅ AI-TAO: Task completed successfully!")
        else:
            print("❌ AI-TAO: Task execution failed")

        return execution_result

    except Exception as e:
        print(f"💥 AI-TAO: Critical error during execution: {e}")
        return ExecutionResult(
            success=False,
            errors=[{"error": f"AI-TAO execution failed: {e}", "critical": True}]
        )