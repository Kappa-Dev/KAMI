#! /usr/bin/python3

# Default usage of the "agent anatomizer".

from anatomizer2 import AgentAnatomy
import json


agent = AgentAnatomy('stat6')

agent.get_proteins()
agent.proteins()

agent.get_features()
#agent.features()

agent.merge_features()
#agent.mergedfeatures()

agent.nest_features()
agent.nestedfeatures()

agent.kami()

