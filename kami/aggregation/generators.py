"""Collection of data structures for graph generation.

`KamiGraph`
`Generator`

TODO: Make generation of graph elements independent of identification
or identification optional
"""
import copy
import warnings

import networkx as nx

from regraph import (add_edge,
                     add_node,
                     add_node_attrs,
                     remove_node,
                     remove_edge,
                     remove_node_attrs)

from kami.aggregation.identifiers import EntityIdentifier
from kami.aggregation.bookkeeping import apply_bookkeeping
from kami.data_structures.entities import (Gene, RegionActor,
                                           Residue, SiteActor, State
                                           )
from kami.data_structures.interactions import (Modification, SelfModification,
                                               AnonymousModification,
                                               LigandModification,
                                               Binding, Unbinding)
from kami.exceptions import (KamiError,
                             KamiWarning,
                             NuggetGenerationError)
from kami.utils.id_generators import (get_nugget_gene_id,
                                      get_nugget_region_id,
                                      get_nugget_residue_id,
                                      get_nugget_state_id,
                                      get_nugget_is_bnd_id,
                                      get_nugget_site_id,
                                      get_nugget_bnd_id,)


class KamiGraph:
    """Graph container data structure.

    Attributes
    ----------
    graph : nx.(Di)Graph
        Graph
    meta_typing : dict
        Typing of the graph by the meta-model
    reference_typing : dict
        Typing of the graph by the reference graph
    """

    def __init__(self, graph=None, meta_typing=None,
                 reference_typing=None):
        """Initialize graph container."""
        if graph:
            self.graph = copy.deepcopy(graph)
        else:
            self.graph = nx.DiGraph()

        self.node = self.graph.node
        self.edge = self.graph.adj

        if meta_typing:
            self.meta_typing = copy.deepcopy(meta_typing)
        else:
            self.meta_typing = dict()
        if reference_typing:
            self.reference_typing = copy.deepcopy(reference_typing)
        else:
            self.reference_typing = dict()
        return

    def add_node(self, node_id, attrs=None, meta_typing=None,
                 reference_typing=None):
        """Add node + typings to a nugget."""
        add_node(self.graph, node_id, attrs)
        if meta_typing:
            self.meta_typing[node_id] = meta_typing
        if reference_typing:
            self.reference_typing[node_id] = reference_typing
        return

    def add_node_attrs(self, node_id, attrs):
        add_node_attrs(self.graph, node_id, attrs)

    def add_edge(self, s, t, attrs=None):
        """Add edge between the nodes of a nugget."""
        add_edge(self.graph, s, t, attrs)
        return

    def remove_node(self, node_id):
        remove_node(self.graph, node_id)
        del self.meta_typing[node_id]
        if node_id in self.reference_typing:
            del self.reference_typing[node_id]

    def remove_node_attrs(self, node_id, attrs):
        remove_node_attrs(self.graph, node_id, attrs)

    def remove_edge(self, s, t):
        remove_edge(self.graph, s, t)

    def nodes(self):
        """Return a list of nodes of the nugget graph."""
        return self.graph.nodes()

    def edges(self):
        """Return a list of edges of the nugget graph."""
        return self.graph.edges()


