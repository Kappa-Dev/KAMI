"""Basic API for programmatic interaction with Kami Server."""
from kami.resolvers.black_box import resolve_nuggets





class KamiAPI:

    def __init__(self, adress):
        # check it started
        self.server = adress

    @classmethod
    def from_new_server(cls, address):
        # start server
        new_server = run(sdjhsdj)
        cls(new_server)



def get_hierarchy():
    """Get Kami hierarchy object."""
    pass


def get_action_graph():
    """Get Kami action graph."""
    pass


def get_nuggets():
    """Get nuggets from Kami hierarchy."""

    pass


def process_nuggets(nuggets):
    """Process a collection of nuggets and add it to the hierarchy."""
    # 1. get hierarchy
    hierarchy = get_hierarchy()
    # 2. feed nuggets
    resolve_nuggets(hierarchy, nuggets)
    return


def start_kami_server(option):
    """Start Kami server."""

    pass


def export_to_kappa():
    """Export model to Kappa."""
    pass
