
class BaseImporter:
    @classmethod
    def add_arguments(cls, parser):
        raise NotImplementedError('add_arguments must be implemented')

    def read_options(self, options):
        raise NotImplementedError('read_options must be implemented')