class Generator(object):
    """Base class for nugget generators."""

    def __init__(self, entity_identifier=None, bookkeeping=False):
        """Initialize generator with an entity identifier."""
        self.entity_identifier = entity_identifier
        self.bookkeeping = bookkeeping

    def generate_state(self, nugget, state, father):
        prefix = father

        state_id = get_nugget_state_id(nugget.graph, state, prefix)

        action_graph_state = None
        if self.entity_identifier and father in nugget.reference_typing.keys():
            action_graph_state = self.entity_identifier.identify_state(
                state, nugget.reference_typing[father])

        nugget.add_node(
            state_id,
            state.meta_data(),
            meta_typing="state",
            reference_typing=action_graph_state
        )
        return state_id

    def generate_residue(self, nugget, residue, father, gene):
        prefix = father

        residue_id = get_nugget_residue_id(nugget.graph, residue, prefix)

        action_graph_residue = None
        if self.entity_identifier and gene in nugget.reference_typing.keys():
            action_graph_residue = self.entity_identifier.identify_residue(
                residue, nugget.reference_typing[gene])

        nugget.add_node(
            residue_id,
            residue.meta_data(),
            meta_typing="residue",
            reference_typing=action_graph_residue
        )
        state_id = None
        if residue.state:
            state_id = self.generate_state(
                nugget,
                residue.state,
                residue_id
            )
            nugget.add_edge(state_id, residue_id)

        return (residue_id, state_id)

    def generate_bound(self, nugget, partner, father, test=True):
        (partner_gene, partner_region, partner_site) = self.generate_actor(
            nugget, partner)

        # generate prefix for is_bnd_id
        prefix = father

        is_bnd_id = get_nugget_is_bnd_id(
            nugget.graph, prefix, partner_gene)

        nugget.add_node(
            is_bnd_id,
            attrs={"type": "be", "test": test},
            meta_typing="bnd"
        )
        if partner_site is not None:
            nugget.add_edge(partner_site, is_bnd_id)
        elif partner_region is not None:
            nugget.add_edge(partner_region, is_bnd_id)
        else:
            nugget.add_edge(partner_gene, is_bnd_id)

        if self.bookkeeping:
            apply_bookkeeping(
                EntityIdentifier(
                    nugget.graph, nugget.meta_typing),
                nugget.nodes(), [partner_gene])
        return is_bnd_id

    def generate_site(self, nugget, site, father, gene):
        # 1. create region node
        prefix = father
        site_id = get_nugget_site_id(
            nugget.graph, str(site), prefix
        )

        action_graph_site = None
        if self.entity_identifier and father in nugget.reference_typing.keys():
            action_graph_site = self.entity_identifier.identify_site(
                site, nugget.reference_typing[father])

        nugget.add_node(
            site_id, site.meta_data(),
            meta_typing="site",
            reference_typing=action_graph_site
        )

        # create and attach residues
        for residue in site.residues:
            if residue.loc is not None and site.start is not None and\
               site.end is not None:
                if residue.loc < int(site.start) or residue.loc > int(site.end):
                    raise KamiError(
                        "Residue '%s' of a site '%s' is not valid: "
                        "residue loc (%d) is out of the site range (%d-%d)" %
                        (str(residue), str(site),
                         residue.loc, site.start, site.end)
                    )
            (residue_id, _) = self.generate_residue(
                nugget, residue, site_id, gene)
            nugget.add_edge(residue_id, site_id, residue.location())

        # create and attach states
        for state in site.states:
            state_id = self.generate_state(
                nugget, state, site_id)
            nugget.add_edge(state_id, site_id)

        # 5. create and attach bounds
        for partner in site.bound_to:
            is_bnd_id = self.generate_bound(
                nugget, partner, site_id, test=True)
            nugget.add_edge(site_id, is_bnd_id)

        for partner in site.unbound_from:
            is_notbnd_id = self.generate_bound(
                nugget, partner, site_id, test=False)
            nugget.add_edge(site_id, is_notbnd_id)

        return site_id

    def generate_region(self, nugget, region, father):
        # 1. create region node
        prefix = father

        region_id = get_nugget_region_id(
            nugget.graph, str(region), prefix
        )

        # identify region
        action_graph_region = None
        if self.entity_identifier and father in nugget.reference_typing.keys():
            action_graph_region = self.entity_identifier.identify_region(
                region, nugget.reference_typing[father])

        nugget.add_node(
            region_id, region.meta_data(),
            meta_typing="region",
            reference_typing=action_graph_region
        )

        # 2. create and attach residues
        for residue in region.residues:
            if residue.loc is not None and region.start is not None and\
               region.end is not None:
                if residue.loc < region.start or residue.loc > region.end:
                    raise KamiError(
                        "Residue '%s' of a region '%s' is not valid: "
                        "residue loc (%d) is out of the region range (%d-%d)" %
                        (str(residue), str(region),
                         residue.loc, region.start, region.end)
                    )
            (residue_id, _) = self.generate_residue(
                nugget, residue, region_id, father)
            nugget.add_edge(residue_id, region_id, residue.location())

        # 3. create and attach sites
        for site in region.sites:
            if site.start is not None and site.end is not None and\
               region.start is not None and region.end is not None:
                if site.start < region.start or site.end > region.end:
                    raise KamiError(
                        "Site '%s' of a region '%s' is not valid: site "
                        "range (%d-%d) is out of the region range (%d-%d)" %
                        (str(site), str(region),
                         site.start, site.end, region.start, region.end)
                    )
            site_id = self.generate_site(
                nugget, site, region_id, father)
            nugget.add_edge(site_id, region_id, site.location())

        # 4. create and attach states
        for state in region.states:
            state_id = self.generate_state(
                nugget, state, region_id)
            nugget.add_edge(state_id, region_id)

        # 5. create and attach bounds
        for partners in region.bound_to:
            bound_locus_id = self.generate_bound(
                nugget, partners, region_id, test=True)
            nugget.add_edge(region_id, bound_locus_id)

        for partners in region.unbound_from:
            bound_locus_id = self.generate_bound(
                nugget, partners, region_id, test=False)
            nugget.add_edge(region_id, bound_locus_id)

        if self.bookkeeping:
            apply_bookkeeping(
                EntityIdentifier(
                    nugget.graph, nugget.meta_typing),
                nugget.nodes(), [])

        return region_id

    def generate_gene(self, nugget, gene):
        """Generate agent group + indentify mapping."""
        # 1. create agent node
        agent_id = get_nugget_gene_id(nugget.graph, gene)

        # 2. identify agent (map to a node in the action graph)
        action_graph_agent = None
        if self.entity_identifier:
            action_graph_agent = self.entity_identifier.identify_gene(gene)

        nugget.add_node(
            agent_id,
            gene.meta_data(),
            meta_typing="gene",
            reference_typing=action_graph_agent
        )

        # 2. create and attach residues
        for residue in gene.residues:
            (residue_id, _) = self.generate_residue(
                nugget, residue, agent_id, agent_id)
            nugget.add_edge(residue_id, agent_id, residue.location())

        # 3. create and attach states
        for state in gene.states:
            state_id = self.generate_state(
                nugget, state, agent_id)
            nugget.add_edge(state_id, agent_id)

        # 4. create and attach regions
        for region in gene.regions:
            region_id = self.generate_region(
                nugget, region, agent_id)
            nugget.add_edge(region_id, agent_id, region.location())

        # 5. create and attach sites
        for site in gene.sites:
            site_id = self.generate_site(
                nugget, site, agent_id, agent_id)
            nugget.add_edge(site_id, agent_id, site.location())

        # 6. create and attach bounds
        for bnd in gene.bound_to:
            bound_locus_id = self.generate_bound(
                nugget, bnd, agent_id, test=True)
            nugget.add_edge(agent_id, bound_locus_id)

        for bnd in gene.unbound_from:
            bound_locus_id = self.generate_bound(
                nugget, bnd, agent_id, test=False)
            nugget.add_edge(agent_id, bound_locus_id)

        if self.bookkeeping:
            apply_bookkeeping(
                EntityIdentifier(
                    nugget.graph, nugget.meta_typing),
                nugget.nodes(), [agent_id])

        return agent_id

    def generate_region_actor(self, nugget, region_actor):
        agent_id = self.generate_gene(
            nugget, region_actor.gene)
        region_id = self.generate_region(
            nugget, region_actor.region, agent_id)
        nugget.add_edge(region_id, agent_id, region_actor.region.location())
        return (agent_id, region_id)

    def generate_site_actor(self, nugget, site_actor):
        agent_id = self.generate_gene(
            nugget, site_actor.gene)

        site_id = self.generate_site(
            nugget, site_actor.site, agent_id, agent_id)
        region_id = None
        if len(site_actor.region) > 0:
            for r in site_actor.region:
                region_id = self.generate_region(
                    nugget, r, agent_id)
                nugget.add_edge(region_id, agent_id, r.location())
                nugget.add_edge(site_id, region_id, site_actor.site.location())
        else:
            nugget.add_edge(site_id, agent_id, site_actor.site.location())

        return (agent_id, site_id, region_id)

    def generate_actor(self, nugget, actor):
        actor_region = None
        actor_site = None
        if isinstance(actor, Gene):
            actor_gene = self.generate_gene(nugget, actor)
        elif isinstance(actor, RegionActor):
            (actor_gene, actor_region) = self.generate_region_actor(
                nugget, actor)
        elif isinstance(actor, SiteActor):
            (actor_gene, actor_site, actor_region) =\
                self.generate_site_actor(
                    nugget, actor)
        else:
            raise NuggetGenerationError(
                "Unkown type of a PPI actor: '%s'" % type(actor)
            )
        return actor_gene, actor_region, actor_site

    def generate_mod_target(self, nugget, target, attached_to,
                            gene, mod_value=True):
        residue = None
        if isinstance(target, State):
            if target.test == mod_value:
                warnings.warn(
                    "Modification does not change the state's value!",
                    UserWarning
                )
            state = self.generate_state(
                nugget, target, attached_to)
        elif isinstance(target, Residue):
            if target.state:
                if target.state.test == mod_value:
                    warnings.warn(
                        "Modification does not change the state's value!",
                        KamiWarning
                    )
                (residue, state) = self.generate_residue(
                    nugget, target, attached_to, gene)
            else:
                raise KamiError(
                    "Target of modification is required to be either "
                    "`State` or `Residue` with non-empty state: state "
                    "of residue is empty"
                )
        else:
            raise KamiError(
                "Target of modification is required to be either "
                "`State` or `Residue` with non-empty state: %s "
                "is provided" % type(target)
            )

        if residue is not None:
            nugget.add_edge(residue, attached_to, target.location())

        else:
            nugget.add_edge(state, attached_to)

        return residue, state


