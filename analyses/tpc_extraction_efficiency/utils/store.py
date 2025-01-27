from __future__ import annotations

import warnings

import awkward as ak
import numpy as np


class Store(dict):
    """
    Store: A dictionary that can be added to other Store object to aggregate the results of many independent computations

    This inherits from the inbuilt `dict` class and can be treated in much the same way.

    The main changes to this class are as follows:
        - The user can add Store objects as long as the two objects have the same keys, and the values are of similar types
        - There is special behaviours for awkward arrays which are concatenated not added
        - There is a HTML representation for use in Jupyter
    """

    total = 1
    completed = False

    def _repr_html_(self):
        """HTML representation of the object in the form of a table"""
        string = ""
        # Title
        string += "<h1>Store Object</h1>"

        # Total and metrics
        string += "<h3>Metrics</h3>"
        string += "<table>"
        string += "<tr>"
        string += "<th>Total</th><th>Completed</th><th>Percentage</th>"
        string += "</tr>"
        string += f"<td>{self.total}</td><td>{self.completed}</td><td>{self.completed/self.total*100:0.0f}%</td>"
        string += "</table>"

        # Values
        string += "<h3>Values</h3>"
        string += "<table>"
        string += "<tr>"
        string += "<th>Key</th><th>Value</th>"
        string += "</tr>"
        for key, value in self.items():
            string += "<tr>"
            if hasattr(value, "_repr_html_"):
                if representation := value._repr_html_():
                    pass
                else:
                    representation = repr(value)
            elif isinstance(value, ak.Array):
                representation = f"ak.Array({value.type})"
            else:
                representation = repr(value)
            string += f"<td>{key}</td><td>{representation}</td>"
            string += "</tr>"
        string += "</table>"
        return string

    def __add__(self, right: Store) -> Store:
        """Add the ability of add Store objects"""

        # Check both objects are of type Store
        if not isinstance(right, Store):
            raise TypeError(
                f"Cannot add Store to object of type {type(right)} - Only addition of another Store object is supported"
            )

        # Find the common and unique keys
        common = set(self) & set(right)
        difference = set(self) ^ set(right)
        if self.keys() != right.keys():
            warnings.warn(
                f"The keys of both Stores do not match - {difference} present in only one of the Stores",
                RuntimeWarning,
            )

        # Define the output storage
        output = Store()

        # Add and store the common objects
        for key in common:
            # Check the types of the objects are the same
            if isinstance(type(self[key]), type(right[key])):
                raise TypeError(
                    f"The types of the '{key}' values do not match ({type(self[key])} & {type(right[key])})"
                )
            # If awkward array then append
            elif isinstance(self[key], ak.Array):
                output[key] = ak.concatenate((self[key], right[key]))
            # If numpy array than append
            elif isinstance(self[key], np.ndarray):
                output[key] = np.concatenate((self[key], right[key]))
            # If objects can be added then add
            elif hasattr(self[key], "__add__"):
                output[key] = self[key] + right[key]
            else:
                warnings.warn(
                    f"The '{key}' object of type {type(self[key])} has not '__add__' method and will be ignored",
                    RuntimeWarning,
                )

        # Store the unique objects
        for key in difference:
            if key in self:
                output[key] = self[key]
            else:
                output[key] = right[key]

        # Add and store the total and completed values
        output.total = self.total + right.total
        output.completed = self.completed + right.completed

        return output

    def __radd__(self, right: Store) -> Store:
        """This is required for Dask functionality"""
        if not isinstance(right, Store):
            return self
        else:
            return self.__add__(right)


def add_dask_tasks(tasks):
    """This function intelligently adds object to make Dask computation more efficient"""
    if len(tasks) == 1:
        return tasks
    elif len(tasks) == 2:
        return sum(tasks)
    else:
        branch = [i + j for i, j in zip(*[iter(tasks)] * 2)]
        if len(tasks) % 2:
            branch.append(tasks[-1])
        return add_dask_tasks(branch)
