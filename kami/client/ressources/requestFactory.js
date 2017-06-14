/* Create request for the regraph server.
 *  see usercontent.com/Kappa-Dev/ReGraph/master/iRegraph_api.yaml for more details about requests
 * @ Author Adrien Basso blandin
 * This module is part of regraphGui project
 * this project is under AGPL Licence
*/
define(["ressources/d3/d3.js"], function (d3) {
	return function RequestFactory(url) {
		var self = this;
		var srv = url;
		/* Uniformized request function
		 * @input : type : the request type : POST/GET/DELETE/PUT
		 * @input : loc : the request path : /hierarchy,/rule,/graph 
		 * (load the above link into http://petstore.swagger.io/ for more informations)
		 * @input : path : the path of the object in the hierarchy
		 * @input : urlparam : all the url parameters as a list of {id:string,val:string}
		 * @input : content_type : the mimeType of the request
		 * @input : callback : The callback function if the request succeed
		 * callback function is of type : function callback(error,response){}
		 * @input : data : if the request is a post request, add those data to the request body
		 * @input : rsp_pars : a parser to call on the response before calling the callback function
		 * @return : the callback function
		 */
		function request(type, loc, path, urlparam, content_type, callback, data, rsp_pars) {
			var url_param_string = "";
			if (urlparam && urlparam.length > 0) {
				url_param_string = urlparam.reduce(function (accu, e, i) {
					return accu += e.id + "=" + e.val + (i < urlparam.length - 1 ? "&" : "");
				}, "?");
			}
			var isSlash = (path && path != "/") ? "/" : "";
			var rq = d3.request(srv + loc + path + isSlash + url_param_string)
				.mimeType(content_type)
				.response(function (xhr) { return rsp_pars ? rsp_pars(xhr.responseText) : xhr.responseText; })
				.on("error", function (error) { errorCb(error); })
			if (type == "POST")
				rq.header("X-Requested-With", "XMLHttpRequest")
			rq.on("load", function (xhr) { callback(null, xhr); });
			rq.send(type, data);
		};
		/* Generic Error handler for request
		 * @input : error : the error returned by the request
		 * @return : console error message
		 */
		function errorCb(error) {
			if (error.currentTarget.status != 0) {
				alert(error.currentTarget.status + " : " + error.currentTarget.statusText + "\n" + error.currentTarget.response);
			} else alert("Unexpected Server Error");
			console.error("unable to complete request :");
			console.error(error);
		}
		/* get all the hierarchy starting from a graph
		 * @input : hie_path : the root path
		 * @input : callback : the return callback function
		 * @return : on succeed : callback function
		 */
		this.getHierarchy = function getHierarchy(hie_path, callback) {
			request("GET",
				"/hierarchy",
				hie_path,
				[{ id: "include_graphs", val: false }, { id: "rules", val: true }],
				"application/json",
				callback,
				null,
				JSON.parse);
		};
		this.getHierarchyWithGraphs = function getHierarchyWithGraphs(hie_path, callback) {
			request("GET",
				"/hierarchy",
				hie_path,
				[{ id: "include_graphs", val: true }, { id: "rules", val: false }],
				"application/json",
				callback,
				null,
				JSON.parse);
		};

		this.getGraphAndDirectChildren = function (hie_path, callback) {
			request("GET",
				"/hierarchy",
				hie_path,
				[{ id: "include_graphs", val: true }, { id: "rules", val: false }, { depth_bound: 1 }],
				"application/json",
				callback,
				null,
				JSON.parse);
		};
		/* return the regraph version on the server
		 * @input : callback  : the return callback function
		 * @return : on succeed : callback function
		 */
		this.getVersion = function getVersion(callback) {
			request("GET",
				"/version",
				"",
				null,
				"text/html",
				callback,
				null,
				null
			)
		};
		/* get a graph in json format
		 * @input : gr_path : the graph path
		 * @input : callback : the return callback function
		 * @return : on succeed : callback function
		 */
		this.getGraph = function getGraph(gr_path, callback) {
			request("GET",
				"/graph",
				gr_path,
				null,
				"application/json",
				callback,
				null,
				JSON.parse);
		};

		this.promGetGraph = function (g_path) {
			return new Promise(function (resolve, reject) {
				let myCallback = function (err, rep) {
					if (err) { reject(err) }
					else {
						resolve(JSON.parse(rep.response));
					}
				}
				d3.request(srv + "/graph" + g_path + "/").get(myCallback);
			});
		}

		/* get a graph in json format, without callback override for fail case
		 * @input : gr_path : the graph path
		 * @input : callback : the return callback function
		 * @return : on succeed : callback function
		 */
		// this.getGraph2 = function getGraph2(gr_path,callback){
		// 	d3.request(srv+"/graph"+gr_path+"/")
		// 		// .header("X-Requested-With", "XMLHttpRequest")
		// 		// .header("Content-Type", "application/json")
		// 		.get(callback);
		// };




		/* return the possible matchings for a rule on the graph
		 * @input : gr_path : the graph path
		 * @input : rule_path : the rule path
		 * @input : callback : the return callback function
		 * @return : on succeed : callback function
		 */
		this.getMatching = function getMatching(gr_path, rule_path, callback) {
			request("GET",
				"/graph/matchings",
				gr_path,
				[{ id: "rule_name", val: rule_path }],
				"application/json",
				callback,
				null,
				JSON.parse);
		};
		/* return a specific rule of a graph
		 * @input : gr_path : the graph path
		 * @input : rule_name : the rule name
		 * @input : callback : the return callback function
		 * @return : on succeed : callback function
		 */
		this.getRule = function getRule(gr_path, callback) {
			request("GET",
				"/rule",
				gr_path,
				null,
				"application/json",
				callback,
				// function(err,resp){return callback(err,subRule(rule_name,resp))},
				null,
				JSON.parse);
		};
		/* find a specific rule in a graph
		 * @input : r_name : the rule name
		 * @input : resp : the graph as a hierarchy
		 * @return : the requested rule
		 */
		function subRule(r_name, resp) {
			if (!resp.rules) {
				console.error("this hierarchy has no rules");
				return {};
			}
			var r_idx = resp.rules.indexOf(r_name);
			if (r_idx < 0) throw new Error("unable to find this rule : " + r_name)
			return resp.rules[r_idx];
		};
		/* delete a graph and all its children
		 * @input : hie_path : the hierarchy path
		 * @input : callback : the return callback function
		 * @return : on succeed : callback function
		 */
		this.delHierarchy = function delHierarchy(hie_path, callback) {
			request("DELETE",
				"/hierarchy",
				hie_path,
				null,
				"text/html",
				callback,
				null,
				null);
		};
		/* add a new hierarchy as a child of a specific graph
		 * @input : hie_path : the path of the hierarchy father
		 * @input : data : the hierarchy as a json stringified object
		 * @input : callback : the return callback function
		 * @return : on succeed : callback function
		 */
		this.addHierarchy = function addHierarchy(hie_path, data, callback) {
			d3.request(srv + "/hierarchy" + hie_path)
				.header("X-Requested-With", "XMLHttpRequest")
				.header("Content-Type", "application/json")
				.post(data, callback);
		};
		/* merge two hierarchies
		 * both hierarchies must have the same name and graph
		 * @input : hie_path : the path of the hierarchy
		 * @input : data : the hierarchy as a json stringified object
		 * @input : callback : the return callback function
		 * @return : on succeed : callback function
		 * TODO : transforming this function in something usefull
		 */
		this.mergeHierarchy = function mergeHierarchy(hie_path, data, callback) {
			var rq = d3.request(srv + "/hierarchy" + hie_path)
				.header("X-Requested-With", "XMLHttpRequest")
				.header("Content-Type", "application/json")
				.mimeType("application/json")
				.on("error", function (error) { callback(error, null); })
				.on("load", function (xhr) { callback(null, xhr); });
			rq.send("PUT", data);
		};

		this.mergeHierarchy2 = function mergeHierarchy2(hie_path, data, callback) {
			var rq = d3.request(srv + "/hierarchy2" + hie_path)
				.header("X-Requested-With", "XMLHttpRequest")
				.header("Content-Type", "application/json")
				.mimeType("application/json")
				.on("error", function (error) { callback(error, null); })
				.on("load", function (xhr) { callback(null, xhr); });
			rq.send("PUT", data);
		};
		/* create a new rule
		 * @input : rule_path : the path of rule
		 * @input : pattern : the rule pattern to match.
		 * @input : callback : the return callback function
		 * @return : on succeed : callback function
		 */
		this.addRule = function addRule(rule_path, pattern, callback) {
			d3.request(srv + "/rule" + encodeURIComponent(rule_path) + "?pattern_name=" + pattern)
				.header("X-Requested-With", "XMLHttpRequest")
				.header("Content-Type", "application/json")
				.post(null, callback);
		};
		/* create a new graph by applying a rule
		 * @input : graph_path : the path of graph
		 * @input : src_gr : the graph used to apply the rule.
		 * @input : rule_n : the rule name (this rule must be part of the source graph)
		 * @input : data : the specific pattern used in the graph
		 * @input : callback : the return callback function
		 * @return : on succeed : callback function
		 */
		this.graphFromRule = function graphFromRule(graph_path, src_gr, rule_n, data, callback) {
			d3.request(srv + "/graph/apply" + graph_path + "?target_graph=" + src_gr + "&rule_name=" + rule_n)
				.header("X-Requested-With", "XMLHttpRequest")
				.header("Content-Type", "application/json")
				.post(data, callback);
		};
		/* delete a graph
		 * @input : gr_path : the graph path
		 * @input : callback : the return callback function
		 * @return : on succeed : callback function
		 */
		this.delGraph = function delGraph(gr_path, callback) {
			request("DELETE",
				"/graph",
				gr_path,
				null,
				"text/html",
				callback,
				null,
				null);
		};

		this.renameNode = function (graph_path, node_id, new_name, callback) {
			request("PUT",
				"/graph/rename_node",
				graph_path,
				[{ id: "node_id", val: node_id }, { id: "new_name", val: new_name }],
				"text/html",
				callback,
				null,
				null);
		};

		/* add a node to a graph
		 * @input : g_path : the graph path
		 * @input : n_id : the node id
		 * @input : n_type : the node type (must be a type present in the graph father)
		 * @input : callback : the return callback function
		 * @return : on succeed : callback function
		 */
		this.addNode = function addNode(g_path, n_id, n_type, callback) {
			request("PUT",
				"/graph/add_node",
				g_path,
				[{ id: "node_id", val: n_id }, { id: "node_type", val: (n_type ? n_type : "") }],
				"text/html",
				callback,
				null,
				null);
		};
		/* remove a node from a graph
		 * @input : g_path : the graph path
		 * @input : n_id : the node id
		 * @input : force : boolean
		 * force operation and delete all the nodes typed by this one in children graphs
		 * else, if the node has children, return an error
		 * @input : callback : the return callback function
		 * @return : on succeed : callback function
		 */
		this.rmNode = function rmNode(g_path, n_id, force, callback) {
			request("PUT",
				"/graph/rm_node",
				g_path,
				[{ id: "node_id", val: n_id }, { id: "force", val: force }],
				"text/html",
				callback,
				null,
				null);
		};
		/* add new attributes to an existing node
		 * @input : g_path : the graph path
		 * @input : n_id : the node id
		 * @input : dico : a dictonnary of values
		 * @input : callback : the return callback function
		 * @return : on succeed : callback function
		 */
		this.addNodeAtt = function addNodeAtt(g_path, n_id, dico, callback) {
			var rq = d3.request(srv + "/graph/add_attr" + g_path + "?node_id=" + encodeURIComponent(n_id))
				.header("X-Requested-With", "XMLHttpRequest")
				.header("Content-Type", "application/json")
				.mimeType("application/json")
				.on("error", function (error) { callback(error, null); })
				.on("load", function (xhr) { callback(null, xhr); });
			rq.send("PUT", dico);
		};
		/* remove specified attrobutes from an existing node
		 * @input : g_path : the graph path
		 * @input : n_id : the node id
		 * @input : dico : a dictonnary of values
		 * @input : callback : the return callback function
		 * @return : on succeed : callback function
		 */
		this.rmNodeAtt = function rmNodeAtt(g_path, n_id, dico, callback) {
			var rq = d3.request(srv + "/graph/rm_attr" + g_path + "?node_id=" + encodeURIComponent(n_id))
				.header("X-Requested-With", "XMLHttpRequest")
				.header("Content-Type", "application/json")
				.mimeType("application/json")
				.on("error", function (error) { callback(error, null); })
				.on("load", function (xhr) { callback(null, xhr); });
			rq.send("PUT", dico);
		};
		/* merge two nodes of the same type
		 * @input : g_path : the graph path
		 * @input : n_id1 : the first node id
		 * @input : n_id2 : the second node id
		 * @input : new_id : the merged node id
		 * @input : force : boolean
		 * force the merging, nodes type by either one will be typed by the new node
		 * else, if the node has children, return an error
		 * @input : callback : the return callback function
		 * @return : on succeed : callback function
		 */
		this.mergeNode = function mergeNode(g_path, n_id1, n_id2, new_id, force, callback) {
			request("PUT",
				"/graph/merge_node",
				g_path,
				[{ id: "force", val: force }, { id: "node1", val: n_id1 }, { id: "node2", val: n_id2 }, { id: "new_node_id", val: new_id }],
				"text/html",
				callback,
				null,
				null);
		};
		/* clone a node
		 * @input : g_path : the graph path
		 * @input : n_id : the node id
		 * @input : new_id : the cloned node id
		 * @input : callback : the return callback function
		 * @return : on succeed : callback function
		 */
		this.cloneNode = function cloneNode(g_path, n_id, new_id, callback) {
			request("PUT",
				"/graph/clone_node",
				g_path,
				[{ id: "node_id", val: n_id }, { id: "new_node_id", val: new_id }],
				"text/html",
				callback,
				null,
				null);
		};
		/* add an edge to a graph (an edge between src and trg type must exist)
		 * @input : g_path : the graph path
		 * @input : src : the source node id
		 * @input : trg : the target node id
		 * @input : callback : the return callback function
		 * @return : on succeed : callback function
		 */
		this.addEdge = function addEdge(g_path, src, trg, callback) {
			request("PUT",
				"/graph/add_edge",
				g_path,
				[{ id: "source_node", val: encodeURIComponent(src) }, { id: "target_node", val: encodeURIComponent(trg) }],
				"text/html",
				callback,
				null,
				null);
		};
		/* remove an edge from a graph
		 * @input : g_path : the graph path
		 * @input : src : the source node id
		 * @input : trg : the target node id
		 * @input : force : boolean
		 * force the deletion and propagate to children
		 * else, if the node has children, return an error
		 * @input : callback : the return callback function
		 * @return : on succeed : callback function
		 */
		this.rmEdge = function rmEdge(g_path, src, trg, force, callback) {
			request("PUT",
				"/graph/rm_edge",
				g_path,
				[{ id: "source_node", val: src }, { id: "target_node", val: trg }, { id: "force", val: force }],
				"text/html",
				callback,
				null,
				null);
		};
		/* rename a graph
		 * @input : g_path : the graph path
		 * @input : name : the new name of the graph
		 * @input : callback : the return callback function
		 * @return : on succeed : callback function
		 */
		this.rnGraph = function rnGraph(g_path, name, callback) {
			request("PUT",
				"/graph/rename_graph",
				g_path,
				[{ id: "new_name", val: name }],
				"text/html",
				callback,
				null,
				null);
		};
		/* create a new empty graph
		 * @input : gr_path : the graph path
		 * @input : callback : the return callback function
		 * @return : on succeed : callback function
		 */
		this.addGraph = function addGraph(gr_path, callback) {
			d3.request(srv + "/graph" + gr_path)
				.header("X-Requested-With", "XMLHttpRequest")
				.post(null, callback);
		};
		/* add a node to a rule
		 * @input : g_path : the rule path
		 * @input : n_id : the node id
		 * @input : n_type : the node type (must be a type present in the graph father)
		 * @input : callback : the return callback function
		 * @return : on succeed : callback function
		 */
		this.ruleaddNode = function ruleaddNode(g_path, n_id, n_type, callback) {
			request("PUT",
				"/rule/add_node",
				g_path,
				[{ id: "node_id", val: n_id }, { id: "node_type", val: n_type }],
				"text/html",
				callback,
				null,
				null);
		};
		/* remove a node from a rule
		 * @input : g_path : the rule path
		 * @input : n_id : the node id
		 * @input : callback : the return callback function
		 * @return : on succeed : callback function
		 */
		this.rulermNode = function rulermNode(g_path, n_id, callback) {
			request("PUT",
				"/rule/rm_node",
				g_path,
				[{ id: "node_id", val: n_id }],
				"text/html",
				callback,
				null,
				null);
		};
		/* merge two nodes of the same type in a Rule
		 * @input : g_path : the rule path
		 * @input : n_id1 : the first node id
		 * @input : n_id2 : the second node id
		 * @input : new_id : the merged node id
		 * @input : force : boolean
		 * force the merging, nodes type by either one will be typed by the new node
		 * else, if the node has children, return an error
		 * @input : callback : the return callback function
		 * @return : on succeed : callback function
		 */
		this.rulemergeNode = function rulemergeNode(g_path, n_id1, n_id2, new_id, force, callback) {
			request("PUT",
				"/rule/merge_node",
				g_path,
				[{ id: "node1", val: n_id1 }, { id: "node2", val: n_id2 }, { id: "new_node_id", val: new_id }, { id: "force", val: force }],
				"text/html",
				callback,
				null,
				null);
		};
		/* clone a node in a Rule
		 * @input : g_path : the rule path
		 * @input : n_id : the node id
		 * @input : new_id : the cloned node id
		 * @input : callback : the return callback function
		 * @return : on succeed : callback function
		 */
		this.rulecloneNode = function rulecloneNode(g_path, n_id, new_id, callback) {
			request("PUT",
				"/rule/clone_node",
				g_path,
				[{ id: "node_id", val: n_id }, { id: "new_node_id", val: new_id }],
				"text/html",
				callback,
				null,
				null);
		};
		/* add an edge to a rule (an edge between src and trg type must exist)
		 * @input : g_path : the rule path
		 * @input : src : the source node id
		 * @input : trg : the target node id
		 * @input : callback : the return callback function
		 * @return : on succeed : callback function
		 */
		this.ruleaddEdge = function ruleaddEdge(g_path, src, trg, callback) {
			request("PUT",
				"/rule/add_edge",
				g_path,
				[{ id: "source_node", val: src }, { id: "target_node", val: trg }],
				"text/html",
				callback,
				null,
				null);
		};
		/* remove an edge from a rule
		 * @input : g_path : the rule path
		 * @input : src : the source node id
		 * @input : trg : the target node id
		 * @input : callback : the return callback function
		 * @return : on succeed : callback function
		 */
		this.rulermEdge = function rulermEdge(g_path, src, trg, callback) {
			request("PUT",
				"/rule/rm_edge",
				g_path,
				[{ id: "source_node", val: src }, { id: "target_node", val: trg }],
				"text/html",
				callback,
				null,
				null);
		};
		/* rename a rule
		 * @input : g_path : the rule path
		 * @input : name : the new name of the graph
		 * @input : callback : the return callback function
		 * @return : on succeed : callback function
		 */
		this.rnRule = function rnRule(g_path, name, callback) {
			request("PUT",
				"/rule/rename_rule",
				g_path,
				[{ id: "new_name", val: name }],
				"text/html",
				callback,
				null,
				null);
		};
		/* add a constraint to a node
		 * @input : g_path : the graph path
		 * @input : n_id : the node id
		 * @input : e_type : the type of edge : input our output
		 * @input : cstr : the type of the node to constraint
		 * @input : bnd : the bound val of this constraint
		 * @input : order : the bound type of this constraint : le (<=) or ge (>=)
		 * @input : callback : the return callback function
		 * @return : on succeed : callback function
		 */
		this.addConstraint = function addConstraint(g_path, n_id, e_type, cstr, bnd, order, callback) {
			request("PUT",
				"/graph/add_constraint",
				g_path,
				[{ id: "node_id", val: n_id },
				{ id: "input_or_output", val: e_type },
				{ id: "constraint_node", val: cstr }, { id: "bound", val: bnd }, { id: "le_or_ge", val: order }],
				"text/html",
				callback,
				null,
				null);
		};
		/* remove a constraint from a node
		 * @input : g_path : the graph path
		 * @input : n_id : the node id
		 * @input : e_type : the type of edge : input our output
		 * @input : cstr : the type of the node to constraint
		 * @input : bnd : the bound val of this constraint
		 * @input : order : the bound type of this constraint : le (<=) or ge (>=)
		 * @input : callback : the return callback function
		 * @return : on succeed : callback function
		 */
		this.rmConstraint = function rmConstraint(g_path, n_id, e_type, cstr, bnd, order, callback) {
			request("PUT",
				"/graph/delete_constraint",
				g_path,
				[{ id: "node_id", val: n_id },
				{ id: "input_or_output", val: e_type },
				{ id: "constraint_node", val: cstr }, { id: "bound", val: bnd }, { id: "le_or_ge", val: order }],
				"text/html",
				callback,
				null,
				null);
		};
		/* check the constraints to validate a graph
		 * @input : g_path : the graph path
		 * @input : callback : the return callback function
		 * @return : on succeed : callback function of string list
		 */
		this.validate = function validate(g_path, callback) {
			request("PUT",
				"/graph/validate_constraint",
				g_path,
				null,
				"text/html",
				callback,
				null,
				null);
		};
		/* get meta-data from graphs
		 * @input : g_path : the graph path
		 * @input : callback : the return callback function
		 * @return : on succeed : callback function of dictionary
		 */
		this.getAttr = function getAttr(g_path, callback) {
			request("GET",
				"/graph/get_graph_attr",
				g_path,
				null,
				"application/json",
				callback,
				null,
				JSON.parse);
		};
		/* add attributes to a graph (coordinate, node shape/colors)
		 * @input : g_path : the graph path
		 * @input : dico : the new dictonnary (will be merged)
		 * @input : callback : the return callback function
		 * @return : on succeed : callback function
		 */
		this.addAttr = function addAttr(hie_path, data, callback) {
			var rq = d3.request(srv + "/graph/update_graph_attr" + hie_path)
				.header("X-Requested-With", "XMLHttpRequest")
				.header("Content-Type", "application/json")
				.mimeType("application/json")
				.on("error", function (error) { callback(error, null); })
				.on("load", function (xhr) { callback(null, xhr); });
			rq.send("PUT", data);
		};
		
        this.promAddAttr = callbackToPromise(self.addAttr);

		function callbackToPromise(f) {
			return function () {
				let args = arguments;
				return new Promise(function (resolve, reject) {
					let myCallback = function (err, _rep) {
						if (err) { reject(err) }
						else {
							resolve();
						}
					}
					f(...args, myCallback);
				})
			}
		}

		// 	request("PUT",
		// 		"/graph/update_graph_attr",
		// 		g_path,
		// 		null,
		// 		"application/json",
		// 		callback,
		// 		dico,
		// 		null);
		// };
		/* remove attributes from a graph (coordinate, node shape/colors)
		 * @input : g_path : the graph path
		 * @input : dico_pth : the path to the element we want to remove
		 * @input : callback : the return callback function
		 * @return : on succeed : callback function
		 */
		this.rmAttr = function rmAttr(g_path, data, callback) {
			var rq = d3.request(srv + "/graph/delete_graph_attr" + g_path)
				.header("X-Requested-With", "XMLHttpRequest")
				.header("Content-Type", "application/json")
				.mimeType("application/json")
				.on("error", function (error) { callback(error, null); })
				.on("load", function (xhr) { callback(null, xhr); });
			rq.send("PUT", data);
		};
		/* get regraph version
		 * @input : callback : the return callback function
		 * @return : on succeed : callback function of dictionary
		 */
		this.getVersion = function getVersion(callback) {
			request("GET",
				"/version",
				null,
				null,
				"application/json",
				callback,
				null,
				JSON.parse);
		};
		/* submit a list and nugget and recieve the corresponding kappa code
		 * @input : g_path : the graph path
		 * @input : nuggets : the list of nugget names { "names": ["string"]}
		 * @input : callback : the return callback function
		 * @return : on succeed : callback function of dictionary
		 */
		this.getKappa = function getKappa(g_path, nuggets, callback) {
			d3.request(srv + "/graph/get_kappa" + g_path)
				.header("X-Requested-With", "XMLHttpRequest")
				.header("Content-Type", "application/json")
				.post(nuggets, callback);
		};

		/* submit a list of splices and create the coresponding rewriting rule
		 * @input : g_path : the graph path
		 * @input : splices : the list of splices names { "names": ["string"]}
		 * @input : callback : the return callback function
		 * @return : on succeed : callback function of dictionary
		 */

		this.makeSplices = function makeSplices(g_path, splices, callback) {
			d3.request(srv + "/graph/splices" + g_path)
				.header("X-Requested-With", "XMLHttpRequest")
				.header("Content-Type", "application/json")
				.post(splices, callback);
		};

		this.makeConcat = function makeConcat(g_path, splices, callback) {
			d3.request(srv + "/graph/testconcat" + g_path)
				.header("X-Requested-With", "XMLHttpRequest")
				.header("Content-Type", "application/json")
				.post(splices, callback);
		};

		this.getChildren = function (g_path, n_id, callback) {
			d3.request(srv + "/graph/get_children" + g_path + "?node_id=" + encodeURIComponent(n_id))
				// .header("X-Requested-With", "XMLHttpRequest")
				// .header("Content-Type", "application/json")
				.get(callback);

		};
		/* get a mapping of nodes to ancestors
		 * @input : g_path : the graph path
		 * @input : degree : int > 1, the desired ancestor degree
		 * @input : callback : the return callback function
		 * @return : on succeed : callback function of dictionary
		 */
		this.getAncestors = function (g_path, degree, callback) {
			var myCallback = function (err, rep) {
				if (err) { callback(err, null) }
				else {
					callback(null, JSON.parse(rep.response))
				}
			}
			d3.request(srv + "/graph/get_ancestors" + g_path + "/" + "?degree=" + encodeURIComponent(degree)).get(myCallback);
		};

		function rel_to_object(rel) {
			return rel.reduce(function (obj, x) {
				obj[x["left"]] = x["right"];
				return obj;
			}, {});
		}

		this.promAncestors = function (g_path, degree) {
			return new Promise(function (resolve, reject) {
				let myCallback = function (err, rep) {
					if (err) { reject(err) }
					else {
						resolve(rel_to_object(JSON.parse(rep.response)));
					}
				}
				d3.request(srv + "/graph/get_ancestors" + g_path + "/" + "?degree=" + encodeURIComponent(degree)).get(myCallback);
			});
		}

		this.promGraphTyping = function (graph_path, parent_path) {
			return new Promise(function (resolve, reject) {
				let callback = function (err, rep) {
					if (err) { reject(err) }
					else {
						let mappings = JSON.parse(rep.response)
						Object.keys(mappings).forEach(k => mappings[k] = rel_to_object(mappings[k]));
						resolve(mappings);
					}
				}
				d3.request(srv + "/graph/get_typing" + graph_path + "/" + "?parent=" + encodeURIComponent(parent_path)).get(callback);
			})
		}
		this.promRuleTyping = function (rule_path, parent_path) {
			return new Promise(function (resolve, reject) {
				let callback = function (err, rep) {
					if (err) { reject(err) }
					else {
						let mappings = JSON.parse(rep.response)
						Object.keys(mappings).forEach(k => mappings[k] = rel_to_object(mappings[k]));
						resolve(mappings);
					}
				}
				d3.request(srv + "/rule/get_typing" + rule_path + "/" + "?parent=" + encodeURIComponent(parent_path)).get(callback);
			})
		}

		/* creates a graph from selected nodes
				 * @input : g_path : the graph path
				 * @input : new_name : the name of the new graph
				 * @input : node_list : the selected nodes
				 */

		this.newGraphFromNodes = function (g_path, new_name, node_list, callback) {
			d3.request(srv + "/graph/graph_from_nodes" + g_path + "/" + new_name + "/")
				.header("X-Requested-With", "XMLHttpRequest")
				.header("Content-Type", "application/json")
				.post(JSON.stringify({ "names": node_list }), callback);
		};

		this.promNewGraphFromNodes = callbackToPromise(self.newGraphFromNodes);

		// this.promNewGraphFromNodes = function (g_path, new_name, node_ids) {
		// 	return new Promise(function (resolve, reject) {
		// 		let myCallback = function (err, _rep) {
		// 			if (err) { reject(err) }
		// 			else {
		// 				resolve();
		// 			}
		// 			d3.request(srv + "/graph/graph_from_nodes" + g_path + "/" + new_name + "/")
		// 				.header("X-Requested-With", "XMLHttpRequest")
		// 				.header("Content-Type", "application/json")
		// 				.post(JSON.stringify({ "names": node_ids }), myCallback);
		// 		}
		// 	});
		// }

		/* creates a child rule from selected nodes
				 * @input : g_path : the graph path
				 * @input : new_name : the name of the new graph
				 * @input : node_list : the selected nodes
				 */

		this.newChildRuleFromNodes = function (g_path, new_name, node_list, callback) {
			d3.request(srv + "/rule/child_rule_from_nodes" + g_path + "/" + new_name + "/")
				.header("X-Requested-With", "XMLHttpRequest")
				.header("Content-Type", "application/json")
				.post(JSON.stringify({ "names": node_list }), callback);
		};

		this.promChildRuleFromNodes = callbackToPromise(self.newChildRuleFromNodes);

		this.applyRuleOnParent = function (rule_path, suffix, callback) {
			d3.request(srv + "/rule/apply_on_parent" + rule_path + "/?suffix=" + encodeURIComponent(suffix))
				.header("X-Requested-With", "XMLHttpRequest")
				.header("Content-Type", "application/json")
				.post(null, callback);
		};

		this.mergeGraphs = function (g_path, new_name, graphLeft, graphRight, relation, callback) {
			d3.request(srv + "/graph/merge_graphs" + g_path + "/" +
				encodeURIComponent(new_name) + "/" + "?graph1=" + graphLeft + "&graph2=" + graphRight)
				.header("X-Requested-With", "XMLHttpRequest")
				.header("Content-Type", "application/json")
				.post(JSON.stringify(relation), callback);
		};

		this.checkFormulae = function (g_path, callback) {
			d3.request(srv + "/graph/check" + g_path + "/")
				.get(callback);
		};

		this.addGraph = function (g_path, callback) {
			d3.request(srv + "/graph" + g_path)
				.header("X-Requested-With", "XMLHttpRequest")
				.post(null, callback);
		};

		this.promAddGraph = function (g_path) {
			return new Promise(function (resolve, reject) {
				let myCallback = function (err, _rep) {
					if (err) { reject(err) }
					else {
						resolve();
					}
				}
				self.addGraph(g_path, myCallback);
			})
		}

		this.getParts = function (g_path, callback) {
			d3.request(srv + "/getparts" + g_path + "/")
				.get(callback);
		};

		this.getTypes = function (g_path, nodeId, callback) {
			d3.request(srv + "/gettypes" + g_path + "/?nodeId=" + nodeId)
				.get(callback);
		};

		this.getMetadata = function (g_path, callback) {
			d3.request(srv + "/graph/get_metadata" + g_path)
				.get((err, rep)=>{callback(err, JSON.parse(rep.response))});
		};

		this.pasteNodes = function (g_path, parent_path, node_list, mousepos, callback) {
			let rq = d3.request(srv + "/graph/paste" + g_path + "/" + "?parent=" + encodeURIComponent(parent_path))
				.header("X-Requested-With", "XMLHttpRequest")
				.header("Content-Type", "application/json")
				.on("error", function (error) { callback(error, null); })
				.on("load", function (xhr) { callback(null, xhr); });
			rq.send("PUT", JSON.stringify({ "nodes": node_list, "mouseX": mousepos[0], "mouseY": mousepos[1]}), callback);
		};

	}
});
