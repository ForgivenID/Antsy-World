class SimpleDistributor:
    """
        Class for using a function over a pool of objects, similar to *map()* but executes only once on every call and
        can loop over the pool indefinitely; Use to distribute load over multiple processes/threads.
        Doesn't check if objects from a pool are ready to get a task, so they should have some kind of buffer.
    """

    def __init__(self, objects, func):
        self.objects = objects
        self.func = func
        self.pointer = 0

    def __call__(self, *args, **kwargs):
        if len(self.objects) == 0: return
        self.func(self.objects[self.pointer % len(self.objects)], *args, **kwargs)
        self.pointer += 1


class _SmartDistributor:
    """
        Class for using a function over a pool of objects, similar to *map()* but executes only once on every call and
        can loop over the pool indefinitely; Use to distribute load over multiple processes/threads.
        Distributes load depending on how busy the pool is.
        \n
        **Not implemented.**
    """

    def __init__(self):
        raise NotImplemented
