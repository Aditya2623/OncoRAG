from abc import ABC, abstractmethod


class BasePipe(ABC):
    @property
    @abstractmethod
    def name(self) -> str:
        pass

    @abstractmethod
    def run(self, **kwargs):
        pass

    # def __call__(self):
    #     return self.run()
