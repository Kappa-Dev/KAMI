define(["ressources/d3/d3.js"],function(d3){return function HierarchyFinder(container_id){
	var container = d3.select("#"+container_id).append("div").attr("id","hierarchy");
	var hierarchy=[];
	var hierarchy_hash={};
	getHierarchy("/");
	function getHierarchy(abs_name){
		if(hierarchy.length==0){
			d3.json("https://api.executableknowledge.org/iregraph/hierarchy/?include_graphs=false&rules=false",function(response){
				reqHier(response,"");
				update(abs_name);
			});
		}else update(abs_name);
	};
	function reqHier(root,path){
		path+=(root.name!="/" && path!="/"?"/":"");
		path+=root.name;
		var ar_path;
		if(path=="/") ar_path=["/"];
		else {
			ar_path=path.split("/");
			ar_path[0]="/";
		}
		var ch_list=[];
		root.children.forEach(function(e){ch_list.push(e.name)});
		hierarchy.push({"name":root.name,"abs":path,"arr_abs":ar_path,"children":ch_list});
		hierarchy_hash[path]=hierarchy.length-1;
		if(root.children.length!=0)
			root.children.forEach(function(e){
				reqHier(e,path);
			});
	};
	function update(abs_name){
		var small_hier=hierarchy.filter(function(e){return subPath})
		updatePathList(abs_name);
		updateChildList(abs_name);
	};
	function updatePathList(abs_name){
		if(!container.select("#h_select").empty())
			container.select("#h_select").remove();
		var datas=
		container.append("select")
			.attr("id","h_select")
			.selectAll("option")
			.data().enter()
				.append("option")
				.text(function(d){return d})
				.on("click",function(d){return update(d,false)})
				.attr("selected",function(d,i){return i=path.length-1});
		
	};
	function updateChildList(name){
		
	};
	
	
	var update = function(d,absolute){
		console.log("I will update");
		var path = container.select("#h_select").selectAll("option").data();
		//path.splice(path.length-1,1);
		console.log(path);
		path.push(d);
		console.log(path);
		path=path.join('/');
		console.log("updating for "+path);
		container.select("#h_sons").remove();
		container.select("#h_select").remove();
		
		getFullPath(path);
		getChilds(path);
	};
	
	function getFullPath(path){
		console.log("getting full path of "+path);
		var tmp;
		if(path!="/"){
			tmp=path.split("/");
			tmp[0]="/";
		}else tmp=["/"];
		var data=tmp.map(function(e,i){var fp=e=="/"?"/":tmp.slice(1,i-2).join("/"); return {'name':e,'abs':fp}});
		console.log(data);
		container.append("select")
			.attr("id","h_select")
			.selectAll("option")
			.data(tmp).enter()
				.append("option")
				.text(function(d){return d})
				.on("click",function(d){return update(d,false)})
				.attr("selected",function(d,i){return i=path.length-1});
	}
	function getChilds(path){
		d3.json("https://api.executableknowledge.org/iregraph/hierarchy"+path+"?include_graphs=false&rules=false",function(rep){
			console.log("looking for "+path);
			console.log(rep);
			var datas=[];
			rep.children.forEach(function(e){datas.push(e.name)});
			if (datas.length==0) rep.push("Empty");
			container.append("ul")
				.attr("id","h_sons")
				.selectAll("li")
				.data(datas).enter().append("li").text(function(d){return d}).on("click",function(d){return update(d,true)});
		});
	};
	
	
	
}; });