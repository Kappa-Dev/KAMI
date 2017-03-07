define([
    "ressources/d3/d3.js",
    "ressources/InterractiveGraph.js",
    "ressources/requestRulesFactory.js"
],
    function (d3, InterractiveGraph, ruleFactory) {
        //Regraph Gui Core
        return function RuleViewer(topSvgId, fatherElem, dispatch, server_url) {

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

            let lhs_factory = new ruleFactory(server_url, function (rule) { return rule["L"] })
            let phs_factory = new ruleFactory(server_url, function (rule) { return rule["P"] })
            let rhs_factory = new ruleFactory(server_url, function (rule) { return rule["R"] })

            var lhs = new InterractiveGraph(topSvgId, "lhs", size.width / 2, size.height / 3, dispatch, lhs_factory, true, localDispatch);
            var phs = new InterractiveGraph(topSvgId, "phs", size.width / 2, size.height / 3, dispatch, phs_factory, true, localDispatch);
            var rhs = new InterractiveGraph(topSvgId, "rhs", size.width, size.height * 2 / 3, dispatch, rhs_factory, false, localDispatch);

            main_svg.append(lhs.svg_result)
                .attr("x", 0)
                .attr("y", 0);
            main_svg.append(phs.svg_result)
                .attr("x", size.width / 2)
                .attr("y", 0);
            main_svg.append(rhs.svg_result)
                .attr("x", 0)
                .attr("y", size.height / 3);

            function draw_mappings(pl_mapping, pr_mapping) {
                let pl = [];
                for (let key in pl_mapping) {
                    let source_node = main_svg.selectAll("#phs .node")
                        .filter(function (d) {
                            return d.id == key
                        });
                    let target_node = main_svg.selectAll("#lhs .node")
                        .filter(function (d) {
                            return d.id == pl_mapping[key]
                        });
                    pl.push({ source: source_node.data()[0], target: target_node.data()[0] });
                }
                let pr = [];
                for (let key in pr_mapping) {
                    let source_node = main_svg.selectAll("#phs .node")
                        .filter(function (d) {
                            return d.id == key
                        });
                    let target_node = main_svg.selectAll("#rhs .node")
                        .filter(function (d) {
                            return d.id == pr_mapping[key]
                        });
                    pr.push({ source: source_node.data()[0], target: target_node.data()[0] });
                }
                let links = main_svg.selectAll(".plMapping")
                    //.data(pl, function (d) { return d.source + "-" + d.target; });
                    .data(pl);

                links.enter()//.insert("line","g")
                    .append("path")
                    .classed("ruleMapping", true)
                    .classed("plMapping", true)
                    .attr("marker-mid", "url(#arrow_end)");
                links.exit().remove();

                links = main_svg.selectAll(".prMapping")
                    //.data(pl, function (d) { return d.source + "-" + d.target; });
                    .data(pr);

                links.enter()//.insert("line","g")
                    .append("path")
                    .classed("ruleMapping", true)
                    .classed("prMapping", true)
                    .attr("marker-mid", "url(#arrow_end)");
                links.exit().remove();
                localDispatch.on("move", moveMappingEdges);
            };

            this.update = function update(rep, current_graph, config) {
                localDispatch.on("move", null);
                main_svg.selectAll("#lhs").remove();
                main_svg.selectAll("#rhs").remove();
                main_svg.selectAll("#phs").remove();
                main_svg.selectAll(".separation_line").remove();
                main_svg.selectAll(".ruleMapping").remove();
                main_svg.append(lhs.svg_result);
                main_svg.append(phs.svg_result);
                main_svg.append(rhs.svg_result);
                var repDispatch = d3.dispatch("loadingEnded");
                repDispatch.on("loadingEnded", loadedEndedHandler(() => draw_mappings(rep["PL"], rep["PR"])));
                lhs.update(rep["L"], current_graph, {noTranslate:config.noTranslate, repDispatch:repDispatch});
                phs.update(rep["P"], current_graph, {noTranslate:config.noTranslate, repDispatch:repDispatch});
                rhs.update(rep["R"], current_graph, {noTranslate:config.noTranslate, repDispatch:repDispatch});
                main_svg.append("line")
                    .classed("separation_line", true)
                    .attr("x1", 0)
                    .attr("y1", size.height / 3)
                    .attr("x2", size.width)
                    .attr("y2", size.height / 3);
                main_svg.append("line")
                    .classed("separation_line", true)
                    .attr("x1", size.width / 2)
                    .attr("y1", 0)
                    .attr("x2", size.width / 2)
                    .attr("y2", size.height / 3);
            };

            function loadedEndedHandler(callback) {
                var nbEnd = 0;
                return function () {
                    if (nbEnd == 2) {
                        callback();
                    }
                    else { nbEnd++; }
                }
            };

            /* move the edges representing rule morphisms when one of the graphs moved 
            */
            function moveMappingEdges() {
                let rTransf = d3.zoomTransform(main_svg.select("#rhs").node());
                let pTransf = d3.zoomTransform(main_svg.select("#phs").node());
                let lTransf = d3.zoomTransform(main_svg.select("#lhs").node());
                main_svg.selectAll(".plMapping")
                    .attr("d", function (d) {
                        return "M" + ((d.source.x * pTransf.k + pTransf.x) + size.width / 2) + "," + (d.source.y * pTransf.k + pTransf.y)
                            + " " + (d.target.x * lTransf.k + lTransf.x) + "," + (d.target.y * lTransf.k + lTransf.y);
                    });
                main_svg.selectAll(".prMapping")
                    .attr("d", function (d) {
                        return "M" + ((d.source.x * pTransf.k + pTransf.x) + size.width / 2) + "," + (d.source.y * pTransf.k + pTransf.y)
                            + " " + (d.target.x * rTransf.k + rTransf.x) + "," + (d.target.y * rTransf.k + rTransf.y + size.height / 3);
                    });
            };
            this.svg_result =  function(){return (main_svg.node());};
            this.stop = function (){
                localDispatch.on("move",null);
                main_svg.selectAll("#lhs").remove();
                main_svg.selectAll("#rhs").remove();
                main_svg.selectAll("#phs").remove();
                main_svg.selectAll(".separation_line").remove();
                main_svg.selectAll(".ruleMapping").remove();
            } ;

        }
    });
	