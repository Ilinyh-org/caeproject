from abc import ABCMeta, abstractmethod


class CAETask:
    __metaclass__ = ABCMeta

    @abstractmethod
    def solve(self):
        ...

    @property
    @abstractmethod
    def input_file(self):
        ...

    @input_file.setter
    @abstractmethod
    def input_file(self, file):
        ...

    @property
    @abstractmethod
    def log_file(self):
        ...

    @log_file.setter
    @abstractmethod
    def log_file(self, name):
        ...

    @property
    @abstractmethod
    def parameters_file(self):
        ...

    @parameters_file.setter
    @abstractmethod
    def parameters_file(self, name):
        ...

    @property
    @abstractmethod
    def results_file_name(self):
        ...

    @results_file_name.setter
    @abstractmethod
    def results_file_name(self, name):
        ...

    @property
    @abstractmethod
    def geometry_file_name(self):
        ...

    @geometry_file_name.setter
    @abstractmethod
    def geometry_file_name(self, name):
        ...

    @property
    @abstractmethod
    def application_version(self):
        ...

    @application_version.setter
    @abstractmethod
    def application_version(self, name):
        ...

    @property
    @abstractmethod
    def working_directory_path(self):
        ...

    @working_directory_path.setter
    @abstractmethod
    def working_directory_path(self, name):
        ...

