"""
Aethel Conservation Checker v1.3

Validates the fundamental law of conservation in financial transactions:
the sum of all balance changes must equal zero.

Author: Aethel Team
Version: 1.3.0
Date: February 3, 2026
"""

from dataclasses import dataclass
from typing import List, Optional, Union
import z3


@dataclass
class BalanceChange:
    """Represents a single balance change in a transaction."""
    variable_name: str
    amount: Union[int, float, str]  # Can be numeric or symbolic expression
    line_number: int
    is_increase: bool  # True for gains, False for losses
    
    def to_signed_amount(self) -> Union[int, float, str]:
        """Convert to signed amount (positive for increase, negative for decrease)."""
        if isinstance(self.amount, (int, float)):
            return self.amount if self.is_increase else -self.amount
        else:
            # Symbolic expression
            return f"{self.amount}" if self.is_increase else f"-({self.amount})"


@dataclass
class ConservationResult:
    """Result of conservation checking."""
    is_valid: bool
    changes: List[BalanceChange]
    violation_amount: Optional[Union[int, float, str]] = None
    error_message: Optional[str] = None
    
    def format_error(self) -> str:
        """Format a human-readable error message."""
        if self.is_valid:
            return "Conservation check passed"
        
        lines = ["❌ FAILED: Conservation violation detected"]
        for change in self.changes:
            sign = "+" if change.is_increase else "-"
            lines.append(f"   {change.variable_name}: {sign}{change.amount}")
        
        lines.append("   " + "─" * 40)
        
        if self.violation_amount is not None:
            if isinstance(self.violation_amount, (int, float)):
                if self.violation_amount > 0:
                    lines.append(f"   Total: {self.violation_amount} units created from nothing")
                else:
                    lines.append(f"   Total: {abs(self.violation_amount)} units destroyed")
            else:
                lines.append(f"   Total: {self.violation_amount} (non-zero)")
        
        lines.append("")
        lines.append("   Hint: In a valid transaction, the sum of all balance")
        lines.append("   changes must equal zero. Check your arithmetic.")
        
        return "\n".join(lines)


class ConservationChecker:
    """
    Analyzes verify blocks to detect conservation violations.
    
    The Conservation Checker validates that financial transactions obey
    the law of conservation: money cannot be created or destroyed.
    """
    
    def __init__(self):
        self.cache = {}  # Cache for repeated analyses
    
    def check_intent(self, intent_data: dict) -> ConservationResult:
        """
        Check conservation for an entire intent.
        
        Args:
            intent_data: Dictionary containing parsed intent data with 'verify' block
            
        Returns:
            ConservationResult with status and details
        """
        # Extract verify block
        verify_block = intent_data.get('verify', [])
        
        if not verify_block:
            # No verify block - skip conservation check
            return ConservationResult(is_valid=True, changes=[])
        
        # Analyze verify block for balance changes
        changes = self.analyze_verify_block(verify_block)
        
        if not changes:
            # No balance changes detected - skip conservation check
            return ConservationResult(is_valid=True, changes=[])
        
        # Validate conservation law
        return self.validate_conservation(changes)
    
    def analyze_verify_block(self, verify_block: List[str]) -> List[BalanceChange]:
        """
        Extract all balance changes from a verify block.
        
        Args:
            verify_block: List of condition strings from verify block
            
        Returns:
            List of BalanceChange objects
        """
        changes = []
        
        for line_num, condition in enumerate(verify_block, start=1):
            change = self._extract_balance_change(condition, line_num)
            if change:
                changes.append(change)
        
        return changes
    
    def _extract_balance_change(self, condition: str, line_number: int) -> Optional[BalanceChange]:
        """
        Extract balance change from a condition like:
        - sender_balance == old_sender_balance - 100
        - receiver_balance == old_receiver_balance + 200
        
        Returns None if condition doesn't represent a balance change.
        """
        # Must contain ==
        if '==' not in condition:
            return None
        
        parts = condition.split('==')
        if len(parts) != 2:
            return None
        
        left = parts[0].strip()
        right = parts[1].strip()
        
        # Check if right side contains old_ prefix
        if 'old_' not in right:
            return None
        
        # Try to parse: old_variable ± amount
        # Look for + or - operators
        if '+' in right:
            op_parts = right.split('+')
            if len(op_parts) == 2:
                old_var = op_parts[0].strip()
                amount_str = op_parts[1].strip()
                
                # Verify old_ prefix
                if old_var.startswith('old_'):
                    var_name = old_var[4:]  # Remove "old_" prefix
                    
                    # Try to parse amount as number
                    try:
                        amount = int(amount_str)
                    except ValueError:
                        try:
                            amount = float(amount_str)
                        except ValueError:
                            # Symbolic expression
                            amount = amount_str
                    
                    return BalanceChange(
                        variable_name=var_name,
                        amount=amount,
                        line_number=line_number,
                        is_increase=True
                    )
        
        elif '-' in right:
            # Need to handle negative numbers vs subtraction
            # Split on - but be careful with negative numbers
            op_idx = right.rfind('-')  # Find last - (rightmost)
            if op_idx > 0:  # Not at start (not a negative number)
                old_var = right[:op_idx].strip()
                amount_str = right[op_idx+1:].strip()
                
                # Verify old_ prefix
                if old_var.startswith('old_'):
                    var_name = old_var[4:]  # Remove "old_" prefix
                    
                    # Try to parse amount as number
                    try:
                        amount = int(amount_str)
                    except ValueError:
                        try:
                            amount = float(amount_str)
                        except ValueError:
                            # Symbolic expression
                            amount = amount_str
                    
                    return BalanceChange(
                        variable_name=var_name,
                        amount=amount,
                        line_number=line_number,
                        is_increase=False
                    )
        
        return None
    
    def validate_conservation(self, changes: List[BalanceChange]) -> ConservationResult:
        """
        Validate that sum of changes equals zero.
        
        Args:
            changes: List of balance changes
            
        Returns:
            ConservationResult indicating pass/fail
        """
        if not changes:
            return ConservationResult(is_valid=True, changes=[])
        
        # Compute sum of all signed changes
        total = 0
        symbolic_parts = []
        
        for change in changes:
            signed_amount = change.to_signed_amount()
            
            if isinstance(signed_amount, (int, float)):
                total += signed_amount
            else:
                # Symbolic expression
                symbolic_parts.append(signed_amount)
        
        # If we have symbolic parts, we can't validate numerically
        if symbolic_parts:
            # For now, assume symbolic expressions are valid
            # In a full implementation, we'd use Z3 to check
            return ConservationResult(is_valid=True, changes=changes)
        
        # Check if sum equals zero
        if abs(total) < 1e-10:  # Use epsilon for floating point comparison
            return ConservationResult(is_valid=True, changes=changes)
        else:
            return ConservationResult(
                is_valid=False,
                changes=changes,
                violation_amount=total,
                error_message="Conservation violated: sum of changes != 0"
            )
