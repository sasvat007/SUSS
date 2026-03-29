"""
Validation module for Financial State Engine inputs.

Ensures all inputs are valid before processing. Raises descriptive exceptions
for invalid data to aid debugging and integration with other systems.
"""

from datetime import datetime, timedelta
from typing import List, Optional, Tuple
from .models import (
    Transaction, Payable, Receivable, HiddenTransaction, 
    BusinessContext
)


class ValidationError(Exception):
    """Base exception for validation errors."""
    pass


class TransactionValidationError(ValidationError):
    """Exception for invalid transaction."""
    pass


class PayableValidationError(ValidationError):
    """Exception for invalid payable."""
    pass


class ReceivableValidationError(ValidationError):
    """Exception for invalid receivable."""
    pass


class BusinessContextValidationError(ValidationError):
    """Exception for invalid business context."""
    pass


def parse_date(date_str: str) -> datetime:
    """
    Parse date string in YYYY-MM-DD format.
    
    Args:
        date_str: Date string
        
    Returns:
        datetime object
        
    Raises:
        ValueError: If date format is invalid
    """
    try:
        return datetime.strptime(date_str, "%Y-%m-%d")
    except ValueError as e:
        raise ValueError(f"Invalid date format: {date_str}. Expected YYYY-MM-DD.") from e


def is_valid_date_format(date_str: str) -> bool:
    """Check if date string is in valid YYYY-MM-DD format."""
    try:
        parse_date(date_str)
        return True
    except ValueError:
        return False


def validate_transaction(transaction: Transaction, current_balance: float) -> None:
    """
    Validate a transaction.
    
    Args:
        transaction: Transaction to validate
        current_balance: Current account balance for sanity check
        
    Raises:
        TransactionValidationError: If transaction is invalid
    """
    # Validate date format
    if not is_valid_date_format(transaction.date):
        raise TransactionValidationError(
            f"Transaction {transaction.id}: Invalid date format '{transaction.date}'. "
            "Expected YYYY-MM-DD."
        )
    
    # Validate amount
    if transaction.amount == 0:
        raise TransactionValidationError(
            f"Transaction {transaction.id}: Amount cannot be zero."
        )
    
    # Validate transaction type
    if transaction.transaction_type not in ["debit", "credit"]:
        raise TransactionValidationError(
            f"Transaction {transaction.id}: Invalid type '{transaction.transaction_type}'. "
            "Must be 'debit' or 'credit'."
        )
    
    # Validate description is not empty
    if not transaction.description or not transaction.description.strip():
        raise TransactionValidationError(
            f"Transaction {transaction.id}: Description cannot be empty."
        )


def validate_payable(payable: Payable, reference_date: Optional[str] = None) -> None:
    """
    Validate a payable.
    
    Args:
        payable: Payable to validate
        reference_date: Reference date for checking past due dates (YYYY-MM-DD)
        
    Raises:
        PayableValidationError: If payable is invalid
    """
    # Validate id
    if not payable.id or not payable.id.strip():
        raise PayableValidationError("Payable: ID cannot be empty.")
    
    # Validate amount
    if payable.amount <= 0:
        raise PayableValidationError(
            f"Payable {payable.id}: Amount must be positive, got {payable.amount}."
        )
    
    # Validate due date format
    if not is_valid_date_format(payable.due_date):
        raise PayableValidationError(
            f"Payable {payable.id}: Invalid due_date format '{payable.due_date}'. "
            "Expected YYYY-MM-DD."
        )
    
    # Validate status
    valid_statuses = ["due", "pending", "overdue", "paid"]
    if payable.status not in valid_statuses:
        raise PayableValidationError(
            f"Payable {payable.id}: Invalid status '{payable.status}'. "
            f"Must be one of {valid_statuses}."
        )
    
    # Validate priority level
    valid_priorities = ["critical", "high", "normal", "low"]
    if payable.priority_level not in valid_priorities:
        raise PayableValidationError(
            f"Payable {payable.id}: Invalid priority_level '{payable.priority_level}'. "
            f"Must be one of {valid_priorities}."
        )
    
    # Validate description is not empty
    if not payable.description or not payable.description.strip():
        raise PayableValidationError(
            f"Payable {payable.id}: Description cannot be empty."
        )


def validate_receivable(receivable: Receivable, reference_date: Optional[str] = None) -> None:
    """
    Validate a receivable.
    
    Args:
        receivable: Receivable to validate
        reference_date: Reference date for checking past expected dates (YYYY-MM-DD)
        
    Raises:
        ReceivableValidationError: If receivable is invalid
    """
    # Validate id
    if not receivable.id or not receivable.id.strip():
        raise ReceivableValidationError("Receivable: ID cannot be empty.")
    
    # Validate amount
    if receivable.amount <= 0:
        raise ReceivableValidationError(
            f"Receivable {receivable.id}: Amount must be positive, got {receivable.amount}."
        )
    
    # Validate expected date format
    if not is_valid_date_format(receivable.expected_date):
        raise ReceivableValidationError(
            f"Receivable {receivable.id}: Invalid expected_date format '{receivable.expected_date}'. "
            "Expected YYYY-MM-DD."
        )
    
    # Validate confidence score
    if not (0.0 <= receivable.confidence <= 1.0):
        raise ReceivableValidationError(
            f"Receivable {receivable.id}: Confidence must be between 0.0 and 1.0, "
            f"got {receivable.confidence}."
        )
    
    # Validate status
    valid_statuses = ["pending", "received", "cancelled", "delayed"]
    if receivable.status not in valid_statuses:
        raise ReceivableValidationError(
            f"Receivable {receivable.id}: Invalid status '{receivable.status}'. "
            f"Must be one of {valid_statuses}."
        )
    
    # Validate description is not empty
    if not receivable.description or not receivable.description.strip():
        raise ReceivableValidationError(
            f"Receivable {receivable.id}: Description cannot be empty."
        )


