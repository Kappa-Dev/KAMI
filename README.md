# KAMI: Knowledge Aggregator and Model Instantiator

## About project

## Configuration

## KAMI Hierarchy

## Imports from other formats

### INDRA

## Exports to other formats

### Kappa

### INDRA

## KAMI Gui

The **RegraphGui** is a javascript library for Regraph
Hierarchy can be added, edited, merged and removed.
The UI is dumb : due to the current implementation of regraph, it reload the whole graph or hierarchy on each update.
This UI is autonomus and only need itself to work.... and a regraph server.

### Configuration
To configure the ui, simply edit the index.js file.
Change the server url and if needed the root node name.

### Usage

Top tab allow hierachy navigation and loading,adding and exporting graph or hierarchy.
to select a graph, click on its name, to go inside it, double click on its name. to go back, select another level in the hierarchy selector on the right

The side menu allow to remove selected graph and all the hierarchy behind.
It also allow graph merging using matching : (beta format).

The main div contain the graph associated with the selected tab.
This graph can be edited with right click
The ui can be zoomed and dragged with mousewheel
Nodes and edges are editable.
some node edition require to select other nodes : to do so : shift click on it.
To lock or unlock a node : ctrl click on it.
The main graph is associated with a force simulator witch is reseted at each graph modification.


