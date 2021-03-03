import re
import random

from traitlets import Dict, Unicode, Bool, observe
from traitlets.config.loader import Config
from textwrap import dedent

from .. import utils
from . import NbGraderPreprocessor
from typing import Any, Tuple
from nbformat.notebooknode import NotebookNode
from nbconvert.exporters.exporter import ResourcesDict


class RandomizeNotebook(NbGraderPreprocessor):
    """A preprocessor for randomizing variables in a notebook.
    
    """

    #TODO: Allow for setting ranges on random int and float and maybe make str choose from list

    begin_random_str = Unicode(
        "RANDOM STR",
        help="The comment marking a random string variable"
    ).tag(config=True)

    begin_random_int = Unicode(
        "RANDOM INT",
        help="The comment marking a random int variable"
    ).tag(config=True)

    begin_random_float = Unicode(
        "RANDOM FLOAT",
        help="The comment marking a random float variable"
    ).tag(config=True)


    def preprocess(self, nb: NotebookNode, resources: ResourcesDict) -> Tuple[NotebookNode, ResourcesDict]:
        nb, resources = super(RandomizeNotebook, self).preprocess(nb, resources)
        if 'celltoolbar' in nb.metadata:
            del nb.metadata['celltoolbar']
        return nb, resources

    def preprocess_cell(self,
                        cell: NotebookNode,
                        resources: ResourcesDict,
                        cell_index: int
                        ) -> Tuple[NotebookNode, ResourcesDict]:
        """Find a line in the cell that ends with the comment `self.begin_random_str`, `self.begin_random_int` or `self.begin_random_float` (e.g. ### RANDOM STR). Replace that variable's value with a random value.

        This modifies the cell in place, and then returns True if a random value was inserted.
        """
        # pull out the cell input/source
        lines = cell.source.split("\n")

        new_lines = []
        
        for line in lines:
            equal_idx = line.find("=")
            # Only check for replace if a variable assignment occurs
            if equal_idx != -1:
                #TODO: Add more random variables (maybe use hypothesis)
                random_value = False
                if self.begin_random_str in line:
                    random_value = random.choice(['a', 'b', 'c'])
                elif self.begin_random_int in line:
                    random_value = random.randint(-1000, 1000)
                elif self.begin_random_float in line:
                    random_value = random.uniform(-1000, 1000)

                if random_value:
                    line = f"{line[:equal_idx]}= {random_value}"

            new_lines.append(line)  

        # replace the cell source
        cell.source = "\n".join(new_lines)

        return cell, resources