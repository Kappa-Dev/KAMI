define([
    "ressources/d3/d3.js",
    "ressources/requestFactory.js"
],
    function (d3, factory) {

        //Interface allowing to define relations between nodes of different graphs

        return function NewNode(topDivId, fatherElem, dispatch, requestm, parentIGraph) {
            console.log("topDivId", topDivId);
            let typesList = [];
            let currentType = null;
            let offset = 0;
            let prefix = "";
            let main_div = fatherElem
                .append("div")
                .attr("id", topDivId)
                .classed("list-group", true)
                .classed("scrollbar", true)
                .classed("newNodeDiv", true)
                .style("visibility", "hidden");
            let prefixDiv = main_div.append("div")
                                    .classed("prefixNewNode", true);

            function drawTypes() {
                main_div.selectAll(".possibleTypes")
                    .remove();
                let filteredList = typesList.filter(typeName =>
                    (-1) !== typeName.toLowerCase().search(prefix.toLowerCase()));
                let typesSelect = main_div
                    .selectAll(".possibleTypes")
                    .data(filteredList);

                typesSelect.enter()
                    .append("a")
                    .classed("possibleTypes", true)
                    .classed("list-group-item", true)
                    .on("click", activate)
                    .classed("active", (_d,i) => i === offset)
                    .text(d => d);

                // let selection = main_div.select(".possibleTypes")
                //     .classed("active", true);
                if (filteredList.length != 0) {
                    currentType = filteredList[offset];
                }
                else {
                    currentType = null;
                }
                prefixDiv.text(prefix);
                console.log("current_type", currentType);
            }

            function activate(d, i) {
                currentType = d;
                main_div.selectAll(".possibleTypes")
                    .classed("active", false);
                d3.select(this).classed("active", true);
                offset = i;
                console.log("current_type", currentType);
            }

            this.update = function update(types) {
                main_div.style("visibility", "hidden");
                typesList = types;
                prefix = "";
                offset = 0;
                drawTypes();
            };

            this.input = function () {
                if (d3.event.target === d3.select("body").node()) {
                    if (d3.event.keyCode === 27) {
                        prefix = "";
                        offset = 0;
                        main_div.style("visibility", "hidden");
                        drawTypes();
                        parentIGraph.endNewNode();
                    }
                    else if (d3.event.keyCode === 8 && prefix !== "") {
                        prefix = prefix.slice(0, -1);
                        offset = 0;
                        drawTypes();
                    }
                    else if (d3.event.key === "ArrowDown") {
                        let size = main_div.selectAll(".possibleTypes").size();
                        if (size !== 0) {
                            offset = (offset + 1) % size;
                            console.log(offset);
                            drawTypes();
                        }
                    }
                    else if (d3.event.key === "ArrowUp") {
                        let size = main_div.selectAll(".possibleTypes").size();
                        if (size !== 0) {
                            offset = (offset - 1 + size) % size;
                            console.log(offset);
                            drawTypes();
                        }
                    }
                    else if (d3.event.key.length === 1) {

                        prefix = prefix + d3.event.key;
                        offset = 0;
                        drawTypes();
                    }
                    console.log("prefix", prefix);
                    console.log(d3.event.key);
                }
            }

            this.currentType = function(){
                return  currentType;
            }

        }
    });
    