class ModGenerator(Generator):
    """Modification nugget generator."""

    def generate(self, mod):
        """Create a mod nugget graph and find its typing."""
        nugget = KamiGraph()

        template_rels = {"mod_template": dict()}

        # 1. Process enzyme
        (enzyme, enzyme_region, enzyme_site) = self.generate_actor(
            nugget, mod.enzyme)
        template_rels["mod_template"][enzyme] = {"enzyme"}
        if enzyme_region:
            template_rels["mod_template"][enzyme_region] = {"enzyme_region"}
        if enzyme_site:
            template_rels["mod_template"][enzyme_site] = {"enzyme_site"}

        # Process substrate
        (substrate, substrate_region, substrate_site) = self.generate_actor(
            nugget, mod.substrate)
        template_rels["mod_template"][substrate] = {"substrate"}
        if substrate_region:
            template_rels["mod_template"][substrate_region] = {"substrate_region"}
        if substrate_site:
            template_rels["mod_template"][substrate_site] = {"substrate_site"}

        # 2. create mod node
        mod_attrs = mod.to_attrs()
        mod_attrs["value"] = mod.value

        nugget.add_node(
            "mod",
            mod_attrs,
            meta_typing="mod"
        )

        template_rels["mod_template"]["mod"] = {"mod"}

        # 3. create state related nodes subject to modification
        if substrate_site:
            attached_to = substrate_site
        elif substrate_region:
            attached_to = substrate_region
        else:
            attached_to = substrate

        (mod_residue_id, mod_state_id) = self.generate_mod_target(
            nugget, mod.target, attached_to, substrate, mod.value)
        if mod_residue_id is not None:
            template_rels["mod_template"][mod_residue_id] = {"substrate_residue"}
        template_rels["mod_template"][mod_state_id] = {"mod_state"}

        if enzyme_site:
            nugget.add_edge(enzyme_site, "mod")
        elif enzyme_region:
            nugget.add_edge(enzyme_region, "mod")
        else:
            nugget.add_edge(enzyme, "mod")
        nugget.add_edge("mod", mod_state_id)

        return (
            nugget, "mod",
            template_rels,
            mod.desc
        )


