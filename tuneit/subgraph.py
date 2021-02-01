class Subgraph:
    def __init__(self, nodes, output=None, dependencies=None):

        self.nodes = nodes
        self.output = output
        self.dependencies = dependencies

    def __call__(self, *args):
        "should call all the functions in the correct order and return the result"
        pass
