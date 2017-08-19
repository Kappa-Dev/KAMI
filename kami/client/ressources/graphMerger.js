define([
    "ressources/d3/d3.js",
    "ressources/InterractiveGraph.js",
    "ressources/requestFactory.js"
],
    function (d3, InterractiveGraph, factory) {

        //Interface allowing to define relations between nodes of different graphs

        return function GraphMerger(topSvgId, fatherElem, dispatch, server_url) {
            let relation = [];
            let configMerger = {};
            let parentPath, leftGraphName, rightGraphName;
            
            var localDispatch = d3.dispatch(
                "move"//triggered when a subgraph moved
            );

            var size = d3.select("#graph_frame").node().getBoundingClientRect();
            let main_svg = fatherElem
                .append("svg")
                .attr("id", topSvgId)
                .classed("svg-content-responsive", true)
                .attr("width", size.width)
                .attr("height", size.height);

            

            //let request = new factory(server_url, function (rule) { return rule["L"] })
            let request = new factory(server_url)
            let leftGraph = new InterractiveGraph(topSvgId, "leftGraph", size.width / 2, size.height, dispatch, request, true, localDispatch);
            let rightGraph = new InterractiveGraph(topSvgId, "rightGraph", size.width / 2, size.height, dispatch, request, true, localDispatch);
            let beginMouseX, beginMouseY, startOfLinkNode

            main_svg.append(leftGraph.svg_result)
                .attr("x", 0)
                .attr("y", 0);
            main_svg.append(rightGraph.svg_result)
                .attr("x", size.width / 2)
                .attr("y", 0);

            main_svg.append("line")
                .attr("id", "MergeLinkLine")
                .classed("linkLine", true)
                .style("visibility", "hidden");

            function initDragHandlers() {
                main_svg.select("#leftGraph")
                    .selectAll("g.node")
                    .call(d3.drag().on("drag", dragHandler(leftGraph))
                        .on("end", dragEndHandler(leftGraph))
                        .on("start", dragStartHandler(leftGraph))
                        .filter(function () { return true })
                    );
                main_svg.select("#rightGraph")
                    .selectAll("g.node")
                    .call(d3.drag().on("drag", dragHandler(rightGraph))
                        .on("end", dragEndHandler(rightGraph))
                        .on("start", dragStartHandler(rightGraph))
                        .filter(function () { return true })
                    );

            }

            function dragHandler(subGraph) {
                return function (d) {
                    if (d3.event.sourceEvent.buttons == 1) {
                        subGraph.dragged.call(this, d);
                    }
                    else if (d3.event.sourceEvent.buttons == 2) {
                        var mousepos = d3.mouse(main_svg.node());
                        main_svg.selectAll("#MergeLinkLine")
                            .attr("x2", beginMouseX + (mousepos[0] - beginMouseX) * 0.99)
                            .attr("y2", beginMouseY + (mousepos[1] - beginMouseY) * 0.99);
                    }
                }
            }

            function dragStartHandler(subGraph) {
                return function (d) {
                    if (d3.event.sourceEvent.button == 0) {
                        subGraph.dragNodeStart.call(this, d);
                    }
                    else if (d3.event.sourceEvent.button == 2) {
                        let mousepos = d3.mouse(main_svg.node());
                        beginMouseX = mousepos[0];
                        beginMouseY = mousepos[1];
                        main_svg.selectAll("#MergeLinkLine")
                            .attr("x1", beginMouseX)
                            .attr("y1", beginMouseY)
                            .attr("x2", beginMouseX)
                            .attr("y2", beginMouseY)
                            .style("visibility", "visible");
                        startOfLinkNode = this;
                    }
                }
            }

            function dragEndHandler(subGraph) {
                return function (d) {
                    if (d3.event.sourceEvent.button == 0) {
                        subGraph.dragNodeEnd.call(this, d);
                    }
                    else if (d3.event.sourceEvent.button == 2) {
                        // console.log(d3.select(startOfLinkNode.parentNode.parentNode));
                        // console.log(d3.select("#leftGraph"));

                        main_svg.selectAll("#MergeLinkLine")
                            .style("visibility", "hidden")
                        let target = d3.event.sourceEvent.path[1]
                        let targetSelection = d3.select(target);
                        if (targetSelection.classed("node")) {
                            targetSelection.each(function (d2) {
                                if (d2.type == d.type) {
                                    if (target.parentNode.parentNode.id == "rightGraph" &&
                                        startOfLinkNode.parentNode.parentNode.id == "leftGraph") {
                                        let i = relation.findIndex(v => v.source.id === d.id && v.target.id === d2.id);
                                        if (i === -1) {
                                            relation.push({ source: d, target: d2 });
                                        }
                                        else {
                                           relation.splice(i, 1);
                                        }
                                        drawRelation();

                                    }
                                    else if (target.parentNode.parentNode.id == "leftGraph" &&
                                        startOfLinkNode.parentNode.parentNode.id == "rightGraph") {
                                        let i = relation.findIndex(v => v.source.id === d2.id && v.target.id === d.id);
                                        if (i === -1) {
                                            relation.push({ source: d2, target: d });
                                        }
                                        else {
                                            relation.splice(i, 1);
                                        }
                                        drawRelation();
                                    }
                                }
                            })
                        }
                        else {
                            if (startOfLinkNode.parentNode.parentNode.id == "leftGraph") {
                                // let i = relation.findIndex(v => v.source.id === d.id);
                                // relation.splice(i, 1);
                                relation = relation.filter(v => v.source.id !== d.id);
                                drawRelation();

                            }
                            else if (startOfLinkNode.parentNode.parentNode.id == "rightGraph") {
                                // let i = relation.findIndex(v => v.target.id === d.id);
                                // relation.splice(i, 1);
                                relation = relation.filter(v => v.target.id !== d.id);
                                drawRelation();
                            }

                        }
                    }
                }
            }

            function drawRelation() {
                console.log(relation)
                main_svg.select("#rightGraph")
                    .selectAll("g.node")
                    .classed("matched", d => relation.some(r => r.target.id === d.id));
                main_svg.select("#leftGraph")
                    .selectAll("g.node")
                    .classed("matched", d => relation.some(r => r.source.id === d.id));

                main_svg.select("#rightGraph")
                    .selectAll("path.link")
                    .classed("matched", e => relation.some(r => r.target.id === e.source.id || r.target.id === e.target.id));
                main_svg.select("#leftGraph")
                    .selectAll("path.link")
                    .classed("matched", e => relation.some(r => r.source.id === e.source.id || r.source.id === e.target.id));

                var links = main_svg.selectAll(".ruleMapping")
                    .data(relation);

                links.enter()
                    .append("path")
                    .classed("ruleMapping", true)
                    .classed("matched", true);

                links.exit().remove();
                moveMappingEdges();
            }

            // g1, g2 : graphs
            // path1, path2 : paths of the graphs
            // config1, config2 : configs for the interractiveGraph displays
            // mergerConfig : config for the merger
            //                Used to chose between merging the graphs or typing one by the other
            this.update = function update(g1, g2, path1, path2, config1, config2, mergerConfig) {
                relation = [];
                configMerger = mergerConfig;
                const nodeOfId = function (id1) {
                    const i = g2.nodes.findIndex(n => n.id === id1);
                    return g2.nodes[i];
                }
                relation = g1.nodes.filter(n1 => g2.nodes.some(n2 => n2.id === n1.id))
                    .map(n => ({ source: n, target: nodeOfId(n.id) }));


                parentPath = path1.substring(0, path1.lastIndexOf("/"));
                leftGraphName = path1.substring(path1.lastIndexOf("/") + 1);
                rightGraphName = path2.substring(path1.lastIndexOf("/") + 1);

                localDispatch.on("move", null);
                main_svg.selectAll("#leftGraph").remove();
                main_svg.selectAll("#rightGraph").remove();
                main_svg.selectAll(".separation_line").remove();
                main_svg.selectAll(".ruleMapping").remove();
                main_svg.append(leftGraph.svg_result);
                main_svg.append(rightGraph.svg_result);
                var repDispatch = d3.dispatch("loadingEnded");
                repDispatch.on("loadingEnded", loadedEndedHandler(function () {
                    initDragHandlers();
                    drawRelation();
                    localDispatch.on("move", moveMappingEdges);
                }));
                let graphConfigL = { noTranslate: config1.noTranslate, repDispatch: repDispatch }
                let graphConfigR = { noTranslate: config2.noTranslate, repDispatch: repDispatch }
                if (config1["ancestor_mapping"] !== undefined) {
                    graphConfigL["ancestor_mapping"] = config1["ancestor_mapping"]["typing"];
                }
                if (config2["ancestor_mapping"] !== undefined) {
                    graphConfigR["ancestor_mapping"] = config2["ancestor_mapping"]["typing"];
                }
                leftGraph.update(g1, path1, graphConfigL);
                rightGraph.update(g2, path2, graphConfigR);
                main_svg.append("line")
                    .classed("separation_line", true)
                    .attr("x1", size.width / 2)
                    .attr("y1", 0)
                    .attr("x2", size.width / 2)
                    .attr("y2", size.height);
            };

            // call the callback function once both interactiveGraphs have finished loading
            function loadedEndedHandler(callback) {
                var nbEnd = 0;
                return function () {
                    if (nbEnd == 1) {
                        callback();
                    }
                    else { nbEnd++; }
                }
            }

            /* move the edges representing rule morphisms when one of the graphs moved 
            */
            function moveMappingEdges() {
                let rTransf = d3.zoomTransform(main_svg.select("#rightGraph").node());
                let lTransf = d3.zoomTransform(main_svg.select("#leftGraph").node());
                main_svg.selectAll(".ruleMapping")
                    .attr("d", function (d) {
                        return "M" + ((d.source.x * lTransf.k + lTransf.x)) + "," + (d.source.y * lTransf.k + lTransf.y)
                            + " " + ((d.target.x * rTransf.k + rTransf.x) + size.width / 2) + "," + (d.target.y * rTransf.k + rTransf.y);
                    });
            }
            this.svg_result = function () { return (main_svg.node()); };
            this.stop = function () {
                localDispatch.on("move", null);
                main_svg.selectAll("#rightGraph").remove();
                main_svg.selectAll("#leftGraph").remove();
                main_svg.selectAll(".separation_line").remove();
                main_svg.selectAll(".ruleMapping").remove();
            }

            function mergeGraphs() {
                console.log("merge;")
                let name = prompt("New graph name: ", "");
                if (!name) { return 0; }
                let rel = relation.map(r => ({
                    "left": r.source.id,
                    "right": r.target.id
                }));
                let callback = function (err, _ret) {
                    if (err) {
                        console.log(err);

                    }
                    else {
                        dispatch.call("loadGraph", this, parentPath + "/" + name + "/");
                        dispatch.call("hieUpdate", this);
                    }
                }
                request.mergeGraphs(parentPath, name, leftGraphName, rightGraphName, rel, callback)
                console.log(name);

            }

            function typeGraph() {
                let rel = relation.map(r => ({
                    "left": r.source.id,
                    "right": r.target.id
                }));
                request.promRetypeGraph(parentPath + "/" + leftGraphName,
                    parentPath + "/" + rightGraphName,
                    rel)
                    .then(() => {
                        dispatch.call("loadGraph", this, parentPath + "/" + rightGraphName + "/");
                        dispatch.call("hieUpdate", this);
                    })


            }

            function createButtons() {
                let buttonsDiv = document.createElementNS("http://www.w3.org/1999/xhtml", "div");
                // buttonsDiv.setAttributeNS("http://www.w3.org/2000/xmlns/", "xmlns:xlink", "http://www.w3.org/1999/xlink");
                let buttons = d3.select(buttonsDiv);
                if (configMerger && configMerger["type"]) {
                    console.log("type", configMerger);
                    buttons.append("button")
                        .text("Retype")
                        .attr("type", "button")
                        .classed("top_chart_elem", true)
                        .classed("btn", true)
                        .classed("btn-success", true)
                        .classed("btn-block", true)
                        .on("click", typeGraph);
                }
                else {
                    console.log("merge", configMerger);
                    buttons.attr("id", "mergeButtons")
                        .append("button")
                        .text("Merge")
                        .attr("type", "button")
                        .classed("top_chart_elem", true)
                        .classed("btn", true)
                        .classed("btn-success", true)
                        .classed("btn-block", true)
                        .on("click", mergeGraphs);
                }
                return buttons.node();
            }
            this.buttons = createButtons;

        }
    });
    