class BndGenerator(Generator):
    """Binding nugget generator."""

    def generate(self, bnd):
        nugget = KamiGraph()
        template_rels = {
            "bnd_template": dict()
        }

        left = []
        right = []

        # 1. create bnd actors
        gene_id, region_id, site_id = self.generate_actor(nugget, bnd.left)
        template_rels["bnd_template"][gene_id] = {"left_partner"}
        if site_id is not None:
            left.append(site_id)
            template_rels["bnd_template"][site_id] = {"left_partner_site"}
        if region_id is not None:
            template_rels["bnd_template"][region_id] = {"left_partner_region"}
            if site_id is None:
                left.append(region_id)
        if site_id is None and region_id is None:
            left.append(gene_id)

        gene_id, region_id, site_id = self.generate_actor(nugget, bnd.right)
        template_rels["bnd_template"][gene_id] = {"right_partner"}
        if site_id is not None:
            right.append(site_id)
            template_rels["bnd_template"][site_id] = {"right_partner_site"}
        if region_id is not None:
            template_rels["bnd_template"][region_id] = {"right_partner_region"}
            if site_id is None:
                right.append(region_id)
        if site_id is None and region_id is None:
            right.append(gene_id)

        # 2. create binding action
        left_ids = "_".join(left)
        right_ids = "_".join(right)
        bnd_id = get_nugget_bnd_id(nugget.graph, left_ids, right_ids)

        bnd_attrs = bnd.to_attrs()
        bnd_attrs["type"] = "do"
        if isinstance(bnd, Binding):
            bnd_attrs["test"] = True
        else:
            bnd_attrs["test"] = False

        nugget.add_node(
            bnd_id, bnd_attrs,
            meta_typing="bnd"
        )
        template_rels["bnd_template"][bnd_id] = {"bnd"}

        # connect left/right members to the respective loci
        for member in left:
            nugget.add_edge(member, bnd_id)

        for member in right:
            nugget.add_edge(member, bnd_id)

        return (
            nugget, "bnd",
            template_rels,
            bnd.desc
        )


