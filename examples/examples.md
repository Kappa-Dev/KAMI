# Examples
## Installation
 1. Create a virtual environment named venv

    ```
    virtualenv venv -p path/to/your/python3
    ```

 1.  Activate it

     ```
     source venv/bin/activate
     ```
1. Install the ReGraph library.

    ```
    git clone https://github.com/Kappa-Dev/ReGraph.git
    cd ReGraph
    pip install -r requirements.txt
    pip install -e .
    ```
1. get and install kami

    ```
    cd ..
    git clone https://github.com/Kappa-Dev/KAMI.git
    cd KAMI
    pip install lxml
    pip install -e .
    ```
## Launching KAMI
```
 python3 kami/server/webserver.py
```
Then connect to the server at address http://localhost:5000 using a web browser. We use chrome for this as KAMI appears to run best on it (which results in a lack of testing for other browsers). 


## Examples

First import the examples.json file using the hamberger menu 

### The hierarchy
On the left side is the graph hierarchy browser that should contain a graph named **kami_base**.
Clicking on it once displays the **kami_base** graph.
Double clicking on it, is similar to entering a folder, that contains other graphs *typed* by the **kami_base graph** (in this case a graph called **kami**).

>A *typing* of a graph assigns to each of its nodes a node from another graph (this other node is called its *type*). This mapping must preserve edges and nodes attributes.

Clicking on the **kami** graph displays it.
![action_graph](images/kami.png)
The nodes of this graph will be the types of the nodes of our models. For instance, nodes of type **agent** will end up being kappa agents. 

Double clicking on kami, we discover the *action graph* called **example_action_graph**. As before, clicking on it displays it.
The action graph is an overview of the model used to:
* visualize and explore the model. 
* define the various components and put constrains the actual (kappa like) rules we can express. This is because these rules are themselves represented as graphs that are typed by the action graph.

![action_graph](images/action_graph.png)
We can see some example rules by double clicking on the **example_action_graph** name. 

### The example rules
We call these rules *nuggets* in kami.
Some of them may actually result in multiple kappa rules. We can generate kappa code by left-clicking on any rule, then selecting the rules we want to use, then clicking the "Get kappa button".

#### simple_bind
![action_graph](images/simple_bind.png)
For this example we can think of the loci **locus** and **j1** as kappa site. Agents **A** and **C** as kappa agents. Locus **locus** being situated on a region of agent **C** named **region**.

In kappa, this nugget represents the binding rule of site **j1** of agent **A** to site **region_locus** of agent **C**.

#### simple_brk
![action_graph](images/simple_brk.png)
This is the opposite rule of **simple_bind** specifying the the agents can break appart.

#### bnd_test_bnd
![action_graph](images/bnd_test_bnd.png)
This nugget adds a test (a trigle node) to the binding rule. Site **i4_i** of Agent **A** must be bound to site **a3_a** of Agent **B** for this binding rule between **A** and **C** to happen.

#### bnd_test_state_1
![action_graph](images/bnd_test_state_1.png)
This nugget tests the value of state **state**. It must be **p** of the binding rule cannot apply.
> Unlike in kappa, states sites are disjoints from binding sites in kami. 

#### bnd_test_state_2
![action_graph](images/bnd_test_state_2.png)
This nugget has the same meaning as the previous one. We can implicitly put the value of the test on the state instead of using a explicit test nodes (but tests nodes are still usefull in other cases).

#### mod_state
![action_graph](images/mod_state.png)
This nuggets modifies the value of state **state** of agent **C**, from **u** to **p**

#### undistinguishable_bnd
![action_graph](images/undistinguishable_bnd.png)
This nuggets represents twelve different kappa rules. From any of the sites **a1_a, a2_a or a3_a** of agent **B** to any of the sites **i1_i, i2_i, i3_i, i4_i** of agent A.

 #### undistinguishable_brk
![action_graph](images/undistinguishable_brk.png)
 This nuggets generates the twelve unbinding rules that reverse the bindings ones from undistinguishable_bnd.