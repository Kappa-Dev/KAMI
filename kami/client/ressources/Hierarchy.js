/* This module add the "hierarchy" menu to the UI
 * This module add a div containing a selector and a scrolling tab menu
 * this module trigger graphUpdate events
 * @ Author Adrien Basso blandin
 * This module is part of regraphGui project
 * this project is under AGPL Licence
*/
define([
    "ressources/d3/d3.js",
    "ressources/simpleTree.js",
    "ressources/requestFactory.js",
    "ressources/kamiRequestFactory.js",
    "ressources/d3/d3-context-menu.js"
],
    function (d3, Tree, RFactory, KamiRFactory, d3ContextMenu) {
        /* Create a new hierarchy module
         * @input : container_id : the container to bind this hierarchy
         * @input : dispatch : the dispatch event object
         * @input : server_url : the regraph server url
         * @return : a new Hierarchy object
         */
        return function Hierarchy(container_id, dispatch, server_url) {
            if (!server_url) throw new Error("server url undefined");
            var srv_url = server_url;//the current url of the server
            var disp = dispatch;//global dispatcher for events

            var container = d3.select("#" + container_id).append("div").attr("id", "tab_menu").classed("top_menu", true);//add all tabl to menu
            var top_h_select = container.append("div").attr("id", "top_h_select");
            var h_select = top_h_select.append("select").attr("id", "h_select").classed("mod_el", true);//the hierarchy selector
            top_h_select.append("i").attr("id", "gotoParent").classed("icon", true);//the hierarchy selector
            let tabs = container.append("ul").attr("id", "tabs").classed("nav nav-pills", true);
            container.append("div").classed("tab_menu_el_separator", true);
            let h_lists = container.append("div").attr("id", "scrolling_lists").classed("tab-content", true).classed("scrollbar", true);
            // var h_list = container.append("div").attr("id","scrolling_list1");//the list of son of the specified node
            // h_list.classed("scrolling_list", true);
            container.append("div").classed("tab_menu_el_separator", true);
            container.append("input")
                .attr("type", "text")
                .attr("id", "nugFilter")
                .on("input", filterNuggets);
            var condData = [];
            var condList = container.append("div")
                .attr("id", "conditionsList");

            let current_metadata = null;
            let tab_index = null;
            var factory = new RFactory(srv_url);
            var kamiFactory = new KamiRFactory(srv_url);
            var selfHierarchy = this;
            let graph_context_menu = [
                {
                    title: "delete",
                    action: function (elm, d, _i) {
                        if (confirm("Confirmation : remove " + d.path + " and all its children ?"))
                            factory.delHierarchy(d.path, function (e, r) {
                                if (e) return console.error(e);
                                console.log(r);
                                dispatch.call("hieUpdate", this);
                            });
                    }

                },
                {
                    title: "create rule",
                    action: createRule
                },
                {
                    title: "merge selected graphs",
                    action: mergeGraphs
                },
                {
                    title: "formulae",
                    action: editFormulae
                },
                {
                    title: "check",
                    action: checkFormulae
                }
            ];
            let rule_context_menu = [
                {
                    title: "delete",
                    action: deleteRule

                },
                {
                    title: "apply on parent",
                    action: applyOnParent
                }
            ];
            let nugget_context_menu = [
                {
                    title: "unfold nugget",
                    action: unfoldNugget
                },
                {
                    title: "get kappa",
                    action: showKAppaExporter
                },
                {
                    title: "set rate",
                    action: setRate
                }

            ];
            let variant_context_menu = [
                {
                    title: "splice rule",
                    action: createSplicesRule
                }
            ];

            let all_context_menu = [
                {
                    title: "rename",
                    action: renameChild
                }
            ];

            let context_menu = {};
            context_menu["graph"] = graph_context_menu.concat(all_context_menu);
            context_menu["rule"] = rule_context_menu.concat(all_context_menu);
            context_menu["nugget"] = graph_context_menu.concat(nugget_context_menu).concat(all_context_menu);
            context_menu["variant"] = graph_context_menu.concat(variant_context_menu).concat(all_context_menu);

            /* Update the navigation menu to show the subgraphs of root_path*/
            this.update = function update(root_path, tab) {
                if (root_path == undefined) {
                    root_path = current_metadata.path
                }
                if (tab != undefined) {
                    tab_index = current_metadata.children_types.indexOf(tab);
                }
                else {
                    let pills = tabs.selectAll("li").nodes();
                    // if (pills.length === 0) {
                    // 	tab_index = 0;
                    // }
                    // else {
                        let i = pills.findIndex(elm => d3.select(elm).classed("active"));
                        tab_index = Math.max(0, i);
                    //}
                }

                factory.getMetadata(root_path, function (err, req) {
                    current_metadata = req;
                    drawTabs();
                    drawChildren();
                    drawParents();
                });
            };

            function drawTabs() {
                tabs.selectAll("li").remove();
                let tabs_sel = tabs.selectAll("li")
                    .data(current_metadata.children_types);
                tabs_sel.enter()
                    .append("li")
                    .classed("active", (_d, i) => i === tab_index)
                    .append("a")
                    .classed("hiePill", true)
                    .attr("data-toggle", "pill")
                    .attr("href", d => "#" + d)
                    .text(d => d + "s");
                h_lists.selectAll("div").remove();
                let lists_sel = h_lists.selectAll("div")
                    .data(current_metadata.children_types);
                lists_sel.enter()
                    .append("div")
                    .attr("id", d => d)
                    .classed("tab-pane fade", true)
                    .classed("in active", (_d, i) => i === tab_index)
                    .classed("scrolling_list", true);
            }

            function drawChildren() {
                clearCondData();
                current_metadata.children_types.forEach(function (type) {
                    let data = current_metadata.children.filter(md => md.type == type)
                    let h_list = h_lists.select("#" + type);
                    h_list.selectAll("*").remove();
                    var slc = h_list.selectAll(".tab_menu_el")
                        .data(data);
                    slc.exit().remove();
                    slc.enter().append("div")
                        .classed("tab_menu_el", true)
                        .classed("unselectable", true)
                        .classed("selected", false)
                        .attr("id", function (d) { return d.name })
                        .on("click", function (ltype) {
                            if (ltype === "rule") {
                                return function (d, i) { display_rule(d, i, this) }
                            }
                            else {
                                // return dispach_click
                                return function (d, i) { dispatch_click(d, i, this) }
                            }
                        }(type))
                        // .on("click",function(d,i){dispach_click(d,i,this)})
                        // .on("contextmenu", d3ContextMenu(right_click_menu.concat(only_graph_menu)))
                        .on("contextmenu", d3ContextMenu((() => { return context_menu[type] })()))
                        .on("mouseover", function () {
                            var ltype = type;
                            if (ltype !== "rule") {
                                return (d => {
                                    d3.event.stopPropagation();
                                    disp.call("loadPreview", this, d.path);
                                })
                            }
                        }())
                        // .on("mouseover", function (d) {

                        // 	d3.event.stopPropagation();
                        // 	disp.call("loadPreview", this, d.path);
                        // })
                        .on("mouseout", function (_d) { disp.call("closePreview", this) })
                        .on("dblclick", function () {
                            var ltype = type;
                            if (ltype !== "rule") {
                                return (d => selfHierarchy.update(d.path))
                            }
                        }());

                    slc = h_list.selectAll(".tab_menu_el");
                    slc.append("i")
                        .classed("icon", type !== "rule");
                    slc.append("div")
                        .classed("tab_menu_el_name", true)
                        .text(d => d.name);
                    if (type === "nugget") {
                        slc.append("div")
                            .style("width", "1vw");
                        slc.append("div")
                            .classed("tab_menu_el_rate", true)
                            .text(d => {if ("rate" in d) {return d.rate} else {return "UND"}});
                        // d3.selectAll(".tab_menu_el")
                        //     .each(function (id) {
                        //         var elem = d3.select(this)
                        //         factory.getGraph(hierarchy.getAbsPath(id),
                        //             function (err, resp) {
                        //                 if (err) { return 0 }
                        //                 let rate = resp.attributes["rate"];
                        //                 rate = rate ? rate : "und";
                        //                 elem.append("div")
                        //                     .style("width", "1vw");
                        //                 elem.append("div")
                        //                     .classed("tab_menu_el_rate", true)
                        //                     .text(rate);

                        //             }


                        //         )

                        //     })
                    }
                });
            }
            /* update the scrolling tab menu with the current node sons
             * @input : data : the list of sons of the current node
             */
            // function initHlist(data, rules) {
            // 	clearCondData();
            // 	h_list.selectAll("*").remove();
            // 	var slc = h_list.selectAll(".tab_menu_el")
            // 		.data(data);
            // 	slc.exit().remove();
            // 	slc.enter().append("div")
            // 		.classed("tab_menu_el", true)
            // 		.classed("unselectable", true)
            // 		.classed("selected", false)
            // 		.attr("id", function (d) { return d })
            // 		.on("click", function (d, i) { return dispach_click(d, i, this) })
            // 		.on("contextmenu", d3ContextMenu(right_click_menu.concat(only_graph_menu)))
            // 		.on("mouseover", function (d) { disp.call("loadPreview", this, hierarchy.getAbsPath(d)) })
            // 		.on("mouseout", function (_d) { disp.call("closePreview", this) })
            // 		.on("dblclick", function (d) { return lvlChange(d) });

            // 	var slc = h_list.selectAll(".tab_menu_el");
            // 	slc.append("i")
            // 		.classed("icon", true);
            // 	slc.append("div")
            // 		.classed("tab_menu_el_name", true)
            // 		.text(function (d) {
            // 			// let nm = hierarchy.getName(d);
            // 			// return nm.length>14?nm.substring(0,12).concat("..."):nm;
            // 			return hierarchy.getName(d);
            // 		});

            // 	slc = slc.data(data.concat(rules));
            // 	ruleSelection = slc.enter().append("div")
            // 		.classed("tab_menu_el", true)
            // 		.classed("unselectable", true)
            // 		.classed("selected", false)
            // 		.attr("id", function (d) { return d })
            // 		.on("click", function (d) { return display_rule(d, this) })
            // 		.on("contextmenu", d3ContextMenu(right_click_menu.concat(only_rules_menu)));
            // 	ruleSelection.append("i")
            // 		.classed("icon_rule", true);
            // 	ruleSelection.append("div")
            // 		.classed("tab_menu_el_name", true)
            // 		.text(function (d) { console.log(d); return d.id });


            // 	try {
            // 		if (hierarchy.getName(hierarchy.getFather(hierarchy.getFather(data[0]))) === "kami") {
            // 			d3.selectAll(".tab_menu_el")
            // 				.each(function (id) {
            // 					var elem = d3.select(this)
            // 					factory.getGraph(hierarchy.getAbsPath(id),
            // 						function (err, resp) {
            // 							if (err) { return 0 }
            // 							let rate = resp.attributes["rate"];
            // 							rate = rate ? rate : "und";
            // 							elem.append("div")
            // 								.style("width", "1vw");
            // 							elem.append("div")
            // 								.classed("tab_menu_el_rate", true)
            // 								.text(rate);

            // 						}


            // 					)

            // 				})
            // 		}
            // 	}
            // 	catch (err) { }

            // };
            /* update the selector with the current node parents
             * @input : data : the absolute path of the current node
             */

            function drawParents() {
                let l = current_metadata.path.split("/").filter(s => s);
                l.unshift("/");
                h_select.selectAll("*").remove();
                h_select.selectAll("option")
                    .data(l)
                    .enter().append("option")
                    .text(d => d)
                    .attr("selected", d => d == current_metadata.name);
                h_select.on("change", function () {
                    let i = this.selectedIndex;
                    let selected_path = "/" + l.splice(1, i).join("/")
                    selfHierarchy.update(selected_path)
                });
                top_h_select.select("i").on("click", function () {
                    disp.call("loadGraph", this, current_metadata.path)
                });
            }

            function display_rule(d, _i, elem) {
                d3.event.stopPropagation();
                h_lists.selectAll(".tab_menu_el")
                    .classed("current", false)
                d3.select(elem)
                    .classed("current", true)
                disp.call("loadRule", this, d.path);
            }

            function dispatch_click(d, _i, elem) {
                d3.event.stopPropagation();
                if (d3.event.ctrlKey) {
                    if (d3.select(elem).classed("selected"))
                        d3.select(elem).classed("selected", false);
                    else
                        d3.select(elem).classed("selected", true);
                }
                else {
                    tabChange(d, elem);
                }

            };
            /* color in blue the currently selected node of the scrolling tab menu
             * @input : id : the new selected node
             * @call : graphUpdate event
             */
            function tabChange(id, elem) {
                h_lists.selectAll(".tab_menu_el")
                    .classed("current", false);
                d3.select(elem)
                    .classed("current", true);
                disp.call("loadGraph", this, id.path);
            }

            /* triggers the the kappaExporter modal */
            function showKAppaExporter() {
                dispatch.call("loadKappaExporter", this, current_metadata.path + "/");
            }

            function createSplicesRule() {
                let callback = function (err, _rep) {
                    if (err) {
                        console.log(err);
                    }
                    else {
                        dispatch.call("hieUpdate", this, null);
                    }
                }
                let splices = []
                d3.selectAll(".tab_menu_el.selected")
                    .each(function () {
                        splices.push(this.id);
                    })
                let path = current_metadata.path + "/";
                path = (path == "//") ? "/" : path;
                factory.makeSplices(path, JSON.stringify({ "names": splices }), callback)
            }

            function renameChild(_elm, id) {
                var name = prompt("New Name", "");
                if (!name) { return 0 }
                let callback = function (err, _ret) {
                    if (err) {
                        console.log(err);
                    }
                    else {
                        dispatch.call("hieUpdate", this);
                    }
                }
                if (id.type == "rule") {
                    factory.rnRule(id.path, name, callback);
                }
                else {
                    factory.rnGraph(id.path, name, callback);

                }

            }
            // function createConcats() {
            // 	let callback = function (err, _rep) {
            // 		if (err) {
            // 			console.log(err);
            // 		}
            // 		else {
            // 			dispatch.call("hieUpdate", this, null);
            // 		}
            // 	}
            // 	let splices = []
            // 	d3.selectAll(".tab_menu_el.selected")
            // 		.each(function () {
            // 			splices.push(hierarchy.getName(this.id))
            // 		})
            // 	var path = hierarchy.getAbsPath(current_node) + "/";
            // 	path = (path == "//") ? "/" : path;
            // 	factory.makeConcat(path, JSON.stringify({ "names": splices }), callback)
            // }

            function setRate(elm, d, _i) {
                var rate = prompt("Enter the rate", "");
                if (!rate) { return 0 }
                var callback = function (err, _resp) {
                    if (err) {
                        alert(err.currentTarget.response);
                        return false;
                    }
                    selfHierarchy.update(current_metadata.path);
                }
                factory.addAttr(d.path + "/", JSON.stringify({ "rate": rate }), callback);

            }

            function checkFormulae(_elm, d, _i) {
                let callback = function (err, ret) {
                    if (err) {
                        console.log(err);
                        alert(err.srcElement.responseText);
                    }
                    else {
                        console.log(ret.response);
                        let log = JSON.parse(ret.response);
                        console.log(log);
                        // alert(JSON.stringify(log));
                        dispatch.call("showFormulaResult", this, log);
                    }
                }
                factory.checkFormulae(d.path, callback);
            }

            function unfoldNugget(_elm, d, _i) {
                let callback = function (err, _ret) {
                    if (err) {
                        console.log(err);
                    }
                    else {
                        dispatch.call("hieUpdate", this);
                    }
                }
                kamiFactory.unfoldNugget(d.path, callback);
            }


            // this.addGraph = function () {
            // 	var name = prompt("Name of the new graph?", "");
            // 	if (!name) { return 0 }
            // 	var current_path = current_metadata.path + "/";
            // 	if (current_path == "//") { current_path = "/" }
            // 	factory.addGraph(current_path + name + "/",
            // 		function (err, _ret) {
            // 			if (!err) {
            // 				dispatch.call("hieUpdate", this, null);
            // 			}
            // 			else console.error(err);
            // 		});
            // };

            // this.addGraph = function () {
            // 	var name = prompt("Name of the new graph?", "");
            // 	if (!name) { return 0 }
            // 	var current_path = current_metadata.path + "/";
            // 	if (current_path == "//") { current_path = "/" }
            // 	factory.addGraph(current_path + name + "/",
            // 		function (err, _ret) {
            // 			if (!err) {
            // 				dispatch.call("hieUpdate", this, null);
            // 			}
            // 			else console.error(err);
            // 		});
            // };


            function filterNuggets() {
                var searchString = d3.select("#nugFilter").property("value");
                var searchStrings = searchString.split("|");
                var testTextBox = function (nugName) {
                    return searchStrings.some(function (s) {
                        return (-1) !== nugName.toLowerCase().search(s.toLowerCase())
                    })
                };

                var testCondList = function (nugName) {
                    return condData.map(d => d.cond)
                        .reduce((acc, f) => acc && f(nugName), true);
                };
                var test = function (nugName) {
                    return testCondList(nugName) && testTextBox(nugName);
                };

                var notTest = function (nugName) {
                    return !test(nugName)
                };
                d3.selectAll(".tab_menu_el:not(.selected)")
                    .filter(function () {
                        var nugName = d3.select(this).selectAll(".tab_menu_el_name").text();
                        return notTest(nugName);
                    })
                    .style("display", "none");
                d3.selectAll(".tab_menu_el:not(.selected)")
                    .filter(function () {
                        var nugName = d3.select(this).selectAll(".tab_menu_el_name").text();
                        return test(nugName);
                    })
                    .style("display", "flex");
            }

            this.filterNuggets = filterNuggets;

            function createRule(elm, d, _i) {
                var name = prompt("Name of the new rule?", "");
                var path = current_metadata.path + "/";
                if (path == "//") { path = "/" }
                var patternName = d.name;
                var callback = function (err, ret) {
                    if (!err) {
                        dispatch.call("hieUpdate", this, null);
                        console.log(ret);
                    }
                    else console.error(err);
                };
                factory.addRule(path + name + "/", patternName, callback);
            }

            function mergeGraphs(_elm, _d, _i) {
                let selectedGraphs = [];
                d3.selectAll(".tab_menu_el.selected")
                    .each(function () {
                        selectedGraphs.push(this.id)
                    });
                if (selectedGraphs.length != 2) {
                    alert("exactly two graphs must be selected to merge");
                }
                else {
                    let path = current_metadata.path + "/";
                    if (path == "//") { path = "/" }
                    let [g1, g2] = selectedGraphs.map(s => path + s)
                    dispatch.call("loadMerger", this, g1, g2)
                }
            }

            function deleteRule(_elm, d, _i) {
                let callback = function (err, ret) {
                    if (!err) {
                        dispatch.call("hieUpdate", this, null);
                        console.log(ret);
                    }
                    else console.error(err);
                };
                factory.delHierarchy(d.path + "/", callback);

            }

            function applyOnParent(_elm, d, _i) {
                console.log(d);
                let suffix = prompt("Name of the new rule?", "");
                if (!suffix) { return 0 }
                let callback = function (err, ret) {
                    if (!err) {
                        dispatch.call("hieUpdate", this, null);
                        console.log(ret);
                    }
                    else console.error(err);
                };
                factory.applyRuleOnParent(d.path + "/", suffix, callback);
            }

            function editFormulae(_elm, d, _i) {
                dispatch.call("loadFormulaEditor", this, d.path);
            }

            function editCompositions(_elm, d, _i) {
                dispatch.call("loadCompositionsEditor", this, d.path);
            }

            function updateCondList() {
                var s = condList.selectAll("div")
                    .data(condData);
                s.exit().remove();
                s.enter().append("div")
                    .classed("cond", true)
                    .classed("unselectable", true)
                    .on("click", removeFromCondList)
                    .text(function (d) { return d.name + "_filter" });
                filterNuggets();
            }

            function removeFromCondList(d) {
                var index = condData.indexOf(d);
                if (index > -1) {
                    condData.splice(index, 1);
                }
                updateCondList();
            }

            var clearCondData = function () {
                condData = [];
                updateCondList();
            }

            this.clearCondData = clearCondData;
            this.addToCondData = function (d) {
                condData.push(d);
                updateCondList();
            }

            this.metadata = function () { return current_metadata }

        };

    });
