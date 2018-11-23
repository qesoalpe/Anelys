class Event():
    def __init__(self):
        self._suscribers = list()

    def suscribe(self, suscriber):
        if suscriber not in self._suscribers:
            self._suscribers.append(suscriber)


    def unsuscribe(self, suscriber):
        if suscriber in self._suscribers:
            self._suscribers.remove(suscriber)

    def __call__(self, *args, **kwargs):
        rr = None
        for suscriber in self._suscribers:
            if rr is None:
                rr = suscriber(*args, **kwargs)
            else:
                suscriber(*args, **kwargs)
        return rr

    def __len__(self):
        return len(self._suscribers)
