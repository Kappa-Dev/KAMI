define([
	"ressources/d3/d3.js"
],function(d3){
	return function(label,input_l,radio_l,check_l,ok,cancel,pos,callback,d,svg_content){
		var fo=svg_content.append("foreignObject").attr("width", 200);
		var form=fo.append("xhtml:form").attr("width",200).attr("id","_inputform");
		form.classed("inputMenu",true);
		if(label!=null && label!="")
			form.append("label").text(label);
		if(input_l!=null){
			for(var i=0;i<input_l.length;i++) {
				var inp=form.append("input").attr("value", input_l[i]).attr("width", 90).classed("inputMenus", true);
				if(input_l.length==1){
					inp.on("focus",function(){
						inp.on("keypress", function() {
							var e = d3.event;
							if (e.keyCode == 13) {
								d3.event.stopPropagation();
								d3.event.preventDefault();
								var textv,radiov,checkv;
								textv=[];
								if(input_l)
									form.selectAll(".inputMenus").each(function(){textv.push(d3.select(this).node().value);});
								if(radio_l)
									radiov=[radio_l[form.select('input[name="inputMenuRadio"]:checked').node().value]];
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
		if(radio_l!=null){
			for(var i=0;i<radio_l.length;i++){
				form.append("input")
				.attr("type","radio")
				.classed("inputMenur",true)
				.attr("name","inputMenuRadio")
				.attr("value",i)
				.property("checked", i==0);
				form.append("label").text(" "+radio_l[i]);
				form.append("html","<br />");
			}
		}if(check_l!=null){
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
		}if(ok){
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
				if(radio_l)
					radiov=[radio_l[form.select('input[name="inputMenuRadio"]:checked').node().value]];
				if(check_l){
					checkv=[];
					form.selectAll('input[name="inputMenuCheck"]:checked').each(function(){checkv.push(check_l[d3.select(this).property("value")]);});
				}
				fo.remove();
				return callback({line:textv,radio:radiov,check:checkv});
			});
		}if(cancel){
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