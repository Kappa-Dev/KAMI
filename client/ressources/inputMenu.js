/* This module show a configurable popup menu with inputs,selector and checkboxes
 * This module can be used independantly from regraphGui in a SVG container
 * @ Author Adrien Basso blandin
 * This module is part of regraphGui project
 * this project is under AGPL Licence
*/
define([
	"ressources/d3/d3.js"
],function(d3){
	/* Add a popup menu asking for new values.
	 * @input : label : The name of the menu
	 * @input : input_l : a list of text input
	 * @input : radio_l : a list of element for a selector 
	 * @input : check_l : a list of element for a list of checkboxes
	 * @input : ok : a boolean : if true, add an ok button 
	 * @input : cancel : a boolean : if true, add a cancel button
	 * @input : pos : the position of the popup relative to the object triggering
	 * pos can be : left, right, top, bot or center
	 * @input : callback : the return callback function
	 * @input : d : the data bound to the object triggering the popup
	 * @input : svg_content : the svg container to bound the menu
	 * @return : callback function with empty object if canceled 
	 * or with {line:string list,radio:string list,check:string list} if validated (ok or enter key)
	 */
	return function(label,input_l,radio_l,check_l,ok,cancel,pos,callback,d,svg_content){
		var fo=svg_content.append("foreignObject").attr("width", 200);
		var form=fo.append("xhtml:form").attr("width",200).attr("id","_inputform");
		form.classed("inputMenu",true);
		if(label!=null && label!="")//if a label is defined : add it
			form.append("label").text(label);
		if(input_l!=null){
			for(var i=0;i<input_l.length;i++) {//add input for each element of the input list
				var inp=form.append("input").attr("value", input_l[i]).attr("width", 90).classed("inputMenus", true);
				if(input_l.length==1){
					inp.on("focus",function(){
						inp.on("keypress", function() {//if enter is pressed
							var e = d3.event;
							if (e.keyCode == 13) {
								d3.event.stopPropagation();
								d3.event.preventDefault();
								var textv,radiov,checkv;
								textv=[];
								if(input_l)
									form.selectAll(".inputMenus").each(function(){textv.push(d3.select(this).node().value);});
								if(radio_l && radio_l.length>0)
									radiov=[radio_l[form.select("#inputMenuRadio").property('selectedIndex')]];
								if(check_l){
									checkv=[];
									form.selectAll('input[name="inputMenuCheck"]:checked').each(function(){checkv.push(check_l[d3.select(this).property("value")]);});
								}
								fo.remove();
								return callback({line:textv,radio:radiov,check:checkv});
							}
						});
					});
					inp.on("blur",function(){inp.on("keypress",null);});
				}
			}
		}
		if(radio_l && radio_l.length>0){//if a list of element is set : add a selector
			form.append("select")
				.classed("inputMenur",true)
				.attr("id","inputMenuRadio")
				.selectAll("option")
					.data(radio_l)
					.enter()
					.append("option")
						.text(function(d){return d})
						.attr("selected",function(d,i){return i==0});
		}if(check_l!=null){//if a list of element is set : add checkboxes
			for(var i=0;i<check_l.length;i++){
				form.append("input")
				.attr("type","checkbox")
				.classed("inputMenuc",true)
				.attr("name","inputMenuCheck")
				.attr("value",i)
				.property("checked", i==0);
				form.append("label").text(" "+check_l[i]);
				form.append("html","<br />");
			}	
		}if(ok){//if ok is clicked
			form.append("input")
			.attr("type","button")
			.classed("inputMenu",true)
			.attr("id","inputMenuOk")
			.attr("value","Ok")
			.on('click',function(){
				d3.event.stopPropagation();
				d3.event.preventDefault();
				var textv,radiov,checkv;
				textv=[];
				if(input_l)
					form.selectAll(".inputMenus").each(function(){textv.push(d3.select(this).node().value);});
				if(radio_l && radio_l.length>0)
					radiov=[radio_l[form.select("#inputMenuRadio").property('selectedIndex')]];
				if(check_l){
					checkv=[];
					form.selectAll('input[name="inputMenuCheck"]:checked').each(function(){checkv.push(check_l[d3.select(this).property("value")]);});
				}
				fo.remove();
				return callback({line:textv,radio:radiov,check:checkv});
			});
		}if(cancel){//if cancel is clicked return an emptu object
			form.append("input")
			.attr("type","button")
			.classed("inputMenu",true)
			.attr("id","inputMenuCL")
			.attr("value","Cancel")
      		.on('click',function(){
				fo.remove();
				return callback({});
			});
		}
		var foHeight = document.getElementById("_inputform").getBoundingClientRect().height;
		fo.attr('height',foHeight)
			.attr('x', function(){if(pos=="left") return d.x-d.r-100; else if(pos=="right") return d.x+d.r; else return d.x-50})
			.attr('y', function(){if(pos=='top') return d.y-foHeight-d.r; else if(pos=="bot") return d.y+d.r;else return d.y-foHeight/2});
/*d3.select(svg).insert('polygon', '.inputMenu').attr({
'points': "0,0 0," + foHeight + " 100," + foHeight + " 100,0 0,0 0,0 0,0",
              'height': foHeight,
              'width': 100,
              'fill': '#D8D8D8', 
              'opacity': 0.75,
              'transform': 'translate(' + (d.x) + ',' + (d.y) + ')'
                        });*/
	}
});	