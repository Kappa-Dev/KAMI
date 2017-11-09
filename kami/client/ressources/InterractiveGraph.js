/* This module add the graph container to the UI
 * this module trigger graphUpdate events
 * @ Author Adrien Basso blandin
 * This module is part of regraphGui project
 * this project is under AGPL Licence
 */
define([
    "ressources/d3/d3.js",
    "ressources/d3/d3-context-menu.js",
    "ressources/requestFactory.js",
    "ressources/inputMenu.js",
    "ressources/newNodeSelect.js"

], function (d3, d3ContextMenu, RqFactory, inputMenu, newNode) {
    /* Create a new interractive graph structure
     * @input : container_id : the container to bind this hierarchy
     * @input : dispatch : the dispatch event object
     * @input : server_url : the regraph server url
     * @return : a new InterractiveGraph object
     */
    return function InterractiveGraph(container_id, new_svg_name, svg_width, svg_height, dispatch, request, readOnly, localDispatch) {
        var disp = dispatch;
        let nodeClipboard = {
            path: null,
            nodes: []
        };
        //var size = d3.select("#"+container_id).node().getBoundingClientRect();//the svg size
        // d3.select("#"+container_id)//the main svg object
        // 	// .append("div")
        // 	// .attr("id","tab_frame")
        // 	.append("svg:svg")

        //var svg = d3.select(document.createElement("svg:svg"))
        var svgDom = document.createElementNS("http://www.w3.org/2000/svg", "svg:svg");
        svgDom.setAttributeNS("http://www.w3.org/2000/xmlns/", "xmlns:xlink", "http://www.w3.org/1999/xlink");

        var svg = d3.select(svgDom)
            .attr("id", new_svg_name)
            .attr("height", svg_height)
            .attr("width", svg_width);

        svg.append('svg:rect')
            .attr('width', svg_width) // the whole width of g/svg
            .attr('height', svg_height) // the whole heigh of g/svg
            .attr('fill', 'none')
            .attr('pointer-events', 'all');
        var width = +svg.attr("width"),
            height = +svg.attr("height"),
            transform = d3.zoomIdentity;
        var svg_content = svg.append("g")//the internal zoom and drag object for svg
            .classed("svg_zoom_content", true);
        var simulation;//the force simulation
        var radius = 30;
        var links_f;//the link force
        //var request = new RqFactory(server_url);
        var g_id = "/";//the graph id in the hierarchy
        var type_list;
        var locked = false;//lock event actions
        var zoom;
        var saveX, saveY;//remember position of node before drag event
        var beginX, beginY;//remember position of node at start of drag
        var startOfLinkNode;//id of node that started the link
        var edgesList;//the edges of the graph
        let newNodeSelect = null;
        let newNodeId = null;
        if (!readOnly) {
            newNodeId = new_svg_name + "NewNode";
            newNodeSelect = new newNode(newNodeId, d3.select("#tab_frame"), dispatch, request, this);
        }
        let existsEdge = function (source, target) {
            return edgesList.some(d => d.source.id == source && d.target.id == target);
        };

        let buttonsDiv = document.createElementNS("http://www.w3.org/1999/xhtml", "div");

        //if not readonly
        createButtons();
        /* initialize all the svg objects and forces
         * this function is self called at instanciation
         */
        (function init() {
            initSvg();
            simulation = d3.forceSimulation();
            // initForce();
        }());
        /* init all the forces
         * this graph has :
         * 	-collision detection
         * 	-link forces : force nodes linked to stay close
         * 	-many bodies forces : repulsing force between nodes
         * 	-center force : foce node to stay close to the center
         */

        function initForce(path, graph, config) {
            simulation.stop();
            simulation.force("link", null);
            simulation.force("chargeAgent", null);
            simulation.force("chargeBnd", null);
            simulation.force("chargeBrk", null);
            simulation.force("link", d3.forceLink().id(function (d) { return d.id; }))
                .force("charge", new d3.forceManyBody().distanceMax(radius * 10))
                .force("center", d3.forceCenter(width / 2, height / 2))
                .force("collision", d3.forceCollide(radius + radius / 4));
            // simulation.on("tick", move);
            simulation.alphaDecay(0.06);
            simulation.stop();
            if (path) {
                loadType(path, graph, config, function (rep) { loadGraph(rep, null, config); });
            }
        }


        function initForceKami(path, graph, config) {
            //simulation = d3.forceSimulation();
            simulation.stop();
            simulation.force("link", null);
            simulation.force("charge", null);
            simulation.force("center", null);
            //simulation.force("center", d3.forceCenter(width / 2, height / 2));
            simulation.force("chargeAgent", null);
            simulation.force("chargeBnd", null);
            simulation.force("chargeBrk", null);
            simulation.force("collision", d3.forceCollide(radius + radius / 4));
            simulation.force("collision").strength(0.3);
            let ancestorArray = config.ancestor_mapping;
            var distanceOfLink = function (l) {
                let edge_length =
                    {
                        "mod": { "state": 150 },
                        "is_equal": { "state": 150 },
                        "state": { "region": 50, "agent": 50, "residue": 50 },
                        "residue": { "agent": 30, "region": 30 },
                        "syn": { "agent": 150 },
                        "agent": { "mod": 150 },
                        "deg": { "agent": 150 },
                        "region": { "agent": 30 },
                        "locus": { "agent": 150, "region": 150, "is_bnd": 50, "is_free": 50, "bnd": 50, "brk": 50 }
                    };
                let source_type = ancestorArray[l.source["id"]];
                let target_type = ancestorArray[l.target["id"]];
                return (edge_length[source_type][target_type] * width / 2000);
            };
            simulation.force("link", d3.forceLink().id(function (d) { return d.id; }));
            simulation.force("link").distance(distanceOfLink);
            //simulation.force("link").iterations(2);

            // var chargeAgent = d3.forceManyBody();
            // //chargeAgent.theta(0.2);
            // chargeAgent.strength(-500);
            // chargeAgent.distanceMax(radius * 10);
            // // chargeAgent.distanceMin(0);
            // var initAgent = chargeAgent.initialize;

            // chargeAgent.initialize = (function () {
            // 	return function (nodes) {
            // 		var agent_nodes = nodes.filter(function (n, _i) {
            // 			return (
            // 				ancestorArray[n.id] == "agent")
            // 		});
            // 		initAgent(agent_nodes);
            // 	};
            // })();

            // // simulation.force("chargeAgent", chargeAgent);

            // var chargeBnd = d3.forceManyBody();
            // chargeBnd.strength(-1000);
            // chargeBnd.distanceMax(radius * 10);
            // var initbnd = chargeBnd.initialize;
            // chargeBnd.initialize = function (nodes) {
            // 	var bnd_nodes = nodes.filter(function (n, i) {
            // 		return (
            // 			ancestorArray[n.id] === "agent" 
            // 			// ancestorArray[n.id] === "mod"
            // 		)
            // 	});
            // 	initbnd(bnd_nodes);
            // };

            // simulation.force("chargeBnd",chargeBnd);


            // var chargeBrk = d3.forceManyBody();
            // chargeBrk.strength(-10000);
            // chargeBrk.distanceMax(radius * 10);
            // var initbrk = chargeBrk.initialize;
            // chargeBrk.initialize = function (nodes) {
            // 	var brk_nodes = nodes.filter(function (n, i) {
            // 		return (
            // 			ancestorArray[n.id] === "brk" ||
            // 			ancestorArray[n.id] === "mod"
            // 		)
            // 	});
            // 	initbrk(brk_nodes);
            // };

            // simulation.force("chargeBrk",chargeBrk);



            // simulation.on("tick", move);
            // simulation.on("end", function () {
            // 	simulation.force("chargeAgent", null);
            // 	simulation.force("chargeBrk", null);
            // 	simulation.force("chargeBnd", null);
            // }
            // );

            simulation.stop();

            var node_to_symbol = function (n) {
                var ancestor = ancestorArray[n.id];
                if (
                    ancestor == "agent" ||
                    ancestor == "residue" ||
                    ancestor == "region" ||
                    ancestor == "locus"
                ) {
                    return d3.symbolCircle;
                }
                // Draw a star for states.
                else if (ancestor == "state") {
                    return {
                        draw: function (context, size) {
                            let n_arms = 18,
                                long_arm_mult = 1.2,
                                // delta is the angle that spans
                                // one arm of the star.
                                delta = (Math.PI * 2 / n_arms),
                                r_short = Math.sqrt(size/Math.PI),
                                r_long = r_short * long_arm_mult;
                            context.moveTo(0, r_long);
                            for (let arm = 1 ; arm <= n_arms ; ++arm) {
                                let theta1 = arm * delta - delta / 2,
                                    x_short = Math.sin(theta1) * r_short,
                                    y_short = Math.cos(theta1) * r_short;
                                context.lineTo(x_short, y_short);
                                // Let the last arm get closed 
                                // by context.closePath()
                                if (arm != n_arms) {
                                    let theta2 = arm * delta,
                                        x_long = Math.sin(theta2) * r_long,
                                        y_long = Math.cos(theta2) * r_long;
                                    context.lineTo(x_long, y_long);
                                }
                            }
                            context.closePath();
                        }
                    };
                }

                else if (
                    ancestor == "mod" ||
                    ancestor == "syn" ||
                    ancestor == "deg" ||
                    ancestor == "bnd" ||
                    ancestor == "brk") {
                    return d3.symbolSquare;
                }
                else if (
                    ancestor == "is_bnd" ||
                    ancestor == "is_equal" ||
                    ancestor == "is_free") {
                    //return d3.symbolDiamond;
		    // Draw a square diamond for tests.
                    return {
                        draw: function (context, size) {
                            let side = Math.sqrt(size),
				// Good old Pythagoras.
				diagonal =  Math.sqrt(2*side*side),
                                p = diagonal/2
                            context.moveTo( 0,  p);
                            context.lineTo( p,  0);
			    context.lineTo( 0, -p);
                            context.lineTo(-p,  0);
			    context.closePath();
                        }
                    };
                }
                else {
                    return d3.symbolCircle;
                }
            };
            var node_to_size = function (n) {
                var ancestor = ancestorArray[n.id];
                if (ancestor == "mod" ||
                    ancestor == "syn" ||
                    ancestor == "deg" ||
                    ancestor == "brk" ||
                    ancestor == "bnd"
                ) { return 2000; }
                else if (
                    ancestor == "is_bnd" ||
                    ancestor == "is_equal" ||
                    ancestor == "is_free"
                ) { return 2000; }
                else if (
                    ancestor == "region"
                ) { return 4000; }
                else if (
                    ancestor == "residue"
                ) { return 2500; }
                else if (
                    ancestor == "state"
                ) { return 2200; }
                else if (
                    ancestor == "locus"
                ) { return 2000; }
                else if (
                    ancestor == "agent"
                ) { return 6000; }
                else {
                    return 4000;
                }
            };
            var node_to_color = function (n) {
                let ancestor = ancestorArray[n.id];
                return ({
                    "mod": "#3399ff", // "#77855C",
                    "is_equal": "#77855C",
                    "syn": "#55A485",
                    "deg": "#8C501E", // "#A47066",
                    "brk": "#E63234", // "#B83319",
                    "bnd": "#82A532", // "#648226",
                    "is_bnd": "#82A532", //"#648226",
                    "is_free": "#E63234", // "#B83319",
                    "state": "#FFD33D", // "#77855C",
                    "region": "#C68482", // "#AB8472",
                    "agent": "#AB7372",
                    "locus": "#828282", // "#718CC4",
                    "residue": "#CE9896" // "#94716A"
                }[ancestor]);

            };

            var link_to_dotStyle = function (l) {
                var ancestorSource = ancestorArray[l.source.id];
                var ancestorTarget = ancestorArray[l.target.id];
                var components = ["residue", "region", "agent"];
		var components2 = ["locus", "state"];
		var components3 = ["bnd", "brk", "is_bnd", "is_free"];
                if (components.indexOf(ancestorSource) > -1 &&
                    components.indexOf(ancestorTarget) > -1) {
                        return ("Gray");
                    // return ("1,0");
                } else if (ancestorSource == "locus" &&
		    components3.indexOf(ancestorTarget) > -1) {
                        return ("Gray");
                } else if (components2.indexOf(ancestorSource) > -1 &&
                    components.indexOf(ancestorTarget) > -1) {
                        return ("notDotted")
                } else {
                    return ("Dotted");
                    //return ("3, 6")
                }
            };
            var shapeClassifier =
                {
                    "shape": node_to_symbol,
                    "size": node_to_size,
                    "dotStyle": link_to_dotStyle,
                    "nodeColor": node_to_color
                };
            loadType(path, graph, config, function (rep) { loadGraph(rep, shapeClassifier, config); });
        }
        /* init the svg object
         * add arrows on edges
         * add svg context menu
         * add tooltip
         * add zoom and drag behavior
         */
        function initSvg() {
            //add drag/zoom behavior
            zoom = d3.zoom().scaleExtent([0.02, 3]).on("zoom", zoomed);
            zoom.filter(function () { return !event.button && !event.shiftKey; });
            svg.classed("svg-content-responsive", true);
            svg.append("svg:defs").selectAll("marker")
                .data(["arrow_end"])      // Different link/path types can be defined here
                .enter().append("svg:marker")    // This section adds the arrows
                .attr("id", function (d) { return d; })
                .attr("refX", 0)
                .attr("refY", 3)
                .attr("markerWidth", 10)
                .attr("markerHeight", 10)
                .attr("orient", "auto")
                .attr("markerUnits", "strokeWidth")
                // .attr("position","90%")
                .append("svg:path")
                .attr("d", "M0,0 L0,6 L9,3 z");
            svg.on("contextmenu", d3ContextMenu(function () { return svgMenu(); }));//add context menu
            svg.call(zoom);
            svg.call(d3.drag().on("drag", selectionHandler).on("end", selectionHandlerEnd).on("start", selectionHandlerStart));
            svg.on("click", svgClickHandler);
            // d3.select("body").on("keydown", svgKeydownHandler);

            d3.select("#tab_frame").append("div")//add the description tooltip
                .attr("id", "n_tooltip")
                .classed("n_tooltip", true)
                .style("visibility", "hidden");
            svg_content.append("svg:image")
                .attr("width", 900)
                .attr("height", 400)
                .attr("x", function () { return width / 2 - 450; })
                .attr("y", function () { return height / 2 - 200; })
                .attr("xlink:href", "ressources/toucan.png");
        };
        // this.initSvg = initSvg;
        /* this fonction  is triggered by tick events
         * move all the svg object (node and links)
         * movement can be due to force simulation or user dragging
         */


        function move(shapeClassifier) {
            return function () {
                var nodes = svg_content.selectAll("g.node");
                nodes.attr("transform", function (d) {
                    return "translate(" + d.x + "," + d.y + ")";
                });
                svg_content.selectAll(".link")
                    .attr("d", function (d) {
                        var x1 = d.source.x,
                            y1 = d.source.y,
                            x2 = d.target.x,
                            y2 = d.target.y,
                            dx = x2 - x1,
                            dy = y2 - y1,
                            dr = Math.sqrt(dx * dx + dy * dy),
                            drx = dr,
                            dry = dr,
                            xRotation = 0,
                            largeArc = 0,
                            sweep = 1;

                        // Self edge.
                        if (x1 === x2 && y1 === y2) {
                            xRotation = -45;
                            largeArc = 1;
                            drx = 30;
                            dry = 20;
                            x2 = x2 + 1;
                            y2 = y2 + 1;
                            return "M" + x1 + "," + y1 + "A" + drx + "," + dry + " " + xRotation + "," + largeArc + "," + sweep + " " + x2 + "," + y2;
                        }
                        else {
                            //transf = d3.zoomTransform(svg.node());
                            let nodeRadius = Math.sqrt(shapeClassifier["size"](d.target)) / 1.77245385091;
                            let arrowLength = 10;
                            let arrowWidth = 5;
                            let [arrowX, arrowY] = [x2 - dx * (nodeRadius + arrowLength) / dr, y2 - dy * (nodeRadius + arrowLength) / dr];
                            let [orthoX, orthoY] = [-dy / dr * arrowWidth, dx / dr * arrowWidth];
                            let [arrowLeftX, arrowLeftY] = [arrowX + orthoX, arrowY + orthoY];
                            let [arrowRightX, arrowRightY] = [arrowX - orthoX, arrowY - orthoY];
                            let [endx, endy] = [x2 - dx * nodeRadius / dr, y2 - dy * nodeRadius / dr];

                            if (shapeClassifier["dotStyle"](d) === "Dotted") {
                                let dotArrayLength = ~~(dr / 12);
                                let dottedpoints = Array(~~(dotArrayLength / 2)).fill()
                                    .map((_, i) => [x1 + 2 * i * dx / dotArrayLength,
                                    y1 + 2 * i * dy / dotArrayLength,
                                    x1 + (2 * i + 1) * dx / dotArrayLength,
                                    y1 + (2 * i + 1) * dy / dotArrayLength]);
                                let str = dottedpoints.map(([xd1, yd1, xd2, yd2]) => `L ${xd1} ${yd1} M ${xd2} ${yd2}`)
                                    .join(" ");
                                return `M ${x1} ${y1}` + str + `L ${endx} ${endy} L ${arrowLeftX} ${arrowLeftY} L ${arrowRightX} ${arrowRightY} L ${endx} ${endy}`;
                            }
                            else {
                                return `M ${x1} ${y1} L ${endx} ${endy} L ${arrowLeftX} ${arrowLeftY} L ${arrowRightX} ${arrowRightY} L ${endx} ${endy}`;
                            }
                            //return "M" + x1 + "," + y1 + "A" + drx + "," + dry + " " + xRotation + "," + largeArc + "," + sweep + " " + x2 + "," + y2;
                        }
                        //return "M" + x1 + "," + y1 + "C 1 1, 0 0,"+ x2+ "," + y2;
                    })
                    .style("stroke", function (d) {
                        if (shapeClassifier["dotStyle"](d) === "Gray") {
			    return "gray"
			} else {
			    return "black"
			}
		    });
                if (localDispatch) { localDispatch.call("move") };
            };
        }
        /* this fonction  is triggered by zoom events
         * transform the svg container according to zoom
         */
        function zoomed() {
            if (!locked) {
                svg_content.attr("transform", d3.event.transform);
                if (localDispatch) { localDispatch.call("move"); }
            }
        }
        /* update the current view to a new graph
         * this function also load all nodes types
         * @input : graph : the new graph
         * @input : path : the graph path
         * @input : config.noTranslate (bool) : do not resize and center the graph after update
         * @input : config.repDispatch (d3.dispatch) : canal used to signal end of loading to caller
         * @input : config.highlightRel (nodeData -> nodeData -> bool)
         *          which nodes to highlight when hovering over a node
         * @input : config.showAttributes : if true show the node attributes on the graph
         */

        this.update = function update(graph, path, config) {
            simulation.stop();
            g_id = path;
            if (path != "/") {
                svg_content.selectAll("*").remove();
                if (path.search("/kami_base/kami/") == 0) {
                    initForceKami(path, graph, config);
                }
                else {
                    initForce(path, graph, config);
                }
            }
            else {
                svg_content.append("svg:image")
                    .attr("width", 900)
                    .attr("height", 400)
                    .attr("x", function () { return width / 2 - 450 })
                    .attr("y", function () { return height / 2 - 200 })
                    .attr("xlink:href", "ressources/toucan.png");
            }
        };

        /* precondition : /kami_base/kami/ is the start of the path */
        function kamiAncestor(path, doSomething) {
            var path2 = path.split("/");
            path2 = path2.slice(3);
            var degree = path2.length;
            var callback = function (err, rep) {
                if (err) {
                    alert(err.currentTarget.response);
                    return false;
                }
                //var rep = JSON.parse(resp.response);
                var mapping = rep.reduce(function (obj, x) {
                    obj[x["left"]] = x["right"];
                    return obj;
                }, {});
                doSomething(mapping);
            }
            request.getAncestors(path, degree, callback);

        };

        /* load all type of a graph, this is needed for node coloration 
         * @input : graph : the new graph
         * @input : path : the graph path
         * @input : callback : the next function to call : loadGraph
         */
        function loadType(path, graph, config, callback) {
            if (path != "/") {
                path = path.split("/");
                if (path.length <= 2) {
                    type_list = [];
                    if (!readOnly && !config.noTranslate) { newNodeSelect.update(type_list) };
                    return callback(graph);
                }
                path.pop();
                path = path.join("/");
                request.getGraph(path, function (e, r) {
                    if (e) console.error(e);
                    else {
                        type_list = r.nodes.map(function (e) {
                            return e.id;
                        });
                        if (!readOnly && !config.noTranslate) { newNodeSelect.update(type_list); }
                        //disp.call("configUpdate",this,type_list);
                        callback(graph);
                    }
                });
            } else callback(graph);
        };
        /* find a specific node in a graph
         * @input : n : the node id
         * @input : graph : the graph object 
         * @return : the node DOM object
         */
        function findNode(n, graph) {
            var ret = graph.filter(function (e) {
                return e.id == n;
            });
            return ret[0];
        }
        /* load a new graph in the svg
         * nodes and edges have context menu
         * nodes can be dragged
         * nodes can be selected with shift + click
         * nodes can be unlocked with ctrl+click
         * nodes can be renamed by double clicking it
         * @input : response : a json structure of the graph
         */
        function loadGraph(response, shapeClassifier, config) {
            //define default shapes functions if not defined
            if (!shapeClassifier) { var shapeClassifier = {} };
            if (!shapeClassifier.shape) { shapeClassifier.shape = function (_) { return d3.symbolCircle } };
            if (!shapeClassifier.size) { shapeClassifier.size = function (_) { return 3000 } };
            if (!shapeClassifier.dotStyle) { shapeClassifier.dotStyle = function (_) { return "notDotted" } };
            if (!shapeClassifier.nodeColor) {
                shapeClassifier.nodeColor = function (d) {
                    if (d.type && d.type != "") return "#" + setColor(type_list.indexOf(d.type), type_list.length);
                    else return "#EEEEEE";
                }
            };



            //transform links for search optimisation
            var links = response.edges.map(function (d) {
                return { source: findNode(d.from, response.nodes), target: findNode(d.to, response.nodes) }
            });
            edgesList = links;




            //add all links as line in the svg
            var link = svg_content.selectAll(".link")
                .data(links, function (d) { return d.source.id + "-" + d.target.id; });
            link.enter()//.insert("line","g")
                .append("path")
                .classed("link", true)
                //.attr("marker-mid", "url(#arrow_end)")
                .on("contextmenu", d3ContextMenu(edgeCtMenu));
            link.exit().remove();
            // svg_content.selectAll(".link")
            // 	.attr("stroke-dasharray", shapeClassifier.dotStyle)

            try {
                simulation.force("link").links(links);
            }
            catch (err) { return 0; }


            //add all node as circle in the svg
            var node = svg_content.selectAll("g.node")
                .data(response.nodes, function (d) { return d.id; });

            var node_g = node.enter().insert("g")
                .classed("node", true)
                .call(d3.drag().on("drag", dragged)
                    .on("end", dragNodeEndHighlightRel(config))
                    .on("start", dragNodeStart)
                    // .filter(function () { return (d3.event.button == 0) || !readOnly }))//disable right click drag if readOnly
                    .filter(function () { return true }))//disable right click drag if readOnly
                .on("mouseover", mouseOver)
                .on("mouseout", mouseOut)
                //.on("mouseup",function(){d3.selectAll("g").dispatch("endOfLink")})
                .on("click", clickHandler)
                //.on("contextmenu",d3ContextMenu(function(){return nodeCtMenu()}));
                .on("contextmenu", nodeContextMenuHandler);

            svg_content.selectAll("g.node").each(function (d) { if (d.type) d3.select(this).classed(d.type, true) });
            if (config.repDispatch) { config.repDispatch.call("loadingEnded") }

            //add selection rectangle
            svg_content.append("rect")
                .attr("id", "selectionRect")
                .style("visibility", "hidden")
                .data([{ startx: 0, starty: 0 }]);

            //add line for edges creation and deletion
            svg_content.append("line")
                .attr("id", "LinkLine")
                .classed("linkLine", true)
                .style("visibility", "hidden");


            //define position function
            var get_position_function = function (response_graph) {
                if (response_graph.hasOwnProperty("attributes") && response_graph["attributes"].hasOwnProperty("positions")) {
                    var positions = response_graph["attributes"]["positions"];
                    return (function (d) {
                        if (positions.hasOwnProperty(d.id)) {
                            return [positions[d.id]["x"], positions[d.id]["y"]]
                        }
                        else { return null }
                    })
                }
                else {
                    return (function (d) { return null })
                }
            };

            var positionOf = get_position_function(response);

            //set nodes position if known
            var unknownNum = 0;
            node_g.each(function (d) {
                pos = positionOf(d);
                if (pos != null) {
                    d.x = pos[0];
                    d.y = pos[1];
                    d.fx = pos[0];
                    d.fy = pos[1];
                }
                else { unknownNum++ }
            });
            //add symbol
            node_g.append("path")
                .classed("nodeSymbol", true)
                .attr("d", d3.symbol()
                    .type(shapeClassifier.shape)
                    .size(shapeClassifier.size))
                .style("fill", shapeClassifier.nodeColor)
            // .style("fill", function (d) {
            // 	if (d.type && d.type != "") return "#" + setColor(type_list.indexOf(d.type), type_list.length);
            // 	else return "#EEEEEE";
            // });

            //  node_g.style("WebkitFilter","grayscale(100%)");
            //  node_g.style("-webkit-filter","grayscale(100%)");
            //  node_g.style("filter","grayscale(100%)");

            //add all node id as label
            node_g.insert("text")
                .classed("nodeLabel", true)
                .attr("x", 0)
                .attr("dy", ".3em")
                .attr("text-anchor", "middle")
                .text(function (d) {
                    let name = d.id.split(" ")[0]
                    return name.length > 7 ? name.substring(0, 5).concat("..") : name;
                })
                //.text(function(d){return d.id})
                .attr("font-size", function () { return (radius / 2) + "px" })
                // .style("fill", function (d) {
                // 	if (d.type && d.type != "") return "#" + setColor(type_list.indexOf(d.type), type_list.length, true);
                // 	else return "black";
                // })
                // .style("stroke", function (d) {
                // 	if (d.type && d.type != "") return "#" + setColor(type_list.indexOf(d.type), type_list.length, true);
                // 	else return "black";
                // })
                .on("dblclick", clickText);

            node_g.filter(d => d.attrs && "val" in d.attrs)
                .insert("text")
                .classed("nodeLabel", true)
                .attr("x", 0)
                .attr("dy", "1.3em")
                .attr("text-anchor", "middle")
                .text(d => {
                    const setString = setToString(d.attrs["val"]);
                    if (setString.length > 7) {
                        return setString.substring(0, 5).concat("..");
                    }
                    else {
                        return setString;
                    }
                })
                //.text(function(d){return d.id})
                .attr("font-size", function () { return (radius / 2) + "px" })
            // .style("fill", function (d) {
            // 	if (d.type && d.type != "") return "#" + setColor(type_list.indexOf(d.type), type_list.length, true);
            // 	else return "black";
            // })
            // .style("stroke", function (d) {
            // 	if (d.type && d.type != "") return "#" + setColor(type_list.indexOf(d.type), type_list.length, true);
            // 	else return "black";
            // })

            node.exit().remove();


            //start the simulation
            //simulation.nodes([]);
            simulation.nodes(response.nodes);

            simulation.alpha(0.01 * unknownNum);
            simulation.alphaDecay(0.1);
            simulation.on("end", function () {
                simulation.on("tick", move(shapeClassifier));
                if (!config.noTranslate) {
                    var rep = getBounds();
                    simulation.alphaDecay(0.02);
                    if (rep) {
						var margin = 80;
                        var xratio = svg.attr("width") / (rep[0][1] - rep[0][0] + 2*margin);
                        var yratio = svg.attr("height") / (rep[1][1] - rep[1][0] + 2*margin);
                        var xorigine = rep[0][0] - margin
                        var yorigine = rep[1][0] - margin
                        var ratio = Math.min(xratio, yratio);
                        //rate = Math.max(rate, 0.02);
                        //rate = Math.min(1.1, rate);
                        //rate = rate * 0.9;
                        var centerX = (svg.attr("width") - (rep[0][1] - rep[0][0] + 2*margin) * ratio) / 2;
                        var centerY = (svg.attr("height") - (rep[1][1] - rep[1][0] + 2*margin) * ratio) / 2;
                        svg.call(zoom.transform, transform.translate(-xorigine * ratio + centerX, -yorigine * ratio + centerY).scale(ratio));
                        svg_content.selectAll("g.node")
                            .attr("vx", 0)
                            .attr("vy", 0);

                    }
                    else {
                        svg.call(zoom.scaleTo, 1);
                    }
                }
                move(shapeClassifier)();
                simulation.on("end", function () {
                    svg_content.selectAll("g.node")
                        .attr("vx", 0)
                        .attr("vy", 0);
                });
            });
            simulation.restart();
            // console.log("sim",simulation.force("link"));
            // console.log("sim",simulation.force("center"));
            // console.log("sim",simulation.force("charge"));
            // console.log("sim",simulation.force("chargeAgent"));
            // console.log("sim",simulation.force("chargeBnd"));
            // console.log("sim",simulation.force("chargeBrk"));
        };

        function getBounds() {
            var minx, maxx, miny, maxy;
            svg_content.selectAll("g.node")
                .each(function (d, i) {
                    if (i == 0) {
                        minx = d.x;
                        maxx = d.x;
                        miny = d.y;
                        maxy = d.y;
                        return 0;
                    }
                    if (d.x < minx) { minx = d.x };
                    if (d.x > maxx) { maxx = d.x };
                    if (d.y < miny) { miny = d.y };
                    if (d.y > maxy) { maxy = d.y };
                });
            if (minx) { return [[minx, maxx], [miny, maxy]] }
            else { return undefined };
        };
        /* define a color set according to the size of an array
         * and the element position in the array
         * @input : nb : the element index
         * @input : tot : the size of the array
         * @input : neg : return the color as negative
         * @return : a color in hex format
         */
        function setColor(nb, tot, neg) {
            if (neg) {
                // //calculate color luminosity
                // var tmp = ((0x777777/tot)*(nb+1)).toString(16).split(".")[0];
                // var ret =(parseInt(tmp[0]+tmp[1],16)*299+parseInt(tmp[2]+tmp[3],16)*587+parseInt(tmp[4]+tmp[5],16)*114)/1000;
                // //if brigth : return black, else return white
                // // if(ret <150) return (0xDDDDDD).toString(16);
                // // else return (0x000000).toString(16);

                //return (0x0b0b0b).toString(16);
                // return (0x282828).toString(16);
                return (0x252525).toString(16);


            }
            var red = 136 + (33 / tot) * (nb + 1);
            var blue = (150000 - red * 886) / 114;
            var reds = red.toString(16).split(".")[0];
            while (reds.length < 2) { reds = "0" + reds; };
            var blues = blue.toString(16).split(".")[0];
            while (blues.length < 2) { blues = "0" + blues; };
            return (reds + reds + blues);

            // var ret = ((0x777777/tot)*(nb+1)).toString(16).split(".")[0]
            //while(ret.length<6){ret="0"+ret;};
            // return ret;
        }
        /* define the svg context menu
         * svg context menu allow to unlock all nodes,
         * select all nodes,
         * unselect all nodes,
         * add a new node of a correct type,
         * remove all selected nodes
         * @return : the svg context menu object
         * @call : graphUpdate
         */
        function svgMenu() {
            var menu = [{
                title: "Unlock all",
                action: function (elm, d, i) {
                    svg_content.selectAll("g").each(function (d) { d.fx = null; d.fy = null });
                    if (simulation.nodes().length > 0)
                        simulation.alpha(1).restart();
                    request.rmAttr(g_id, JSON.stringify(["positions"]), function () { });
                }
            }, {
                title: "Lock all",
                action: function (elm, d, i) {

                    var req = {};
                    svg_content.selectAll("g").each(function (d) {
                        d.fx = d.x;
                        d.fy = d.y;
                        req[d.id] = { "x": d.x, "y": d.y }
                    });
                    request.addAttr(g_id, JSON.stringify({ positions: req }), function () { });
                }
            }, {
                title: "Select all",
                action: function (elm, d, i) {
                    svg_content.selectAll("g").classed("selected", true);
                    svg_content.selectAll("g").select(".nodeSymbol").classed("selectedSymbol", true);
                    maybeDrawButtons();
                }
            }, {
                title: "Unselect all",
                action: function (elm, d, i) {
                    svg_content.selectAll("g").classed("selected", false);
                    svg_content.selectAll("g").select(".nodeSymbol").classed("selectedSymbol", false);
                    hideButtons();
                }
            }, {
                title: "Anatomizer",
                action: anatomizerHandler
            }];
            if (!readOnly) {
                menu.push({
                    title: "Add node",
                    action: function (elm, d, i) {
                        var mousepos = d3.mouse(elm);
                        var svgmousepos = d3.mouse(svg_content.node());
                        locked = true;
                        inputMenu("New Name", [""], type_list.concat(["notype"]), null, true, true, 'center',
                            function (cb) {
                                locked = false;
                                if (cb.line) {
                                    request.addNode(g_id, cb.line, cb.radio, function (e, r) {
                                        if (e) console.error(e);
                                        else {
                                            console.log("node added")
                                            let req = {};
                                            req[cb.line] = { "x": svgmousepos[0], "y": svgmousepos[1] }
                                            request.addAttr(g_id, JSON.stringify({ positions: req }),
                                                function () { disp.call("graphUpdate", this, g_id, true); });

                                        }
                                    });
                                }
                            },
                            { x: mousepos[0], y: mousepos[1], r: radius / 2 },
                            svg)
                    }
                });
            };
            var selected = svg_content.selectAll("g.selected")
            if (!readOnly && selected.size()) {
                menu.push({
                    title: "Remove Selected nodes",
                    action: deleteSelectedNodes
                });

                menu.push({
                    title: "Copy",
                    action: function (_elm, _d, _i) {
                        let node_ids = selected.data().map(d => d.id);
                        copyNodes(node_ids);
                    }
                });
            }
            if (nodeClipboard["path"] !== null && nodeClipboard["nodes"] !== []) {
                // if (g_id === nodeClipboard["path"] ||
                //     nodeClipboard["path"] == g_id.substring(0, g_id.lastIndexOf("/"))) {
                menu.push({
                    title: "Paste",
                    action: pasteNode
                });

                // }
            }

            return menu;
        };
        /* define the node context menu
         * node context menu allow to remove it,
         * clone it,
         * link it to all selected nodes,
         * merge with a selected node : TODO -> change server properties,
         * @return : the node context menu object
         * @call : graphUpdate
         */

        function nodeCtMenu(nodeType, from_config) {
            var menu = [{
                title: "Remove",
                action: function (elm, d, i) {
                    if (confirm("Are you sure you want to delete this Node ?")) {
                        request.rmNode(g_id, d.id, true, function (e, r) {
                            if (e) console.error(e);
                            else {
                                disp.call("graphUpdate", this, g_id, true);
                                console.log(r);
                            }
                        });
                    }
                }
            }, {
                title: "Clone",
                action: function (elm, d, i) {

                    //let svgmousepos = d3.mouse(svg_content.node());
                    console.log(elm, d, i);
                    locked = true;
                    inputMenu("New Name", [d.id + "copy"], null, null, true, true, 'center', function (cb) {
                        if (cb.line) {
                            request.cloneNode(g_id, d.id, cb.line, function (e, r) {
                                if (e) console.error(e);
                                else {
                                    let req = {};
                                    //req[cb.line] = { "x": svgmousepos[0] + 10, "y": svgmousepos[1] }
                                    req[cb.line] = { "x": d.x + 70, "y": d.y + 70 }
                                    request.addAttr(g_id, JSON.stringify({ positions: req }),
                                        function () { disp.call("graphUpdate", this, g_id, true); });
                                }
                            });
                        }
                        locked = false;
                    }, d, svg_content)
                }
            },

            // {title: "children",
            //  action: getChildren},

            {
                title: "Add value",
                action: addVal
            },

            {
                title: "Remove Value",
                action: rmVal
            },
            {
                title: "Types",
                action: nodeTypesEditor
            },

            ];

            var selected = svg_content.selectAll("g.selected")
            if (selected.size()) {
                menu.push({
                    title: "Link to",
                    action: function (elm, d, i) {
                        hideButtons();
                        var cpt = 0, err_cpt = 0;
                        selected.each(function (el) {
                            request.addEdge(g_id, d.id, el.id, function (e, r) {
                                if (!e) { console.log(r); cpt++; }
                                else { console.error(e); err_cpt++; }
                                if (cpt == selected.size() - err_cpt) disp.call("graphUpdate", this, g_id, true);
                            });
                        });

                    }
                });
                if (selected.size() == 1) {
                    menu.push({
                        title: "Merge with selected nodes",
                        action: function (elm, d, i) {
                            locked = true;
                            //var svgmousepos = d3.mouse(svg_content.node());
                            inputMenu("New Name", [d.id + selected.datum().id], null, null, true, true, 'center', function (cb) {
                                if (cb.line) {
                                    hideButtons();
                                    request.mergeNode(g_id, d.id, selected.datum().id, cb.line, true, function (e, r) {
                                        if (!e) {
                                            let req = {};
                                            //req[r] = { "x": svgmousepos[0] + 10, "y": svgmousepos[1] }
                                            req[r] = { "x": ( d.x + selected.datum().x )/2, "y": ( d.y + selected.datum().y )/2 }
                                            request.addAttr(g_id, JSON.stringify({ positions: req }),
                                                function () { disp.call("graphUpdate", this, g_id, true); });
                                            console.log(r);
                                        }
                                        else console.error(e);
                                    });
                                } locked = false;
                            }, d, svg_content);
                        }
                    })
                }
            }
            if (from_config !== undefined && nodeType === "locus") {
                return menu.concat(from_config);
            }
            else {
                return menu;

            }
        };
        /* define the edge context menu
         * edge context menu allow to remove it,
         * select source and target node,
         * @call : graphUpdate
         */
        var edgeCtMenu = [{
            title: "Select Source-target",
            action: function (elm, d, _i) {
                svg_content.selectAll("g")
                    .filter(function (e) { return e.id == d.source.id || e.id == d.target.id })
                    .classed("selected", true);
                drawButtons();
            }
        }, {
            title: "Remove",
            action: function (elm, d, _i) {
                locked = true;
                if (confirm('Are you sure you want to delete this Edge ? The linked element wont be removed')) {
                    request.rmEdge(g_id, d.source.id, d.target.id, false, function (e, r) {
                        if (e) console.error(e);
                        else {
                            disp.call("graphUpdate", this, g_id, true);
                            console.log(r);
                        }
                        locked = false;
                    });
                } else locked = false;
            }
        }];
        /* handling mouse over nodes
         * show all the node information in the bottom left tooltip
         * @input : d : the node datas
         */
        function numSetToString(set) {
            for (const setType of Object.keys(set)) {
                if (setType === "pos_list") {
                    return set[setType].join(",");
                }
                if (setType === "neg_list") {
                    if (set[setType].length !== 0) {
                        return "D* \\ {" + set[setType].join(",") + "}";
                    }
                    else {
                        return "D*"
                    }
                }
                if (setType === "string") {
                    return set[setType];
                }
                return ""
            }
        }

        function strSetToString(set) {
            for (const setType of Object.keys(set)) {
                if (setType === "pos_list") {
                    return set[setType].join(",");
                }
                if (setType === "neg_list") {
                    if (set[setType].length !== 0) {
                        return "S* \\ {" + set[setType].join(",") + "}";
                    }
                    else {
                        return "S*"
                    }
                }
                return ""
            }
        }

        function setToString(set) {
            const strset = strSetToString(set["strSet"]);
            const numset = numSetToString(set["numSet"])
            if (strset === "") { return numset }
            if (numset === "") { return strset }
            const str = numset + " + " + strset;
            return str === "D* + S*" ? "*" : str;
        }

        function mouseOver(d) {
            var div_ct = "<p><h3><b><center>" + d.id + "</center></b>";
            div_ct += "<h5><b><center>class: " + d.type + "</center></b></h5>";
            if (d.attrs) {
                div_ct += "<ul>";
                for (let el of Object.keys(d.attrs)) {
                    let setString = setToString(d.attrs[el])
                    if (setString) {
                        div_ct += "<li><b><center>" + el + ":" + setString + "</center></b></li>";
                    }
                }
                div_ct += "</ul>";
            }
            div_ct += "</p>";
            d3.select("#n_tooltip")
                .style("visibility", "visible")
                // .style("background-color", "#fffeec")
                // .style("position", "absolute")
                // .style("bottom", "20px")
                // .style("left", "10px")
                // .style("border", "4px solid #0f71ba")
                // .style("border-radius", "10px")
                // .style("box-shadow", " 3px 3px 3px #888888")
                // .style("z-index", " 100")
                // .style("display", " block")
                // .style("text-align", " left")
                // .style("vertical-align", " top")
                // .style("width", " 150px")
                // .style("overflow ", " hidden")
                .html(div_ct);
        };
        /* handling mouse out of nodes
         * hide the bottom left tooltip
         * @input : d : the node datas (not needed yet)
         */
        function mouseOut(d) {
            d3.select("#n_tooltip")
                .style("visibility", "hidden")
                .text("");
        };
        /* handling click on a node
         * on shift : select/uselect the node
         * on ctrl : unlock the node and restart simulation
         * @input : d : the node datas
         */
        function clickHandler(d) {
            d3.event.stopPropagation();
            if (d3.event.ctrlKey) {
                d.fx = null;
                d.fy = null;
                if (simulation.nodes().length > 0)
                    simulation.alpha(1).restart();
                request.rmAttr(g_id, JSON.stringify(["positions", d.id]), function () { });
            }
            if (d3.event.shiftKey) {
                if (d3.select(this).classed("selected")) {
                    d3.select(this).classed("selected", false);
                    d3.select(this).select(".nodeSymbol").classed("selectedSymbol", false);
                    maybeDrawButtons();
                }
                else {
                    d3.select(this).classed("selected", true);
                    d3.select(this).select(".nodeSymbol").classed("selectedSymbol", true);
                    drawButtons();
                }
            }
        };
        /* handling double-click on a node text
         * open an input menu
         * change the node id 
         * @input : d : the node datas
         * @call : graphUpdate
         */
        function clickText(d) {
            let svgmousepos = d3.mouse(svg_content.node());
            var el = d3.select(this);
            var lab = [d.id];
            locked = true;
            inputMenu("name", lab, null, null, true, true, 'center', function (cb) {
                if (cb.line && cb.line != d.id) {
                    request.renameNode(g_id, d.id, cb.line, function (err, ret) {
                        let req = {};
                        req[cb.line] = { "x": svgmousepos[0] + 10, "y": svgmousepos[1] }
                        locked = false;
                        request.addAttr(g_id, JSON.stringify({ positions: req }),
                            function () {
                                disp.call("graphUpdate", this, g_id, true);
                            });
                    });
                }
                else { locked = false; }
            }, d, svg_content);

            // request.cloneNode(g_id, d.id, cb.line, function (err, ret) {
            // 	if (!err) {
            // 		request.rmNode(g_id, d.id, false, function (e, r) {
            // 			if (e) console.error(e);
            // 			else {
            // 				let req = {};
            // 				req[cb.line] = { "x": svgmousepos[0]+10, "y": svgmousepos[1] }
            // 				request.addAttr(g_id, JSON.stringify({ positions: req }),
            // 					function () { disp.call("graphUpdate", this, g_id, true); });
            // 			}
            // 		})
            // 	}
            // 	else console.error(err);
            // });

        };
        /* handling dragging event on nodes
         * @input : d : the node datas
         */
        function dragged(d) {
            if (locked) return;
            var xpos = d3.event.x;
            var ypos = d3.event.y;
            if (d3.event.sourceEvent.buttons == 1) {
                if (simulation.alpha() < 0.09 && simulation.nodes().length > 0)
                    simulation.alpha(1).restart();
                // var xpos = d3.event.x;
                // var ypos = d3.event.y;
                var tx = xpos - saveX;
                var ty = ypos - saveY;
                d3.select(this).attr("cx", d.fx = xpos).attr("cy", d.fy = ypos);
                svg_content.selectAll("g.selected")
                    .filter(function (d2) { return d2.id != d.id })
                    .each(function (d2) {
                        d2.x = d2.x + tx;
                        d2.y = d2.y + ty;
                        d2.fx = d2.x;
                        d2.fy = d2.y;
                        d3.select(this)
                            .attr("cx", d2.fx)
                            .attr("cy", d2.fy)
                    });
                saveX = xpos;
                saveY = ypos;
            }
            else if (d3.event.sourceEvent.buttons == 2 && !readOnly) {
                var mousepos = d3.mouse(svg_content.node());
                svg_content.selectAll("#LinkLine")
                    .attr("x2", beginMouseX + (mousepos[0] - beginMouseX) * 0.99)
                    .attr("y2", beginMouseY + (mousepos[1] - beginMouseY) * 0.99);
            }
        }

        /* handling dragend event on nodes
         * @input : d : the node datas
         */
        function dragNodeEndHighlightRel(config) {
            return function (d, _elm, _i) {
                var nodecontext = this;
                var currentEvent = d3.event;
                var xpos = d3.event.x;
                var ypos = d3.event.y;
                console.log(d3.event.sourceEvent.button);
                if (!d3.event.sourceEvent.button) {
                    var id = d["id"];
                    var req = {};
                    req[id] = { "x": xpos, "y": ypos };
                    //request.addAttr(g_id, JSON.stringify({positions:req}),function(){});
                    svg_content.selectAll("g.selected")
                        .each(function (d) {
                            d.fx = d.x;
                            d.fy = d.y;
                            req[d.id] = { "x": d.x, "y": d.y }
                        });
                    if (!readOnly) {
                        request.addAttr(g_id, JSON.stringify({ positions: req }), function () { });
                    }

                    if (Math.abs(xpos - beginX) > 3 || Math.abs(ypos - beginY) > 3) {
                        svg_content.selectAll("g.selected")
                            .classed("selected", false);
                        hideButtons();
                    }
                }
                else if (d3.event.sourceEvent.button != 0) {
                    svg_content.selectAll("#LinkLine")
                        .style("visibility", "hidden")
                    var targetElement = d3.select(d3.event.sourceEvent.path[1]);
                    if (targetElement.classed("node")) {
                        targetElement.each(function (d2) {
                            if (d2.id !== d.id && d3.event.sourceEvent.button == 2 && !readOnly) {
                                if (!d3.event.sourceEvent.shiftKey) {
                                    console.log("edges", edgesList);
                                    if (!existsEdge(d.id, d2.id)) {
                                        request.addEdge(g_id, d.id, d2.id, function (e, r) {
                                            if (!e) {
                                                disp.call("graphUpdate", this, g_id, true)
                                            }
                                            else { console.error(e) }
                                        });
                                    }
                                    else {
                                        request.rmEdge(g_id, d.id, d2.id, true, function (e, r) {
                                            if (!e) {
                                                disp.call("graphUpdate", this, g_id, true)
                                            }
                                            else { console.error(e) }
                                        });
                                    }
                                }
                                else {
                                    if (config.shiftLeftDragEndHandler) {
                                        console.log(g_id);
                                        config.shiftLeftDragEndHandler(g_id, d, d2);
                                    }
                                }
                            }
                            else if (d2.id == d.id && d3.event.sourceEvent.button == 2 && !readOnly) {
                                var handler = d3ContextMenu(function () { return nodeCtMenu(d2.type, config["nodeCtMenu"]) })
                                d3.customEvent(currentEvent.sourceEvent, handler, nodecontext, [d, null]);
                            }
                            else if (d2.id == d.id && d3.event.sourceEvent.button == 1) {
                                if (config.highlightRel) {
                                    if (d3.event.sourceEvent.shiftKey) {
                                        highlightSubNodes(config.highlightRel(d.id));
                                        getChildren(d, true);
                                    }
                                    else {
                                        highlightNodes(config.highlightRel(d.id));
                                        getChildren(d, false);

                                    }
                                }
                            }
                        });
                    }
                }
            };
        }

        function dragNodeStart(d) {
            saveX = d3.event.x;
            saveY = d3.event.y;
            beginX = d3.event.x;
            beginY = d3.event.y;
            if (d3.event.sourceEvent.button == 2 && !readOnly) {
                let mousepos = d3.mouse(svg_content.node());
                beginMouseX = mousepos[0];
                beginMouseY = mousepos[1];
                svg_content.selectAll("#LinkLine")
                    .attr("x1", beginMouseX)
                    .attr("y1", beginMouseY)
                    .attr("x2", beginMouseX)
                    .attr("y2", beginMouseY)
                    .style("visibility", "visible");
                startOfLinkNode = d.id;
            }
        }

        this.dragged = dragged;
        this.dragNodeEnd = dragNodeEndHighlightRel({});
        this.dragNodeStart = dragNodeStart;

        function nodeContextMenuHandler(_d) {
            d3.event.stopPropagation();
            d3.event.preventDefault();
            // d3.select(this)
            // 	.on("mouseup", function () { console.log("mouseout") });

        };

        function addVal(elm, d, _i) {
            var val = prompt("Enter a value", "");
            if (!val) { return 0 }
            var callback = function (err, resp) {
                if (err) {
                    alert(err.currentTarget.response);
                    return false;
                }
                // if (!d.attrs) { d.attrs = {} };
                // if (!d.attrs["val"]) { d.attrs["val"] = [] };
                // const index = d.attrs["val"].indexOf(val);
                // if (index === -1) { d.attrs["val"].push(val) };
                disp.call("graphUpdate", this, g_id, true);
            }
            request.addNodeAtt(g_id, d.id, JSON.stringify({ "val": [val] }), callback);
        };

        function rmVal(elm, d, i) {
            var val = prompt("Enter a value", "");
            if (!val) { return 0 };
            var callback = function (err, resp) {
                if (err) {
                    alert(err.currentTarget.response);
                    return false;
                }
                if (!d.attrs) { return 0 };
                if (!d.attrs["val"]) { return 0 };
                // let index = d.attrs["val"].indexOf(val);
                // if (index != -1) { d.attrs["val"].splice(index, 1) };
                disp.call("graphUpdate", this, g_id, true);
            }
            request.rmNodeAtt(g_id, d.id, JSON.stringify({ "val": [val] }), callback);
        };

        function nodeTypesEditor(_elm, d, _i) {
            disp.call("loadTypeEditor", this, g_id, d.id)
        };

        function getChildren(d, keepOldConds) {
            var callback = function (err, rep) {
                if (err) {
                    alert(err.currentTarget.response);
                    return false;
                }
                const jsonRep = JSON.parse(rep.response);
                const children = jsonRep["children"];
                disp.call("addNugetsToInput", this, children, d.id, keepOldConds);
            }
            request.getChildren(g_id, d.id, callback)
        };

        function selectionHandler() {
            var mousepos = d3.mouse(svg_content.node());
            svg_content.selectAll("#selectionRect")
                .each(function (d) {
                    d3.select(this)
                        .attr("width", Math.abs(mousepos[0] - d.startx))
                        .attr("height", Math.abs(mousepos[1] - d.starty))
                        .attr("x", Math.min(mousepos[0], d.startx))
                        .attr("y", Math.min(mousepos[1], d.starty))
                })

        };
        function selectionHandlerStart() {
            var selectionStart = d3.mouse(svg_content.node());
            svg_content.selectAll("#selectionRect")
                .style("visibility", "visible")
                .each(function (d) {
                    d.startx = selectionStart[0];
                    d.starty = selectionStart[1];
                });
        };
        function selectionHandlerEnd() {
            var mousepos = d3.mouse(svg_content.node());
            svg_content.selectAll("#selectionRect")
                .style("visibility", "hidden")
                .each(function (d) {
                    var minx = Math.min(mousepos[0], d.startx);
                    var maxx = Math.max(mousepos[0], d.startx);
                    var miny = Math.min(mousepos[1], d.starty);
                    var maxy = Math.max(mousepos[1], d.starty);
                    svg_content.selectAll("g")
                        .filter(function (n) {
                            return (
                                n.x <= maxx &&
                                n.x >= minx &&
                                n.y <= maxy &&
                                n.y >= miny);
                        })
                        .classed("selected", true);
                    svg_content.selectAll("g")
                        .filter(function (n) {
                            return (
                                n.x <= maxx &&
                                n.x >= minx &&
                                n.y <= maxy &&
                                n.y >= miny);
                        })
                        .select(".nodeSymbol")
                        .classed("selectedSymbol", true);
                    maybeDrawButtons();
                });
        }

        function svgClickHandler() {
            svg_content.selectAll("g.selected")
                .classed("selected", false);
            svg_content.selectAll(".nodeSymbol")
                .classed("selectedSymbol", false);
            hideButtons();
            dehilightNodes();
        }
        this.svg_result = function () { return (svg.node()); };


        function dehilightNodes() {
            svg.selectAll(".nodeSymbol")
                .classed("highlighted", false);
			svg.selectAll(".node")
                .classed("lowlighted", false);
			svg.selectAll(".link")
				.classed("highlighted", false);
            svg.selectAll(".link")
                .classed("lowlighted", false);

        }

        function highlightNodes(to_highlight) {
            svg.selectAll(".nodeSymbol")
                .classed("highlighted", function (d) { return to_highlight(d.id) });
			svg.selectAll(".node")
			    .classed("lowlighted", function (d) { return !to_highlight(d.id) });

			svg.selectAll(".link")
				.classed("highlighted", function (d) { return to_highlight(d.source.id) && to_highlight(d.target.id) });
            svg.selectAll(".link")
                .classed("lowlighted", function (d) { return !to_highlight(d.source.id) || !to_highlight(d.target.id) });
        }

        //only highlights node among the already highlighted
		//That function is bugged at the moment. Don't use it for now.
        function highlightSubNodes(to_highlight) {
            svg.selectAll(".nodeSymbol")
				.classed("highlighted", function (d) { return (d3.select(this).classed("highlighted")) && to_highlight(d.id) });
			svg.selectAll(".node")
                .classed("lowlighted", function (d) { return (d3.select(this).classed("lowlighted")) && !to_highlight(d.id) });

            svg.selectAll(".link")
                .classed("lowlighted", true);
        }
        function newChild() {
            var selected = svg_content.selectAll("g.selected")
            let node_ids = selected.data().map(d => d.id);
            disp.call("addGraphIGraph", this, g_id, node_ids);

        }
        function newGraph(_elm, _d, _i) {
            var selected = svg_content.selectAll("g.selected")
            let val = prompt("New name:", "");
            if (!val) { return 0 }
            let node_ids = selected.data().map(d => d.id);
            let callback = function (err, _ret) {
                if (err) { console.error(err) }
                else {
                    disp.call("hieUpdate", this);
                }
            };
            request.newGraphFromNodes(g_id, val, node_ids, callback);
        }

        function newChildRule(_elm, _d, _i) {
            var selected = svg_content.selectAll("g.selected")
            let val = prompt("New name:", "");
            if (!val) { return 0 }
            let node_ids = selected.data().map(d => d.id);
            let callback = function (err, _ret) {
                if (err) { console.error(err) }
                else {
                    disp.call("hieUpdate", this);
                }
            };
            request.newChildRuleFromNodes(g_id, val, node_ids, callback);
        }

        function maybeDrawButtons() {
            var selected = svg_content.selectAll("g.selected")
            if (selected.size()) {
                drawButtons();
            }
            else {
                hideButtons();
            }
        }

        function drawButtons() {
            d3.select(buttonsDiv)
                .style("display", "block");
        }

        function hideButtons() {
            d3.select(buttonsDiv)
                .style("display", "none");
        }

        function createButtons() {
            if (!readOnly) {
                let buttons = d3.select(buttonsDiv);
                buttons.attr("id", "GraphButtons")
                    // .append("button")
                    // .text("New child graph")
                    // .on("click", newGraph);
                    .append("button")
                    .text("New child")
                    .on("click", newChild);

                // buttons .append("button")
                // 	.text("New sigbling graph")
                // 	.on("click", function () { alert("sibling graph") });

                // buttons.append("button")
                // 	.text("New child rule")
                // 	.on("click", newChildRule);

                // buttons.append("button")
                // 	.text("New sibling rule")
                // 	.on("click", function () { alert("sibling rule") });

                buttons.selectAll("button")
                    .attr("type", "button")
                    .classed("top_chart_elem", true)
                    .classed("btn", true)
                    .classed("btn-block", true);
                buttons.style("display", "none");
                return buttons.node();
            }
        }

        function deleteSelectedNodes(elm, d, i) {
            var selected = svg_content.selectAll("g.selected");
            if (!readOnly && selected.size()) {
                if (confirm("Delete all selected Nodes ?")) {
                    hideButtons();
                    selected.each(function (el, i) {
                        request.rmNode(g_id, el.id, true, function (e, r) {
                            if (e) console.error(e);
                            else console.log(r);
                            if (i === selected.size() - 1) disp.call("graphUpdate", this, g_id, true);
                        })
                    });
                }
            }
        }

        this.buttons = function () { return buttonsDiv; };

        function copyNodes(nodeIds) {
            nodeClipboard["path"] = g_id;
            nodeClipboard["nodes"] = nodeIds;
        }

        function pasteNode(_elm, _d, _i, svgmousepos) {
            if (svgmousepos === undefined) {
                svgmousepos = d3.mouse(svg_content.node());
            }
            let callback = function (_e, _r) {
                disp.call("graphUpdate", this, g_id, true);
            };
            request.pasteNodes(g_id, nodeClipboard["path"], nodeClipboard["nodes"], svgmousepos, callback);
        }

        function svgKeydownHandler() {
            if (d3.event.target === d3.select("body").node()) {
                console.log("parent");
                if (d3.event.keyCode === 80 || (d3.event.keyCode === 86 && d3.event.ctrlKey)) {
                    if (nodeClipboard["path"] !== null && nodeClipboard["nodes"] !== []) {
                        let transf = d3.zoomTransform(svg.node());
                        pasteNode(null, null, null, [(-transf.x + width / 2) / transf.k, (-transf.y + height / 2) / transf.k]);
                    }

                }
                else if (d3.event.keyCode === 89 || (d3.event.keyCode === 67 && d3.event.ctrlKey)) {
                    var selected = svg_content.selectAll("g.selected")
                    if (selected.size()) {
                        let node_ids = selected.data().map(d => d.id);
                        copyNodes(node_ids);
                    }
                }
                else if (d3.event.keyCode === 46) {
                    deleteSelectedNodes();
                }
                else if (String.fromCharCode(d3.event.keyCode) === "N" && !readOnly) {
                    console.log("beforevisible");
                    d3.select("#" + newNodeId).style("visibility", "visible");
                    d3.select("body").on("keydown", newNodeSelect.input);
                    svg.on("click", newNodeClickHandler);
                }
            }
        }
        this.svgKeydownHandler = svgKeydownHandler;

        function newNodeClickHandler() {
            let currentType = newNodeSelect.currentType();
            if (currentType) {
                let svgmousepos = d3.mouse(svg_content.node());
                let callback = function (e, _r) {
                    if (e) console.error(e);
                    else { disp.call("graphUpdate", this, g_id, true); }
                }
                request.addNodeNewName(g_id, currentType, currentType, svgmousepos, callback);
            }
        }

        this.endNewNode = function () {
            console.log("endNewNode")
            d3.select("body").on("keydown", svgKeydownHandler);
            svg.on("click", svgClickHandler);
        }

        function anatomizerHandler() {
            let uniProtId = prompt("enter UniProt accession or HGNC symbol", "");
            if (!uniProtId) { return false }

            let callback = function (e, _r) {
                if (e) { console.log(e) }
                else {
                    console.log("graphUpdate");
                    disp.call("graphUpdate", this, g_id, true);
                }
            };
            request.anatomizer(g_id, uniProtId, callback);

        }

    };
});