def validate_hidden_transaction(hidden_tx: HiddenTransaction) -> None:
    """
    Validate a hidden transaction.
    
    Args:
        hidden_tx: Hidden transaction to validate
        
    Raises:
        ValidationError: If hidden transaction is invalid
    """
    # Validate id
    if not hidden_tx.id or not hidden_tx.id.strip():
        raise ValidationError("HiddenTransaction: ID cannot be empty.")
    
    # Validate type
    valid_types = ["salary", "loan_payment", "subscription", "tax", "rental", "utility", "other"]
    if hidden_tx.transaction_type not in valid_types:
        raise ValidationError(
            f"HiddenTransaction {hidden_tx.id}: Invalid type '{hidden_tx.transaction_type}'. "
            f"Must be one of {valid_types}."
        )
    
    # Validate amount
    if hidden_tx.amount == 0:
        raise ValidationError(
            f"HiddenTransaction {hidden_tx.id}: Amount cannot be zero."
        )
    
    # Validate frequency
    valid_frequencies = ["weekly", "biweekly", "monthly", "quarterly", "yearly"]
    if hidden_tx.frequency not in valid_frequencies:
        raise ValidationError(
            f"HiddenTransaction {hidden_tx.id}: Invalid frequency '{hidden_tx.frequency}'. "
            f"Must be one of {valid_frequencies}."
        )
    
    # Validate next date format
    if not is_valid_date_format(hidden_tx.next_date):
        raise ValidationError(
            f"HiddenTransaction {hidden_tx.id}: Invalid next_date format '{hidden_tx.next_date}'. "
            "Expected YYYY-MM-DD."
        )
    
    # Validate category
    if not hidden_tx.category or not hidden_tx.category.strip():
        raise ValidationError(
            f"HiddenTransaction {hidden_tx.id}: Category cannot be empty."
        )


def validate_business_context(context: BusinessContext) -> None:
    """
    Validate business context.
    
    Args:
        context: Business context to validate
        
    Raises:
        BusinessContextValidationError: If context is invalid
    """
    # Validate min_cash_buffer
    if context.min_cash_buffer < 0:
        raise BusinessContextValidationError(
            f"min_cash_buffer cannot be negative, got {context.min_cash_buffer}."
        )
    
    # Validate time_horizon_days
    if context.time_horizon_days <= 0:
        raise BusinessContextValidationError(
            f"time_horizon_days must be positive, got {context.time_horizon_days}."
        )
    
    if context.time_horizon_days > 365:
        raise BusinessContextValidationError(
            f"time_horizon_days should not exceed 365, got {context.time_horizon_days}."
        )
    
    # Validate avg_payment_delay_days
    if context.avg_payment_delay_days < 0:
        raise BusinessContextValidationError(
            f"avg_payment_delay_days cannot be negative, got {context.avg_payment_delay_days}."
        )
    
    # Validate currency
    if context.currency not in ["INR", "USD", "EUR", "GBP"]:
        raise BusinessContextValidationError(
            f"Unsupported currency '{context.currency}'. Currently only INR is fully supported."
        )


def validate_all_inputs(
    current_balance: float,
    transactions: List[Transaction],
    payables: List[Payable],
    receivables: List[Receivable],
    hidden_transactions: List[HiddenTransaction],
    business_context: BusinessContext,
    reference_date: Optional[str] = None
) -> Tuple[bool, List[str]]:
    """
    Validate all inputs at once.
    
    Args:
        current_balance: Current account balance
        transactions: List of transactions
        payables: List of payables
        receivables: List of receivables
        hidden_transactions: List of hidden transactions
        business_context: Business context
        reference_date: Reference date for validation (YYYY-MM-DD)
        
    Returns:
        Tuple of (is_valid: bool, errors: List[str])
    """
    errors = []
    
    # Validate business context first (it's foundational)
    try:
        validate_business_context(business_context)
    except BusinessContextValidationError as e:
        errors.append(str(e))
        return False, errors
    
    # Validate transactions
    for tx in transactions:
        try:
            validate_transaction(tx, current_balance)
        except TransactionValidationError as e:
            errors.append(str(e))
    
    # Validate payables
    for payable in payables:
        try:
            validate_payable(payable, reference_date)
        except PayableValidationError as e:
            errors.append(str(e))
    
    # Validate receivables
    for receivable in receivables:
        try:
            validate_receivable(receivable, reference_date)
        except ReceivableValidationError as e:
            errors.append(str(e))
    
    # Validate hidden transactions
    for hidden_tx in hidden_transactions:
        try:
            validate_hidden_transaction(hidden_tx)
        except ValidationError as e:
            errors.append(str(e))
    
    return len(errors) == 0, errors
