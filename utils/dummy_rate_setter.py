class DummyRateSetter(object):
    def __init__(self, rates=[1.0], inflections=[]):
        assert len(rates) > 0, "Must have at least one rate."
        self.rates = rates
        self.inflections = inflections
        self._count = 0
        self._i = 0

    def __call__(self):
        if len(self.inflections) > (self._i+1) and self._count > self.inflections[self._i]:
            self._i += 1
        self._count += 1
        return self.rates[self._i]