
from onesim.events import Event
from typing import Dict, List, Any        
from datetime import datetime


from typing import Any, List
from datetime import datetime
from onesim.events import Event

class ExpensesManagedEvent(Event):
    def __init__(self,
        from_agent_id: str,
        to_agent_id: str,
        company_id: str = "",
        total_expenses: float = 0.0,
        completion_status: str = 'completed',
        **kwargs: Any
    ) -> None:
        super().__init__(from_agent_id=from_agent_id, to_agent_id=to_agent_id, **kwargs)
        self.company_id = company_id
        self.total_expenses = total_expenses
        self.completion_status = completion_status

from typing import Any, List
from datetime import datetime
from onesim.events import Event

class CreditRatingAssessedEvent(Event):
    def __init__(self,
        from_agent_id: str,
        to_agent_id: str,
        company_id: str = "",
        credit_rating: str = 'unrated',
        **kwargs: Any
    ) -> None:
        super().__init__(from_agent_id=from_agent_id, to_agent_id=to_agent_id, **kwargs)
        self.company_id = company_id
        self.credit_rating = credit_rating

from typing import Any, List
from datetime import datetime
from onesim.events import Event

class StartEvent(Event):
    def __init__(self,
        from_agent_id: str,
        to_agent_id: str,
        **kwargs: Any
    ) -> None:
        super().__init__(from_agent_id=from_agent_id, to_agent_id=to_agent_id, **kwargs)

from typing import Any, List
from datetime import datetime
from onesim.events import Event

class RevenueGeneratedEvent(Event):
    def __init__(self,
        from_agent_id: str,
        to_agent_id: str,
        consumer_id: str = "",
        company_id: str = "",
        revenue_amount: float = 0.0,
        **kwargs: Any
    ) -> None:
        super().__init__(from_agent_id=from_agent_id, to_agent_id=to_agent_id, **kwargs)
        self.consumer_id = consumer_id
        self.company_id = company_id
        self.revenue_amount = revenue_amount

from typing import Any, List
from datetime import datetime
from onesim.events import Event

class LoanApprovedEvent(Event):
    def __init__(self,
        from_agent_id: str,
        to_agent_id: str,
        company_id: str = "",
        approved_loan_amount: float = 0.0,
        interest_rate: float = 0.0,
        **kwargs: Any
    ) -> None:
        super().__init__(from_agent_id=from_agent_id, to_agent_id=to_agent_id, **kwargs)
        self.company_id = company_id
        self.approved_loan_amount = approved_loan_amount
        self.interest_rate = interest_rate

from typing import Any, List
from datetime import datetime
from onesim.events import Event

class CashFlowEvaluatedEvent(Event):
    def __init__(self,
        from_agent_id: str,
        to_agent_id: str,
        company_id: str = "",
        cash_flow_status: str = 'unknown',
        credit_rating: str = 'unrated',
        **kwargs: Any
    ) -> None:
        super().__init__(from_agent_id=from_agent_id, to_agent_id=to_agent_id, **kwargs)
        self.company_id = company_id
        self.cash_flow_status = cash_flow_status
        self.credit_rating = credit_rating

from typing import Any, List
from datetime import datetime
from onesim.events import Event

class LoanApplicationEvent(Event):
    def __init__(self,
        from_agent_id: str,
        to_agent_id: str,
        company_id: str = "",
        loan_amount: float = 0.0,
        credit_rating: str = 'unrated',
        **kwargs: Any
    ) -> None:
        super().__init__(from_agent_id=from_agent_id, to_agent_id=to_agent_id, **kwargs)
        self.company_id = company_id
        self.loan_amount = loan_amount
        self.credit_rating = credit_rating

from typing import Any, List
from datetime import datetime
from onesim.events import Event

class LoanRejectedEvent(Event):
    def __init__(self,
        from_agent_id: str,
        to_agent_id: str,
        company_id: str = "",
        rejection_reason: str = 'unknown',
        **kwargs: Any
    ) -> None:
        super().__init__(from_agent_id=from_agent_id, to_agent_id=to_agent_id, **kwargs)
        self.company_id = company_id
        self.rejection_reason = rejection_reason