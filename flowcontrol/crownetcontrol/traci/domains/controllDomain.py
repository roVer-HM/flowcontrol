from flowcontrol.crownetcontrol.traci.domains.domain import Domain


class CtlDomain(Domain):
    def __init__(
        self,
        name,
        cmdGetID,
        cmdSetID,
        subscribeID,
        subscribeResponseID,
        contextID,
        contextResponseID,
    ):
        super().__init__(
            name,
            cmdGetID,
            cmdSetID,
            subscribeID,
            subscribeResponseID,
            contextID,
            contextResponseID,
        )
