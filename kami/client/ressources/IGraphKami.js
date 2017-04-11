
define([
	"ressources/d3/d3.js"

], function (d3) {
	/* Create a new interractive graph structure
	 * @input : container_id : the container to bind this hierarchy
	 * @input : dispatch : the dispatch event object
	 * @input : server_url : the regraph server url
	 * @return : a new InterractiveGraph object
	 */
    return function IGraphUtils(request, disp) {
        let self = this;

        this.newGraph = function newGraph(svg_content, g_id) {
            return function (_elm, _d, _i) {
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
        }

        this.newChildRule = function newChildRule(svg_content, g_id) {
            return function (_elm, _d, _i) {
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
        }

        this.maybeDrawButtons = function maybeDrawButtons(buttonDiv, svg_content) {
            var selected = svg_content.selectAll("g.selected")
            if (selected.size()) {
                self.drawButtons(buttonDiv);
            }
            else {
                self.hideButtons(buttonDiv);
            }
        }

        this.drawButtons = function drawButtons(buttonsDiv) {
            d3.select(buttonsDiv)
                .style("display", "block");
        }

        this.hideButtons = function hideButtons(buttonsDiv) {
            d3.select(buttonsDiv)
                .style("display", "none");
        }

        this.createButtons = function createButtons(buttonsDiv, svg_content, g_id) {
            let buttons = d3.select(buttonsDiv);
            buttons.attr("id", "GraphButtons")
                .append("button")
                .text("New child graph")
                .on("click", self.newGraph(svg_content, g_id));

            // buttons .append("button")
            // 	.text("New sigbling graph")
            // 	.on("click", function () { alert("sibling graph") });

            buttons.append("button")
                .text("New child rule")
                .on("click", self.newChildRule(svg_content, g_id));

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
});