class AnonymousModGenerator(Generator):
    """Anonymous nugget generator."""

    def generate(self, mod):
        """Create a mod nugget graph and find its typing."""
        nugget = KamiGraph()
        template_rels = {
            "mod_template": dict()
        }

        # Process substrate
        (substrate, substrate_region, substrate_site) = self.generate_actor(
            nugget, mod.substrate)
        template_rels["mod_template"][substrate] = {"substrate"}
        if substrate_region:
            template_rels["mod_template"][substrate_region] = {"substrate_region"}
        if substrate_site:
            template_rels["mod_template"][substrate_site] = {"substrate_site"}

        # 2. create mod node
        mod_attrs = mod.to_attrs()
        mod_attrs["value"] = mod.value

        nugget.add_node(
            "mod",
            mod_attrs,
            meta_typing="mod"
        )
        template_rels["mod_template"]["mod"] = {"mod"}

        # 3. create state related nodes subject to modification
        if substrate_site:
            attached_to = substrate_site
        elif substrate_region:
            attached_to = substrate_region
        else:
            attached_to = substrate

        (mod_residue_id, mod_state_id) = self.generate_mod_target(
            nugget, mod.target, attached_to, substrate, mod.value)
        if mod_residue_id is not None:
            template_rels["mod_template"][mod_residue_id] = {"substrate_residue"}
        template_rels["mod_template"][mod_state_id] = {"mod_state"}

        nugget.add_edge("mod", mod_state_id)
        return (
            nugget, "mod",
            template_rels,
            mod.desc
        )


