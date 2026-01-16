class AgentException(Exception):
    """Raised when an agent service throws an error"""

    pass


class GraphException(Exception):
    """Raised when a graph service throws an error"""

    pass


class ToGException(Exception):
    """Raised when using a ToG approach to answer a prompt fails.
    Possible scenarios are:
    - running into dead ends (no selection possible)
    - no seed entities found or given
    """

    pass


class InstructionError(Exception):
    """Raised when the agent did not follow the instructions.
    Examples:
    - answer does not match required format
    - errors while parsing answer
    - the agent simply did not do what it was supposed to do
    """

    pass
