define([],function(){return {
	absPath : function absPath(p){
		var path = p.concat();
		console.log("path : "+path);
		path[0]="";
		path.push("");
		return path.join("/");	
	}
}});