class SelfModGenerator(Generator):
    """Generator class for auto modification nugget."""

    def generate(self, mod):
        """Create a mod nugget graph and find its typing."""
        nugget = KamiGraph()

        template_rels = {"mod_template": dict()}

        # 1. Process enzyme
        (enzyme, enzyme_region, enzyme_site) = self.generate_actor(
            nugget, mod.enzyme)
        template_rels["mod_template"][enzyme] = {"enzyme", "substrate"}
        if enzyme_region:
            template_rels["mod_template"][enzyme_region] = {"enzyme_region"}
        if enzyme_site:
            template_rels["mod_template"][enzyme_site] = {"enzyme_site"}

        # Process substrate components of the same gene
        substrate_region = None
        substrate_site = None
        if mod.substrate_region is not None:
            substrate_region = self.generate_region(
                nugget, mod.substrate_region, enzyme)
            template_rels["mod_template"][substrate_region] = {"substrate_region"}
            nugget.add_edge(
                substrate_region, enzyme, mod.substrate_region.location())
        if mod.substrate_site is not None:
            if substrate_region is not None:
                substrate_site = self.generate_site(
                    nugget, mod.substrate_site, substrate_region, enzyme)
                nugget.add_edge(
                    substrate_site, substrate_region,
                    mod.substrate_site.location())
            else:
                substrate_site = self.generate_site(
                    nugget, mod.substrate_site, enzyme, enzyme)
                nugget.add_edge(
                    substrate_site, enzyme,
                    mod.substrate_site.location())
            template_rels["mod_template"][substrate_site] = {"substrate_site"}

        # 2. create mod node
        mod_attrs = mod.to_attrs()
        mod_attrs["value"] = mod.value

        nugget.add_node(
            "mod",
            mod_attrs,
            meta_typing="mod"
        )

        template_rels["mod_template"]["mod"] = {"mod"}

        if substrate_site:
            attached_to = substrate_site
        elif substrate_region:
            attached_to = substrate_region
        else:
            attached_to = enzyme

        # 3. create state related nodes subject to modification
        (mod_residue_id, mod_state_id) = self.generate_mod_target(
            nugget, mod.target, attached_to, enzyme, mod.value)
        if mod_residue_id is not None:
            template_rels["mod_template"][mod_residue_id] = {"substrate_residue"}
        template_rels["mod_template"][mod_state_id] = {"mod_state"}

        if enzyme_site:
            nugget.add_edge(enzyme_site, "mod")
        elif enzyme_region:
            nugget.add_edge(enzyme_region, "mod")
        else:
            nugget.add_edge(enzyme, "mod")
        nugget.add_edge("mod", mod_state_id)
        return (
            nugget, "mod",
            template_rels,
            mod.desc
        )


