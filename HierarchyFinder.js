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
		path+=(root.name!="/" && path!="/"?"/":"");//fuck this fucking / root !
		path+=root.name;
		var ar_path;
		if(path=="/") ar_path=["/"];//fuck this fucking / root !
		else {
			ar_path=path.split("/");
			ar_path[0]="/";
		}
		var ch_list=[];
		var sep=path=="/"?"":"/";//fuck this fucking / root !
		root.children.forEach(function(e){ch_list.push(path+sep+e.name)});
		hierarchy.push({"name":root.name,"abs":path,"arr_abs":ar_path,"children":ch_list});
		hierarchy_hash[path]=hierarchy.length-1;
		if(root.children.length!=0)
			root.children.forEach(function(e){
				reqHier(e,path);
			});
	};
	function update(abs_name){
		updatePathList(abs_name);
		updateChildList(abs_name);
	};
	function updatePathList(abs_name){
		if(!container.select("#h_select").empty())
			container.select("#h_select").remove();
		var datas=[];
		hierarchy[hierarchy_hash[abs_name]].arr_abs.forEach(function(e,i){
			if(i>1){
				var pth="";
				pth+=hierarchy[hierarchy_hash[abs_name]].arr_abs.splice(1,i).join("/");
				console.log("pth : ");
				console.log(hierarchy[hierarchy_hash[abs_name]].arr_abs);
				pth="/"+pth;
				datas.push(pth);
			}
			if(i==0)
				datas.push("/");
			if(i==1)
				datas.push("/"+e);
		});
		console.log("datas");
		console.log(datas);
		container.append("select")
			.attr("id","h_select")
			.selectAll("option")
			.data(datas).enter()
				.append("option")
				.text(function(d){return hierarchy[hierarchy_hash[d]].name})
				.on("click",function(d){return update(hierarchy[hierarchy_hash[d]].abs)})
				.attr("selected",function(d){return hierarchy[hierarchy_hash[d]].abs==abs_name});
	};
	function updateChildList(abs_name){
		if(!container.select("#h_child").empty())
			container.select("#h_child").remove();
		var datas=hierarchy[hierarchy_hash[abs_name]].children;
		console.log("datas");
		console.log(datas);
		container.append("ul")
			.attr("id","h_child")
			.selectAll("li")
			.data(datas).enter()
				.append("li")
				.text(function(d){return hierarchy[hierarchy_hash[d]].name})
				.on("click",function(d){return update(hierarchy[hierarchy_hash[d]].abs)})
				.attr("selected",function(d){return hierarchy[hierarchy_hash[d]].abs==abs_name});
	}

	
}; });