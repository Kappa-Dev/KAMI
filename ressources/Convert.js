define([],function(){return {
	absPath : function absPath(path){
		path[0]="";
		path.push("");
		return path.join("/");	
	}
}});