class LigandModGenerator(Generator):
    """Generator class for transmodification nugget."""

    def generate(self, mod):
        """Create a mod nugget graph and find its typing."""
        nugget = KamiGraph()
        template_rels = {
            "mod_template": {},
            "bnd_template": {}
        }

        # 1. Process enzyme
        (enzyme, enzyme_region, enzyme_site) = self.generate_actor(
            nugget, mod.enzyme)
        template_rels["mod_template"][enzyme] = {"enzyme"}
        if enzyme_region:
            template_rels["mod_template"][enzyme_region] = {"enzyme_region"}
        if enzyme_site:
            template_rels["mod_template"][enzyme_site] = {"enzyme_site"}

        # Process substrate
        (substrate, substrate_region, substrate_site) = self.generate_actor(
            nugget, mod.substrate)
        template_rels["mod_template"][substrate] = {"substrate"}
        if substrate_region:
            template_rels["mod_template"][substrate_region] = {"substrate_region"}
        if substrate_site:
            template_rels["mod_template"][substrate_site] = {"substrate_site"}

        # 2. create mod node
        mod_attrs = mod.to_attrs()
        mod_attrs["value"] = mod.value

        nugget.add_node(
            "mod",
            mod_attrs,
            meta_typing="mod"
        )

        template_rels["mod_template"]["mod"] = {"mod"}

        # 3. create state related nodes subject to modification
        if substrate_site:
            attached_to = substrate_site
        elif substrate_region:
            attached_to = substrate_region
        else:
            attached_to = substrate

        (mod_residue_id, mod_state_id) = self.generate_mod_target(
            nugget, mod.target, attached_to, substrate, mod.value)
        if mod_residue_id is not None:
            template_rels["mod_template"][mod_residue_id] = {"substrate_residue"}
        template_rels["mod_template"][mod_state_id] = {"mod_state"}

        if enzyme_site:
            nugget.add_edge(enzyme_site, "mod")
        elif enzyme_region:
            nugget.add_edge(enzyme_region, "mod")
        else:
            nugget.add_edge(enzyme, "mod")
        nugget.add_edge("mod", mod_state_id)

        # 4. Process enzyme/substrate binding conditions
        # 4.1 Validation checks
        template_rels["bnd_template"][enzyme] = {"left_partner"} 
        template_rels["bnd_template"][substrate] = {"right_partner"}
        if mod.enzyme_bnd_subactor == "gene":
            pass
        elif mod.enzyme_bnd_subactor == "region":
            if enzyme_region is None:
                raise KamiError(
                    "Cannot use region as an enzyme binding subactor: "
                    "no regions are included in the enzyme actor '{}'!".format(
                        mod.enzyme.__repr__()))
            else:
                template_rels["bnd_template"][enzyme_region] = {"left_partner_region"}
        elif mod.enzyme_bnd_subactor == "site":
            if enzyme_site is None:
                raise KamiError(
                    "Cannot use site as an enzyme binding subactor: "
                    "no sites are included in the enzyme actor '{}'!".format(
                        mod.enzyme.__repr__()))
            else:
                template_rels["bnd_template"][enzyme_site] = {"left_partner_site"}
        else:
            raise KamiError(
                "Invalid value of `enzyme_bnd_subactor` of LigandModification object:"
                "expected 'gene', 'site' or 'region', got '{}'".format(
                    mod.enzyme_bnd_subactor))

        if mod.substrate_bnd_subactor == "gene":
            pass
        elif mod.substrate_bnd_subactor == "region":
            if substrate_region is None:
                raise KamiError(
                    "Cannot use region as a substrate binding subactor: "
                    "no regions are included in the substrate actor '{}'!".format(
                        mod.substrate.__repr__()))
            else:
                template_rels["bnd_template"][substrate_region] = {"right_partner_region"} 
        elif mod.substrate_bnd_subactor == "site":
            if substrate_site is None:
                raise KamiError(
                    "Cannot use site as a substrate binding subactor: "
                    "no sites are included in the substrate actor '{}'!".format(
                        mod.substrate.__repr__()))
            else:
                template_rels["bnd_template"][substrate_site] = {"right_partner_site"}
        else:
            raise KamiError(
                "Invalid value of `substrate_bnd_subactor` of LigandModification object:"
                "expected 'gene', 'site' or 'region', got '{}'".format(
                    mod.substrate_bnd_subactor))

        enzyme_bnd_region = None
        enzyme_bnd_site = None
        if mod.enzyme_bnd_region is not None:
            if mod.enzyme_bnd_subactor == "gene":
                enzyme_bnd_region = self.generate_region(
                    nugget, mod.enzyme_bnd_region, enzyme)
                template_rels["bnd_template"][enzyme_bnd_region] = {"left_partner_region"}
                nugget.add_edge(enzyme_bnd_region, enzyme,
                                mod.enzyme_bnd_region.location())
            else:
                raise KamiError(
                    "Cannot add enzyme binding region '{}' to ".format(
                        mod.enzyme_bnd_region.__repr__()) +
                    "the enzyme binding subactor: " +
                    "subactor is of type '{}'".format(
                        mod.enzyme_bnd_subactor))
        elif mod.enzyme_bnd_subactor == "region":
            enzyme_bnd_region = enzyme_region

        if mod.enzyme_bnd_site is not None:
            if mod.enzyme_bnd_subactor == "site":
                raise KamiError(
                    "Cannot add enzyme binding site '{}' to ".format(
                        mod.enzyme_bnd_site.__repr__()) +
                    "the enzyme binding subactor: " +
                    "subactor is of type 'site'")
            else:
                if enzyme_bnd_region is not None:
                    father = enzyme_bnd_region
                else:
                    father = enzyme
                enzyme_bnd_site = self.generate_site(
                    nugget, mod.enzyme_bnd_site, father, enzyme)
                template_rels["bnd_template"][enzyme_bnd_site] = {"left_partner_site"}
                if enzyme_bnd_region is not None:
                    nugget.add_edge(
                        enzyme_bnd_site, enzyme_bnd_region,
                        mod.enzyme_bnd_site.location())
                else:
                    nugget.add_edge(enzyme_bnd_site, enzyme,
                                    mod.enzyme_bnd_site.location())
        elif mod.enzyme_bnd_subactor == "site":
            enzyme_bnd_site = enzyme_site

        substrate_bnd_region = None
        substrate_bnd_site = None
        if mod.substrate_bnd_region is not None:
            if mod.substrate_bnd_subactor == "gene":
                substrate_bnd_region = self.generate_region(
                    nugget, mod.substrate_bnd_region, substrate)
                nugget.add_edge(substrate_bnd_region, substrate,
                                mod.substrate_bnd_region.location())
                template_rels["bnd_template"][substrate_bnd_region] = {"right_partner_region"}
            else:
                raise KamiError(
                    "Cannot add substrate binding region '{}' to ".format(
                        mod.substrate_bnd_region.__repr__()) +
                    "the substrate binding subactor: " +
                    "subactor is of type '{}'".format(
                        mod.substrate_bnd_subactor))
        elif mod.substrate_bnd_subactor == "region":
            substrate_bnd_region = substrate_region

        if mod.substrate_bnd_site is not None:
            if mod.substrate_bnd_subactor == "site":
                raise KamiError(
                    "Cannot add substrate binding site '{}' to ".format(
                        mod.substrate_bnd_site.__repr__()) +
                    "the substrate binding subactor: " +
                    "subactor is of type 'site'")
            else:
                if substrate_bnd_region is not None:
                    father = substrate_bnd_region
                else:
                    father = substrate
                substrate_bnd_site = self.generate_site(
                    nugget, mod.substrate_bnd_site, father, substrate)
                template_rels["bnd_template"][substrate_bnd_site] = {"right_partner_site"}
                if substrate_bnd_region is not None:
                    nugget.add_edge(
                        substrate_bnd_site, substrate_bnd_region,
                        mod.substrate_bnd_site.location())
                else:
                    nugget.add_edge(substrate_bnd_site, substrate,
                                    mod.substrate_bnd_site.location())
        elif mod.substrate_bnd_subactor == "site":
            substrate_bnd_site = substrate_site

        nugget.add_node("is_bnd", attrs={"type": "be", "test": True},
                        meta_typing="bnd")
        template_rels["bnd_template"]["is_bnd"] = {"bnd"}

        if enzyme_bnd_site is not None:
            nugget.add_edge(enzyme_bnd_site, "is_bnd")
        elif enzyme_bnd_region is not None:
            nugget.add_edge(enzyme_bnd_region, "is_bnd")
        else:
            nugget.add_edge(enzyme, "is_bnd")

        if substrate_bnd_site is not None:
            nugget.add_edge(substrate_bnd_site, "is_bnd")
        elif substrate_bnd_region is not None:
            nugget.add_edge(substrate_bnd_region, "is_bnd")
        else:
            nugget.add_edge(substrate, "is_bnd")

        return (
            nugget, "mod",
            template_rels,
            mod.desc
        )


def generate_nugget(corpus, interaction, readonly=False):
    """Generate nugget from an interaction object."""
    hierarchy = None
    graph_id = None
    meta_model_id = None
    if not readonly:
        hierarchy = corpus._hierarchy
        graph_id = corpus._action_graph_id
        meta_model_id = "meta_model"

    if corpus.action_graph is None:
        corpus.create_empty_action_graph()

    identifier = EntityIdentifier(
        corpus.action_graph,
        corpus.get_action_graph_typing(),
        hierarchy=hierarchy,
        graph_id=graph_id,
        meta_model_id=meta_model_id)
    if isinstance(interaction, Modification):
        gen = ModGenerator(identifier)
    elif isinstance(interaction, SelfModification):
        gen = SelfModGenerator(identifier)
    elif isinstance(interaction, AnonymousModification):
        gen = AnonymousModGenerator(identifier)
    elif isinstance(interaction, LigandModification):
        gen = LigandModGenerator(identifier)
    elif isinstance(interaction, Binding) or\
            isinstance(interaction, Unbinding):
        gen = BndGenerator(identifier)
    else:
        raise KamiError(
            "Unknown type of interaction '{}'".format(type(interaction)))
    return gen.generate(interaction)
